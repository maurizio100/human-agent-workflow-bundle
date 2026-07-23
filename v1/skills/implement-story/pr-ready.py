#!/usr/bin/env python3
"""Mark the story PR as ready for review."""

import os
import sys
import subprocess

try:
    _repo_root = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True, stderr=subprocess.DEVNULL
    ).strip()
except subprocess.CalledProcessError:
    print("error: not in a git repository", file=sys.stderr)
    sys.exit(1)
os.chdir(_repo_root)


def run(cmd, capture=True, check=True):
    result = subprocess.run(cmd, shell=True, capture_output=capture, text=True, check=check)
    return result.stdout.strip() if capture else None


def find_pr_number(story_id):
    branch = run("git branch --show-current")
    output = run(f'gh pr list --head "{branch}" --json number --jq ".[0].number"', check=False)
    if output:
        return output
    output = run(f'gh pr list --search "head:{story_id}" --json number --jq ".[0].number"', check=False)
    return output or None


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: pr-ready.py <story-id>", file=sys.stderr)
        sys.exit(1)
    story_id = sys.argv[1]
    pr_number = find_pr_number(story_id)
    if not pr_number:
        print(f"error: no open PR found for {story_id}", file=sys.stderr)
        sys.exit(1)
    uncommitted = run("git status --porcelain", check=False)
    tracked_changes = "\n".join(l for l in uncommitted.splitlines() if not l.startswith("??"))
    if tracked_changes:
        print(f"error: uncommitted changes present — commit or stash before marking ready:\n{tracked_changes}", file=sys.stderr)
        sys.exit(1)
    branch = run("git branch --show-current")
    run(f'git push origin "{branch}"')
    run(f"gh pr ready {pr_number}")
    print(f"{story_id} PR #{pr_number} marked ready for review.")
