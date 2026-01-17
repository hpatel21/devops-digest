"""GitHub Actions related functions for DevOps Digest."""

from datetime import datetime, timedelta, timezone

import requests

from .config import GITHUB_API_BASE


def get_failed_actions(token, repo_names):
    """
    Get failed GitHub Actions runs from the last 12 hours.

    Args:
        token: GitHub token
        repo_names: List of full repo names to check

    Returns a list of dicts with: repo_name, workflow_name, branch, failed_at, url
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    failed_actions = []
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=12)

    for repo_name in repo_names:
        try:
            response = requests.get(
                f"{GITHUB_API_BASE}/repos/{repo_name}/actions/runs",
                headers=headers,
                params={"per_page": 20},
                timeout=30,
            )
            if response.status_code == 404:
                # Repo might not have Actions enabled
                continue
            response.raise_for_status()

            for run in response.json().get("workflow_runs", []):
                if run["conclusion"] != "failure":
                    continue

                run_time = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
                if run_time < cutoff_time:
                    continue

                failed_actions.append({
                    "repo_name": repo_name,
                    "workflow_name": run["name"],
                    "branch": run["head_branch"],
                    "failed_at": run_time,
                    "url": run["html_url"],
                })
        except requests.exceptions.RequestException:
            # Skip repos we can't access
            continue

    # Sort by failure time (most recent first)
    failed_actions.sort(key=lambda x: x["failed_at"], reverse=True)

    return failed_actions
