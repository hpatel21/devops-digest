"""Pull request related functions for DevOps Digest."""

from datetime import datetime, timezone

import click
import requests

from .config import GITHUB_API_BASE


def _search_prs(headers, query, debug=False):
    """Execute a GitHub PR search query and return parsed results."""
    if debug:
        click.echo(f"Query: {query}")

    response = requests.get(
        f"{GITHUB_API_BASE}/search/issues",
        headers=headers,
        params={"q": query, "per_page": 100},
        timeout=30,
    )
    response.raise_for_status()

    result = response.json()
    if debug:
        click.echo(f"Total count: {result.get('total_count', 0)}")

    prs = []
    for item in result.get("items", []):
        repo_name = item["repository_url"].replace(f"{GITHUB_API_BASE}/repos/", "")
        created_at = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
        age_days = (datetime.now(timezone.utc) - created_at).days

        prs.append({
            "id": item["id"],
            "repo_name": repo_name,
            "title": item["title"],
            "number": item["number"],
            "age_days": age_days,
            "url": item["html_url"],
        })

    return prs


def get_my_pull_requests(token, username, debug=False):
    """
    Get all open PRs grouped by involvement type.

    Returns a dict with keys: "my_prs", "reviewing", "mentioned"
    Each value is a list of PR dicts with: repo_name, title, number, age_days, url
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Search for each category
    my_prs = _search_prs(headers, f"is:pr is:open author:{username}", debug)
    reviewing = _search_prs(headers, f"is:pr is:open review-requested:{username}", debug)
    mentioned = _search_prs(headers, f"is:pr is:open mentions:{username}", debug)

    # Track seen IDs to remove duplicates (prioritize: my_prs > reviewing > mentioned)
    seen_ids = set()

    for pr in my_prs:
        seen_ids.add(pr["id"])

    reviewing = [pr for pr in reviewing if pr["id"] not in seen_ids]
    for pr in reviewing:
        seen_ids.add(pr["id"])

    mentioned = [pr for pr in mentioned if pr["id"] not in seen_ids]

    # Sort each group by age (oldest first)
    my_prs.sort(key=lambda x: x["age_days"], reverse=True)
    reviewing.sort(key=lambda x: x["age_days"], reverse=True)
    mentioned.sort(key=lambda x: x["age_days"], reverse=True)

    return {
        "my_prs": my_prs,
        "reviewing": reviewing,
        "mentioned": mentioned,
    }
