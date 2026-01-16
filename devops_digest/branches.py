"""Branch related functions for DevOps Digest."""

from datetime import datetime, timedelta, timezone

import requests

from .config import GITHUB_API_BASE, EXCLUDED_BRANCHES


def get_stale_branches(token, username, repo_names):
    """
    Get branches older than 30 days where the HEAD commit was authored by the user.

    Args:
        token: GitHub token
        username: GitHub username to filter by (only show branches where HEAD commit is by this user)
        repo_names: List of full repo names to check

    Returns a list of dicts with: repo_name, branch_name, age_days, last_commit_author
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    stale_branches = []
    cutoff_time = datetime.now(timezone.utc) - timedelta(days=30)

    for repo_name in repo_names:
        try:
            # Get all branches for this repo
            response = requests.get(
                f"{GITHUB_API_BASE}/repos/{repo_name}/branches",
                headers=headers,
                params={"per_page": 100},
                timeout=30,
            )
            if response.status_code == 404:
                continue
            response.raise_for_status()

            for branch in response.json()[:20]:  # Limit to 20 branches per repo
                branch_name = branch["name"]
                if branch_name in EXCLUDED_BRANCHES:
                    continue

                # Get the commit details for last commit date and author
                commit_sha = branch["commit"]["sha"]
                commit_response = requests.get(
                    f"{GITHUB_API_BASE}/repos/{repo_name}/commits/{commit_sha}",
                    headers=headers,
                    timeout=30,
                )
                if commit_response.status_code != 200:
                    continue
                commit_response.raise_for_status()

                commit_data = commit_response.json()

                # Check if the commit author matches the user
                # Check both the GitHub username (if linked) and the git author name
                author_login = commit_data.get("author", {}).get("login", "") if commit_data.get("author") else ""
                author_name = commit_data["commit"]["author"]["name"]

                if author_login.lower() != username.lower() and author_name.lower() != username.lower():
                    continue

                commit_date_str = commit_data["commit"]["committer"]["date"]
                commit_date = datetime.fromisoformat(commit_date_str.replace("Z", "+00:00"))

                if commit_date < cutoff_time:
                    age_days = (datetime.now(timezone.utc) - commit_date).days

                    stale_branches.append({
                        "repo_name": repo_name,
                        "branch_name": branch_name,
                        "age_days": age_days,
                        "last_commit_author": author_name,
                    })

        except requests.exceptions.RequestException:
            continue

    # Sort by age (oldest first)
    stale_branches.sort(key=lambda x: x["age_days"], reverse=True)

    return stale_branches
