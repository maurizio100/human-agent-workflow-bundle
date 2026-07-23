#!/usr/bin/env python3
"""Squash-merge the story PR, delete branch, reset local main."""

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
        print("Usage: merge-pr.py <story-id>", file=sys.stderr)
        sys.exit(1)
    story_id = sys.argv[1]
    pr_number = find_pr_number(story_id)
    if not pr_number:
        print(f"error: no open PR found for {story_id}", file=sys.stderr)
        sys.exit(1)
    run(f"gh pr merge {pr_number} --squash --delete-branch")
    run("git checkout main")
    run("git fetch origin")
    run("git reset --hard origin/main")
    short_sha = run("git rev-parse --short HEAD")
    subject = run("git log -1 --format=%s")
    print(f"{story_id} merged. main is at {short_sha}: {subject}")
