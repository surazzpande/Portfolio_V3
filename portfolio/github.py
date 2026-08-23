"""Fetch repository stats from the GitHub API.

Stats are written to the Project rows by `manage.py refresh_github`, so page
rendering never waits on a network call. Run the command on a schedule (a
GitHub Actions cron works well) to keep the numbers fresh.
"""

import json
import logging
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone as dt_timezone

logger = logging.getLogger(__name__)

API_ROOT = "https://api.github.com/repos/"
TIMEOUT = 8


def fetch_repo(repo: str) -> dict | None:
    """Return selected fields for 'owner/name', or None if it can't be read.

    An unauthenticated call is fine for a handful of public repos (60 requests
    per hour). Set GITHUB_TOKEN to raise that to 5,000.
    """
    request = urllib.request.Request(
        API_ROOT + repo,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "portfolio-site",
        },
    )

    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        logger.warning("GitHub returned %s for %s", exc.code, repo)
        return None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        logger.warning("Could not reach GitHub for %s: %s", repo, exc)
        return None

    return {
        "stars": data.get("stargazers_count") or 0,
        "forks": data.get("forks_count") or 0,
        "language": data.get("language") or "",
        "pushed_at": _parse_timestamp(data.get("pushed_at")),
    }


def _parse_timestamp(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt_timezone.utc)
    except ValueError:
        return None
