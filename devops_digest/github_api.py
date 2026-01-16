"""GitHub API utilities for DevOps Digest."""

import json
import os
from pathlib import Path

import click
import requests

from .config import GITHUB_API_BASE


def get_github_token():
    """Get GitHub token from environment variable."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise click.ClickException(
            "GITHUB_TOKEN environment variable is not set. "
            "Please set it with your GitHub personal access token."
        )
    return token


def get_github_username(token):
    """Get the authenticated user's GitHub username."""
    response = requests.get(
        f"{GITHUB_API_BASE}/user",
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["login"]


def load_config_teams(token):
    """
    Load team names from conf/data.json and fetch all repositories for those teams.

    Returns a list of full repo names (org/repo) from all configured teams.
    """
    # Find the config file relative to the script location
    script_dir = Path(__file__).parent.parent
    config_path = script_dir / "conf" / "data.json"

    if not config_path.exists():
        raise click.ClickException(f"Config file not found: {config_path}")

    with open(config_path) as f:
        config = json.load(f)

    team_names = [team["name"] for team in config.get("teams", [])]

    if not team_names:
        raise click.ClickException("No teams defined in conf/data.json")

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Get the authenticated user's organizations
    orgs_response = requests.get(
        f"{GITHUB_API_BASE}/user/orgs",
        headers=headers,
        timeout=30,
    )
    orgs_response.raise_for_status()
    orgs = orgs_response.json()

    matched_repos = set()

    for org in orgs:
        org_login = org["login"]

        # Try to find teams matching our configured team names
        for team_name in team_names:
            # Get team repos - try with team slug (lowercase, hyphenated)
            team_slug = team_name.lower().replace(" ", "-")
            try:
                repos_response = requests.get(
                    f"{GITHUB_API_BASE}/orgs/{org_login}/teams/{team_slug}/repos",
                    headers=headers,
                    params={"per_page": 100},
                    timeout=30,
                )

                if repos_response.status_code == 200:
                    for repo in repos_response.json():
                        matched_repos.add(repo["full_name"])
            except requests.exceptions.RequestException:
                continue

    return list(matched_repos)


def load_config_repos(token):
    """
    Load repository names from conf/data.json and resolve to full repo paths.

    Returns a list of full repo names (org/repo) that the user has access to.
    """
    # Find the config file relative to the script location
    script_dir = Path(__file__).parent.parent
    config_path = script_dir / "conf" / "data.json"

    if not config_path.exists():
        raise click.ClickException(f"Config file not found: {config_path}")

    with open(config_path) as f:
        config = json.load(f)

    repo_short_names = {repo["name"] for repo in config.get("repositories", [])}

    if not repo_short_names:
        raise click.ClickException("No repositories defined in conf/data.json")

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Search for repos matching the configured names that the user has access to
    matched_repos = []
    page = 1
    while True:
        response = requests.get(
            f"{GITHUB_API_BASE}/user/repos",
            headers=headers,
            params={"per_page": 100, "page": page},
            timeout=30,
        )
        response.raise_for_status()
        page_repos = response.json()
        if not page_repos:
            break

        for repo in page_repos:
            if repo["name"] in repo_short_names:
                matched_repos.append(repo["full_name"])

        page += 1

    return matched_repos
