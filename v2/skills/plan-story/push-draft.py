#!/usr/bin/env python3
"""Push current branch and open a draft PR with the plan as body."""

import os
import sys
import subprocess
from pathlib import Path

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


def find_legacy_file(story_id):
    for root in ("specs/done", "specs/cancelled"):
        for ext in ("feature", "md"):
            for p in Path(root).rglob(f"{story_id}-*.{ext}"):
                return p
    return None


def read_story_title(story_id):
    """Title from the story's GitHub issue (source of truth); legacy file, then
    the bare id, as fallbacks."""
    title = run(
        'gh issue list --state all --search "%s in:title" '
        '--json title --jq \'.[] | select(.title | startswith("%s:")) | .title\' | head -1'
        % (story_id, story_id),
        check=False,
    )
    if title:
        return title.split(":", 1)[1].strip()
    path = find_legacy_file(story_id)
    if path:
        for line in path.read_text().splitlines():
            if line.strip().startswith("Feature:"):
                return line.strip().removeprefix("Feature:").strip()
            if line.strip().startswith("## "):
                return line.strip().removeprefix("## ").strip()
    return story_id


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: push-draft.py <story-id>", file=sys.stderr)
        sys.exit(1)
    story_id = sys.argv[1]
    title = read_story_title(story_id)
    plan_file = Path(f"docs/plans/{story_id}.md")
    branch = run("git branch --show-current")
    run(f'git push -u origin "{branch}"')
    if plan_file.exists():
        run(f'gh pr create --draft --title "{story_id}: {title}" --body-file "{plan_file}"')
    else:
        run(f'gh pr create --draft --title "{story_id}: {title}" --body "Plan: see docs/plans/{story_id}.md"')
    pr_url = run("gh pr view --json url --jq .url")
    print(f"Draft PR opened: {pr_url}")
