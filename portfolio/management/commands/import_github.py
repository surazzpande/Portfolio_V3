"""Import repositories from GitHub as projects.

    python manage.py import_github surazzpande Pande-Suraj

Imported projects arrive **unpublished**, so nothing appears on the live site
until you review it in the admin, write a proper problem/solution, and tick
'published'. Re-running updates the GitHub stats on existing projects without
overwriting any wording you've edited.

Forks and archived repositories are skipped by default.
"""

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone as dt_timezone

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from portfolio.models import Project, Tag

API = "https://api.github.com/users/{user}/repos?per_page=100&sort=pushed"

# Language names GitHub reports -> the tag wording used on the site.
TAG_ALIASES = {
    "Jupyter Notebook": "Jupyter",
    "HTML": "HTML5",
}


class Command(BaseCommand):
    help = "Create or update projects from a GitHub account's repositories."

    def add_arguments(self, parser):
        parser.add_argument("users", nargs="+", help="GitHub usernames to import from.")
        parser.add_argument(
            "--include-forks",
            action="store_true",
            help="Also import repositories you forked from someone else.",
        )
        parser.add_argument(
            "--publish",
            action="store_true",
            help="Publish immediately instead of importing as drafts. Not recommended.",
        )
        parser.add_argument(
            "--min-pushed",
            help="Only import repos pushed on or after this date, e.g. 2024-01-01.",
        )

    def handle(self, *args, **options):
        cutoff = None
        if options["min_pushed"]:
            try:
                cutoff = datetime.strptime(options["min_pushed"], "%Y-%m-%d").replace(
                    tzinfo=dt_timezone.utc
                )
            except ValueError:
                raise CommandError("--min-pushed must look like 2024-01-01")

        created = updated = skipped = 0
        next_order = (
            Project.objects.order_by("-order").values_list("order", flat=True).first() or 0
        ) + 1

        for user in options["users"]:
            self.stdout.write(self.style.MIGRATE_HEADING(f"\n{user}"))
            repos = self._fetch(user)
            if repos is None:
                continue

            for repo in repos:
                if repo.get("fork") and not options["include_forks"]:
                    skipped += 1
                    continue
                if repo.get("archived"):
                    skipped += 1
                    continue

                pushed = self._parse(repo.get("pushed_at"))
                if cutoff and pushed and pushed < cutoff:
                    skipped += 1
                    continue

                stats = {
                    "gh_stars": repo.get("stargazers_count") or 0,
                    "gh_forks": repo.get("forks_count") or 0,
                    "gh_language": repo.get("language") or "",
                    "gh_pushed_at": pushed,
                    "gh_synced_at": timezone.now(),
                }

                project = Project.objects.filter(code_url=repo["html_url"]).first()

                if project:
                    # Only refresh the stats — never clobber wording you've written.
                    for field, value in stats.items():
                        setattr(project, field, value)
                    project.save(update_fields=list(stats))
                    self.stdout.write(f"  refreshed  {repo['name']}")
                    updated += 1
                    continue

                title = repo["name"].replace("_", " ").replace("-", " ").strip()
                project = Project.objects.create(
                    title=title,
                    subtitle=repo.get("description") or "",
                    code_url=repo["html_url"],
                    live_url=repo.get("homepage") or "",
                    published=options["publish"],
                    order=next_order,
                    **stats,
                )
                next_order += 1

                tags = []
                if repo.get("language"):
                    name = TAG_ALIASES.get(repo["language"], repo["language"])
                    tags.append(Tag.objects.get_or_create(name=name)[0])
                for topic in (repo.get("topics") or [])[:5]:
                    tags.append(Tag.objects.get_or_create(name=topic)[0])
                project.tags.set(tags)

                state = "published" if options["publish"] else "draft"
                self.stdout.write(self.style.SUCCESS(f"  imported   {repo['name']}  ({state})"))
                created += 1

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {created}, refreshed {updated}, skipped {skipped}."
            )
        )
        if created and not options["publish"]:
            self.stdout.write(
                "New projects are drafts. Open /admin/portfolio/project/ to write a "
                "problem and solution for the ones worth showing, then tick 'published'."
            )

    def _fetch(self, user):
        request = urllib.request.Request(
            API.format(user=user),
            headers={"Accept": "application/vnd.github+json", "User-Agent": "portfolio-site"},
        )
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            request.add_header("Authorization", f"Bearer {token}")

        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                self.stderr.write(self.style.ERROR(f"  no such GitHub user: {user}"))
            elif exc.code == 403:
                self.stderr.write(
                    self.style.ERROR(
                        "  GitHub rate limit reached. Wait an hour, or set GITHUB_TOKEN."
                    )
                )
            else:
                self.stderr.write(self.style.ERROR(f"  GitHub error {exc.code} for {user}"))
            return None
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            self.stderr.write(self.style.ERROR(f"  could not reach GitHub: {exc}"))
            return None

    @staticmethod
    def _parse(value):
        if not value:
            return None
        try:
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt_timezone.utc)
        except ValueError:
            return None
