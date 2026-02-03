#!/usr/bin/env python3
"""DevOps Digest - A CLI tool for generating daily development reports."""

import click
import requests

from devops_digest import (
    get_github_token,
    get_github_username,
    load_config_repos,
    load_config_teams,
    get_my_pull_requests,
    get_failed_actions,
    get_stale_branches,
    generate_report,
    save_report,
    open_report,
    display_prs,
    display_failed_actions,
    display_stale_branches,
)


@click.command()
@click.option("--test", is_flag=True, help="Test GitHub token and display username")
@click.option("--prs", is_flag=True, help="Show all open PRs where you're involved")
@click.option("--actions", is_flag=True, help="Show failed GitHub Actions from the last 12 hours")
@click.option("--stale", is_flag=True, help="Show stale branches older than 30 days")
@click.option("--view", is_flag=True, help="Open the generated report in default viewer")
@click.option("--debug", is_flag=True, help="Show debug information")
def main(test, prs, actions, stale, view, debug):
    """DevOps Digest - Generate daily development reports."""
    if test:
        token = get_github_token()
        try:
            username = get_github_username(token)
            click.echo(f"GitHub token is valid. Authenticated as: {username}")
        except requests.exceptions.HTTPError as e:
            raise click.ClickException(f"GitHub API error: {e}")
        except requests.exceptions.RequestException as e:
            raise click.ClickException(f"Network error: {e}")
    elif prs:
        token = get_github_token()
        try:
            username = get_github_username(token)
            click.echo(f"Fetching PRs for {username}...")
            grouped_prs = get_my_pull_requests(token, username, debug)
            display_prs(grouped_prs)
        except requests.exceptions.HTTPError as e:
            raise click.ClickException(f"GitHub API error: {e}")
        except requests.exceptions.RequestException as e:
            raise click.ClickException(f"Network error: {e}")
    elif actions:
        token = get_github_token()
        try:
            click.echo("Loading team repositories from config...")
            repo_names = load_config_teams(token)
            if not repo_names:
                click.secho("No repositories found for configured teams.", fg="yellow")
                click.echo("Falling back to configured repositories...")
                repo_names = load_config_repos(token)

            if not repo_names:
                click.echo("No matching repositories found.")
                return

            click.echo(f"Checking {len(repo_names)} repositories for failed actions...")
            failed_actions = get_failed_actions(token, repo_names)
            display_failed_actions(failed_actions)
        except requests.exceptions.HTTPError as e:
            raise click.ClickException(f"GitHub API error: {e}")
        except requests.exceptions.RequestException as e:
            raise click.ClickException(f"Network error: {e}")
    elif stale:
        token = get_github_token()
        try:
            username = get_github_username(token)

            click.echo("Loading repositories from config...")
            repo_names = load_config_repos(token)
            if not repo_names:
                click.echo("No matching repositories found.")
                return

            click.echo(f"Fetching stale branches for {username} (older than 30 days)...")
            stale_branches = get_stale_branches(token, username, repo_names)
            display_stale_branches(stale_branches)
        except requests.exceptions.HTTPError as e:
            raise click.ClickException(f"GitHub API error: {e}")
        except requests.exceptions.RequestException as e:
            raise click.ClickException(f"Network error: {e}")
    else:
        # Default: generate full report
        token = get_github_token()
        try:
            click.echo()
            click.secho("╔════════════════════════════════════════╗", fg="cyan")
            click.secho("║       DevOps Digest Report             ║", fg="cyan", bold=True)
            click.secho("╚════════════════════════════════════════╝", fg="cyan")
            click.echo()

            username = get_github_username(token)
            click.secho(f"👤 Authenticated as: {username}", fg="green")
            click.echo()

            click.echo("Loading repositories from config...")
            repo_names = load_config_repos(token)
            if not repo_names:
                click.secho("⚠️  No matching repositories found in config.", fg="yellow")
                repo_names = []
            else:
                click.secho(f"📦 Found {len(repo_names)} repositories", fg="green")

            click.echo("Loading team repositories for actions...")
            team_repo_names = load_config_teams(token)
            if not team_repo_names:
                click.secho("⚠️  No team repositories found, using config repos for actions.", fg="yellow")
                team_repo_names = repo_names
            else:
                click.secho(f"📦 Found {len(team_repo_names)} team repositories", fg="green")

            click.echo()
            click.secho("Fetching data:", fg="cyan", bold=True)

            report_content, errors = generate_report(token, username, repo_names, team_repo_names, debug)

            click.echo()
            report_path = save_report(report_content)
            click.secho(f"✅ Report saved to: {report_path}", fg="green", bold=True)

            if errors:
                click.echo()
                click.secho(f"⚠️  {len(errors)} error(s) occurred during generation", fg="yellow")

            # Print report to stdout
            click.echo()
            click.secho("═" * 80, fg="cyan")
            click.secho("REPORT CONTENT", fg="cyan", bold=True)
            click.secho("═" * 80, fg="cyan")
            click.echo()
            click.echo(report_content)
            click.echo()
            click.secho("═" * 80, fg="cyan")

            if view:
                click.echo()
                click.echo("Opening report in default viewer...")
                open_report(report_path)

        except requests.exceptions.HTTPError as e:
            raise click.ClickException(f"GitHub API error: {e}")
        except requests.exceptions.RequestException as e:
            raise click.ClickException(f"Network error: {e}")


if __name__ == "__main__":
    main()
