#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "typer>=0.15",
#     "pyyaml>=6.0",
# ]
# ///
"""Sync GitHub Issues to local markdown files for agent workflows.

Workflow:
  1. scripts/issues pull        — sync all open issues locally
  2. Copy/reference the relevant issue into .local-docs/current-issue
  3. Work on the issue
  4. Update .local-docs/current-issue with the Done section
  5. scripts/issues push        — update the GitHub Issue
  6. Close the issue via gh issue close or through a PR
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

# Resolved by uv from the PEP 723 metadata above, not the project virtualenv.
import typer
import yaml

app = typer.Typer(help=__doc__)


@lru_cache
def _bin(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        typer.echo(f"Error: {name} not found on PATH.", err=True)
        raise typer.Exit(1)
    return path


@lru_cache
def _repo_root() -> Path:
    result = subprocess.run(
        [_bin("git"), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        typer.echo("Error: not inside a git repository.", err=True)
        raise typer.Exit(1)
    return Path(result.stdout.strip())


def _default_issues_dir() -> Path:
    return _repo_root() / ".local-docs" / "issues"


def _default_current_issue() -> Path:
    return _repo_root() / ".local-docs" / "current-issue"


ISSUES_QUERY = """\
query($owner: String!, $repo: String!, $endCursor: String) {
  repository(owner: $owner, name: $repo) {
    issues(first: 100, after: $endCursor, orderBy: {field: CREATED_AT, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number
        title
        body
        state
        url
        createdAt
        updatedAt
        labels(first: 20) { nodes { name } }
        assignees(first: 10) { nodes { login } }
        milestone { title }
      }
    }
  }
}
"""

SINGLE_ISSUE_QUERY = """\
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    issue(number: $number) {
      number
      title
      body
      state
      url
      createdAt
      updatedAt
      labels(first: 20) { nodes { name } }
      assignees(first: 10) { nodes { login } }
      milestone { title }
    }
  }
}
"""


def _check_gh() -> None:
    result = subprocess.run(
        [_bin("gh"), "auth", "status"], capture_output=True, text=True
    )
    if result.returncode != 0:
        typer.echo("Error: gh is not authenticated. Run: gh auth login", err=True)
        raise typer.Exit(1)


def _get_repo_owner_and_name() -> tuple[str, str]:
    result = subprocess.run(
        [_bin("gh"), "repo", "view", "--json", "nameWithOwner"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        typer.echo(
            f"Error: could not determine repository: {result.stderr.strip()}", err=True
        )
        raise typer.Exit(1)
    data = json.loads(result.stdout)
    owner, name = data["nameWithOwner"].split("/", 1)
    return owner, name


def _slugify(title: str) -> str:
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug[:60]


def _issue_to_markdown(issue: dict[str, Any]) -> str:
    labels = [node["name"] for node in issue.get("labels", {}).get("nodes", [])]
    assignees = [node["login"] for node in issue.get("assignees", {}).get("nodes", [])]
    milestone = None
    if issue.get("milestone"):
        milestone = issue["milestone"]["title"]

    front_matter: dict[str, Any] = {
        "number": issue["number"],
        "title": issue["title"],
        "state": issue["state"],
        "url": issue["url"],
        "created_at": issue["createdAt"],
        "updated_at": issue["updatedAt"],
    }
    if labels:
        front_matter["labels"] = labels
    if assignees:
        front_matter["assignees"] = assignees
    if milestone:
        front_matter["milestone"] = milestone

    fm = yaml.dump(front_matter, default_flow_style=False, sort_keys=False).rstrip()
    body = issue.get("body") or ""
    return f"---\n{fm}\n---\n\n{body}\n"


def _parse_issue_file(path: Path) -> tuple[dict[str, Any], str]:
    content = path.read_text()
    if not content.startswith("---"):
        typer.echo(
            f"Error: {path} does not start with YAML front-matter (---)", err=True
        )
        raise typer.Exit(1)
    parts = content.split("---", 2)
    if len(parts) < 3:
        typer.echo(f"Error: {path} has malformed front-matter", err=True)
        raise typer.Exit(1)
    metadata = yaml.safe_load(parts[1])
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        typer.echo(
            f"Error: {path} front-matter must be a YAML mapping, got {type(metadata).__name__}",
            err=True,
        )
        raise typer.Exit(1)
    body = parts[2].strip()
    return metadata, body


def _fetch_issue(owner: str, name: str, number: int) -> dict[str, Any]:
    result = subprocess.run(
        [
            _bin("gh"),
            "api",
            "graphql",
            "-F",
            f"owner={owner}",
            "-F",
            f"repo={name}",
            "-F",
            f"number={number}",
            "-f",
            f"query={SINGLE_ISSUE_QUERY}",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        typer.echo(f"Error fetching issue #{number}: {result.stderr.strip()}", err=True)
        raise typer.Exit(1)
    data = json.loads(result.stdout)
    return data["data"]["repository"]["issue"]


@app.command()
def pull(
    issues_dir: Annotated[
        Path,
        typer.Option(
            help="Directory to write issue files to. \\[default: <repo-root>/.local-docs/issues]",
            default_factory=_default_issues_dir,
            show_default=False,
        ),
    ],
) -> None:
    """Fetch all issues from GitHub and write them to .local-docs/issues/."""
    _check_gh()
    owner, name = _get_repo_owner_and_name()

    typer.echo("Fetching issues from GitHub...")
    result = subprocess.run(
        [
            _bin("gh"),
            "api",
            "graphql",
            "--paginate",
            "-F",
            f"owner={owner}",
            "-F",
            f"repo={name}",
            "-f",
            f"query={ISSUES_QUERY}",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        typer.echo(f"Error fetching issues: {result.stderr.strip()}", err=True)
        raise typer.Exit(1)

    issues: list[dict[str, Any]] = []
    for line in result.stdout.strip().splitlines():
        if not line:
            continue
        page = json.loads(line)
        nodes = page["data"]["repository"]["issues"]["nodes"]
        issues.extend(nodes)

    issues_dir.mkdir(parents=True, exist_ok=True)
    for old in issues_dir.glob("*.md"):
        old.unlink()

    with typer.progressbar(issues, label="Writing issues") as progress:
        for issue in progress:
            slug = _slugify(issue["title"])
            filename = f"{issue['number']}-{slug}.md"
            (issues_dir / filename).write_text(_issue_to_markdown(issue))

    typer.echo(f"Pulled {len(issues)} issues to {issues_dir}/")


@app.command()
def push(
    current_issue: Annotated[
        Path,
        typer.Option(
            help="Path to the issue file to push. \\[default: <repo-root>/.local-docs/current-issue]",
            default_factory=_default_current_issue,
            show_default=False,
        ),
    ],
) -> None:
    """Create or update a GitHub Issue from .local-docs/current-issue."""
    _check_gh()
    owner, name = _get_repo_owner_and_name()

    if not current_issue.exists():
        typer.echo(
            f"Error: {current_issue} not found. Copy an issue file there first.",
            err=True,
        )
        raise typer.Exit(1)

    metadata, body = _parse_issue_file(current_issue)
    number = metadata.get("number")

    cmd: list[str] = []
    if number:
        cmd = [_bin("gh"), "issue", "edit", str(number)]
    else:
        cmd = [_bin("gh"), "issue", "create"]

    title = metadata.get("title")
    if title:
        cmd.extend(["--title", title])

    for label in metadata.get("labels", []):
        cmd.extend(["--label", label])

    for assignee in metadata.get("assignees", []):
        cmd.extend(["--assignee", assignee])

    milestone = metadata.get("milestone")
    if milestone:
        cmd.extend(["--milestone", milestone])

    cmd.extend(["--body", body])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        typer.echo(f"Error: {result.stderr.strip()}", err=True)
        raise typer.Exit(1)

    if number:
        typer.echo(f"Updated issue #{number}")
    else:
        url = result.stdout.strip()
        new_number = int(url.rstrip("/").split("/")[-1])
        typer.echo(f"Created issue #{new_number}: {url}")
        issue = _fetch_issue(owner, name, new_number)
        current_issue.write_text(_issue_to_markdown(issue))
        typer.echo(f"Synced issue #{new_number} back to {current_issue}")


if __name__ == "__main__":
    app()
