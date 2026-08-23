"""Refresh the GitHub stats stored against each project.

    python manage.py refresh_github

Projects whose code_url isn't a GitHub URL are skipped. If GitHub can't be
reached the existing numbers are left alone rather than blanked.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from portfolio.github import fetch_repo
from portfolio.models import Project


class Command(BaseCommand):
    help = "Fetch stars, forks, language and last-commit date from GitHub."

    def add_arguments(self, parser):
        parser.add_argument(
            "--project",
            help="Refresh only the project with this exact title.",
        )

    def handle(self, *args, **options):
        projects = Project.objects.all()
        if options["project"]:
            projects = projects.filter(title=options["project"])

        updated = skipped = failed = 0

        for project in projects:
            repo = project.github_repo
            if not repo:
                skipped += 1
                continue

            data = fetch_repo(repo)
            if data is None:
                self.stderr.write(self.style.WARNING(f"  ! could not read {repo}"))
                failed += 1
                continue

            project.gh_stars = data["stars"]
            project.gh_forks = data["forks"]
            project.gh_language = data["language"]
            project.gh_pushed_at = data["pushed_at"]
            project.gh_synced_at = timezone.now()
            project.save(
                update_fields=[
                    "gh_stars", "gh_forks", "gh_language", "gh_pushed_at", "gh_synced_at",
                ]
            )

            self.stdout.write(
                f"  ✓ {repo}: {data['stars']} stars, {data['language'] or 'no language'}"
            )
            updated += 1

        summary = f"Updated {updated}, skipped {skipped} (no GitHub URL), failed {failed}."
        style = self.style.SUCCESS if not failed else self.style.WARNING
        self.stdout.write(style(summary))
