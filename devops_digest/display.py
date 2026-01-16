"""Terminal display functions for DevOps Digest."""

import click

from .utils import relative_time


def display_prs(grouped_prs):
    """Display PRs in a formatted way in the terminal."""
    sections = [
        ("My PRs", grouped_prs["my_prs"]),
        ("Reviewing", grouped_prs["reviewing"]),
        ("Mentioned", grouped_prs["mentioned"]),
    ]

    total_count = sum(len(prs) for _, prs in sections)
    if total_count == 0:
        click.echo("No open PRs found.")
        return

    for section_name, prs in sections:
        if not prs:
            continue

        click.echo()
        click.secho(f"{'─' * 60}", fg="bright_black")
        click.secho(f" {section_name} ({len(prs)})", fg="cyan", bold=True)
        click.secho(f"{'─' * 60}", fg="bright_black")

        for pr in prs:
            # Age color coding
            if pr["age_days"] > 7:
                age_color = "red"
            elif pr["age_days"] > 3:
                age_color = "yellow"
            else:
                age_color = "green"

            click.echo()
            click.secho(f"  {pr['repo_name']}", fg="bright_blue")
            click.echo(f"  #{pr['number']} {pr['title']}")
            click.secho(f"  Age: {pr['age_days']} days", fg=age_color)
            click.secho(f"  {pr['url']}", fg="bright_black")


def display_failed_builds(builds):
    """Display failed builds in a formatted way in the terminal."""
    if not builds:
        click.echo("No failed builds in the last 12 hours.")
        return

    click.echo()
    click.secho(f"{'─' * 60}", fg="bright_black")
    click.secho(f" Failed Builds ({len(builds)})", fg="red", bold=True)
    click.secho(f"{'─' * 60}", fg="bright_black")

    for build in builds:
        click.echo()
        click.secho(f"  {build['repo_name']}", fg="bright_blue")
        click.echo(f"  {build['workflow_name']} on {build['branch']}")
        click.secho(f"  Failed: {relative_time(build['failed_at'])}", fg="red")
        click.secho(f"  {build['url']}", fg="bright_black")


def display_stale_branches(branches):
    """Display stale branches in a formatted way in the terminal."""
    if not branches:
        click.echo("No stale branches found (older than 30 days).")
        return

    click.echo()
    click.secho(f"{'─' * 60}", fg="bright_black")
    click.secho(f" Stale Branches ({len(branches)})", fg="yellow", bold=True)
    click.secho(f"{'─' * 60}", fg="bright_black")

    for branch in branches:
        # Age color coding
        if branch["age_days"] > 90:
            age_color = "red"
        elif branch["age_days"] > 60:
            age_color = "yellow"
        else:
            age_color = "white"

        click.echo()
        click.secho(f"  {branch['repo_name']}", fg="bright_blue")
        click.echo(f"  Branch: {branch['branch_name']}")
        click.secho(f"  Age: {branch['age_days']} days", fg=age_color)
        click.secho(f"  Last commit by: {branch['last_commit_author']}", fg="bright_black")
