# DevOps Digest

A CLI tool for generating daily development reports from GitHub. Track your pull requests, monitor failed builds, and identify stale branches across multiple repositories.

## Features

- **Pull Request Tracking** - View all open PRs where you're involved (authored, reviewing, or mentioned)
- **Failed Build Monitoring** - Check for failed GitHub Actions workflow runs in the last 12 hours
- **Stale Branch Detection** - Identify branches older than 30 days that you've authored
- **Markdown Reports** - Generate comprehensive reports saved to `reports/` directory
- **Team-based Configuration** - Configure repositories by team for build monitoring
- **Docker Support** - Run in containers for consistent environments

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set your GitHub token as an environment variable:
   ```bash
   export GITHUB_TOKEN=your_github_personal_access_token
   ```

## Configuration

Configure repositories and teams in `conf/data.json`:

```json
{
  "repositories": [
    { "name": "repo-name-1" },
    { "name": "repo-name-2" }
  ],
  "teams": [
    { "name": "Frontend" },
    { "name": "Backend" }
  ]
}
```

- **repositories** - Repositories to check for stale branches (matched by name pattern)
- **teams** - GitHub teams whose repositories are checked for failed builds

## Usage

### Generate Full Report
Generate a comprehensive DevOps digest report with all metrics:
```bash
python devops-digest.py
```

The report is saved to `reports/devops-digest-YYYY-MM-DD.md` and includes:
- Summary table with PR count, failed builds, and stale branches
- Grouped pull requests (My PRs, Reviewing, Mentioned)
- Failed builds from the last 12 hours
- Stale branches older than 30 days

### Generate and View Report
Generate a report and open it in your default viewer:
```bash
python devops-digest.py --view
```

### Test GitHub Token
Verify that your GitHub token is configured correctly:
```bash
python devops-digest.py --test
```

### View Pull Requests Only
Show all open PRs where you're involved:
```bash
python devops-digest.py --prs
```

### View Failed Builds Only
Show failed GitHub Actions builds from the last 12 hours:
```bash
python devops-digest.py --builds
```

### View Stale Branches Only
Show your branches older than 30 days:
```bash
python devops-digest.py --stale
```

### Debug Mode
Enable debug output for troubleshooting:
```bash
python devops-digest.py --debug
```

## Docker

### Build and run with Docker
```bash
docker build -t devops-digest .
docker run -e GITHUB_TOKEN=your_token devops-digest
```

### Run with docker-compose
```bash
export GITHUB_TOKEN=your_github_personal_access_token
docker-compose run devops-digest
```

### Run specific commands in Docker
```bash
docker-compose run devops-digest --prs
docker-compose run devops-digest --builds
docker-compose run devops-digest --stale
```

## Project Structure

```
devops-digest/
├── devops-digest.py       # Main CLI entry point
├── conf/
│   └── data.json          # Repository and team configuration
├── devops_digest/
│   ├── branches.py        # Stale branch detection
│   ├── builds.py          # Failed build monitoring
│   ├── config.py          # Configuration constants
│   ├── display.py         # Terminal output formatting
│   ├── github_api.py      # GitHub API utilities
│   ├── prs.py             # Pull request fetching
│   ├── report.py          # Report generation and saving
│   └── utils.py           # Helper utilities
├── reports/               # Generated reports directory
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Requirements

- Python 3.8+ (or Docker)
- GitHub personal access token with `repo` scope
- Dependencies: `click>=8.0.0`, `requests>=2.28.0`
