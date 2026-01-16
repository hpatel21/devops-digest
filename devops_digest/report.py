"""Report generation functions for DevOps Digest."""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

import click
import requests

from .prs import get_my_pull_requests
from .builds import get_failed_builds
from .branches import get_stale_branches
from .utils import relative_time


def generate_report(token, username, repo_names, team_repo_names=None, debug=False):
    """
    Generate a full DevOps digest report.

    Args:
        token: GitHub token
        username: GitHub username
        repo_names: List of full repo names to check for stale branches
        team_repo_names: List of full repo names from teams for failed builds (optional, falls back to repo_names)
        debug: Enable debug output

    Returns a tuple of (report_content, errors) where errors is a list of error messages
    """
    errors = []

    # Use team repos for builds if provided, otherwise fall back to repo_names
    build_repo_names = team_repo_names if team_repo_names else repo_names

    # Fetch PRs
    click.echo("  Fetching pull requests...", nl=False)
    try:
        grouped_prs = get_my_pull_requests(token, username, debug)
        click.secho(" ✓", fg="green")
    except requests.exceptions.RequestException as e:
        grouped_prs = {"my_prs": [], "reviewing": [], "mentioned": []}
        errors.append(f"Failed to fetch PRs: {e}")
        click.secho(" ✗", fg="red")

    # Fetch failed builds
    click.echo("  Fetching failed builds...", nl=False)
    try:
        failed_builds = get_failed_builds(token, build_repo_names)
        click.secho(" ✓", fg="green")
    except requests.exceptions.RequestException as e:
        failed_builds = []
        errors.append(f"Failed to fetch builds: {e}")
        click.secho(" ✗", fg="red")

    # Fetch stale branches
    click.echo("  Fetching stale branches...", nl=False)
    try:
        stale_branches = get_stale_branches(token, username, repo_names)
        click.secho(" ✓", fg="green")
    except requests.exceptions.RequestException as e:
        stale_branches = []
        errors.append(f"Failed to fetch stale branches: {e}")
        click.secho(" ✗", fg="red")

    # Calculate summary stats
    total_prs = len(grouped_prs["my_prs"]) + len(grouped_prs["reviewing"]) + len(grouped_prs["mentioned"])

    # Generate report content
    now = datetime.now()
    report_date = now.strftime("%Y-%m-%d")
    report_time = now.strftime("%H:%M:%S")

    report_lines = [
        f"# DevOps Digest - {report_date}",
        "",
        f"**Generated:** {report_date} at {report_time}",
        f"**User:** {username}",
        "",
        "## Summary",
        "",
        f"| Metric | Count |",
        f"|--------|-------|",
        f"| Open PRs | {total_prs} |",
        f"| Failed Builds (12h) | {len(failed_builds)} |",
        f"| Stale Branches (30d+) | {len(stale_branches)} |",
        "",
    ]

    # PRs Section
    report_lines.append("## Pull Requests")
    report_lines.append("")

    if total_prs == 0:
        report_lines.append("*No open pull requests.*")
        report_lines.append("")
    else:
        # My PRs
        if grouped_prs["my_prs"]:
            report_lines.append("### My PRs")
            report_lines.append("")
            report_lines.append("| Repository | PR | Age |")
            report_lines.append("|------------|-----|-----|")
            for pr in grouped_prs["my_prs"]:
                report_lines.append(f"| {pr['repo_name']} | [#{pr['number']} {pr['title']}]({pr['url']}) | {pr['age_days']} days |")
            report_lines.append("")

        # Reviewing
        if grouped_prs["reviewing"]:
            report_lines.append("### Reviewing")
            report_lines.append("")
            report_lines.append("| Repository | PR | Age |")
            report_lines.append("|------------|-----|-----|")
            for pr in grouped_prs["reviewing"]:
                report_lines.append(f"| {pr['repo_name']} | [#{pr['number']} {pr['title']}]({pr['url']}) | {pr['age_days']} days |")
            report_lines.append("")

        # Mentioned
        if grouped_prs["mentioned"]:
            report_lines.append("### Mentioned")
            report_lines.append("")
            report_lines.append("| Repository | PR | Age |")
            report_lines.append("|------------|-----|-----|")
            for pr in grouped_prs["mentioned"]:
                report_lines.append(f"| {pr['repo_name']} | [#{pr['number']} {pr['title']}]({pr['url']}) | {pr['age_days']} days |")
            report_lines.append("")

    # Failed Builds Section
    report_lines.append("## Failed Builds (Last 12 Hours)")
    report_lines.append("")

    if not failed_builds:
        report_lines.append("*No failed builds in the last 12 hours.* 🎉")
        report_lines.append("")
    else:
        report_lines.append("| Repository | Workflow | Branch | Failed |")
        report_lines.append("|------------|----------|--------|--------|")
        for build in failed_builds:
            failed_time = relative_time(build["failed_at"])
            report_lines.append(f"| {build['repo_name']} | [{build['workflow_name']}]({build['url']}) | {build['branch']} | {failed_time} |")
        report_lines.append("")

    # Stale Branches Section
    report_lines.append("## Stale Branches (30+ Days)")
    report_lines.append("")

    if not stale_branches:
        report_lines.append("*No stale branches found.* 🎉")
        report_lines.append("")
    else:
        report_lines.append("| Repository | Branch | Age | Last Commit By |")
        report_lines.append("|------------|--------|-----|----------------|")
        for branch in stale_branches:
            report_lines.append(f"| {branch['repo_name']} | {branch['branch_name']} | {branch['age_days']} days | {branch['last_commit_author']} |")
        report_lines.append("")

    # Errors Section (if any)
    if errors:
        report_lines.append("## Errors")
        report_lines.append("")
        for error in errors:
            report_lines.append(f"- ⚠️ {error}")
        report_lines.append("")

    report_lines.append("---")
    report_lines.append("*Report generated by DevOps Digest*")

    return "\n".join(report_lines), errors


def save_report(content):
    """
    Save report content to the reports directory.

    Returns the path to the saved file.
    """
    script_dir = Path(__file__).parent.parent
    reports_dir = script_dir / "reports"
    reports_dir.mkdir(exist_ok=True)

    report_date = datetime.now().strftime("%Y-%m-%d")
    report_path = reports_dir / f"devops-digest-{report_date}.md"

    with open(report_path, "w") as f:
        f.write(content)

    return report_path


def open_report(report_path):
    """Open the report in the default markdown viewer."""
    if sys.platform == "darwin":  # macOS
        subprocess.run(["open", str(report_path)], check=False)
    elif sys.platform == "win32":  # Windows
        subprocess.run(["start", str(report_path)], shell=True, check=False)
    else:  # Linux and others
        subprocess.run(["xdg-open", str(report_path)], check=False)
