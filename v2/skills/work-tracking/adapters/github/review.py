#!/usr/bin/env python3
"""GitHub adapter — change integration (implements the work-tracking review CLI).

Maps the change-request model onto GitHub pull requests:
  open-draft <id>  push the story branch, open a DRAFT PR with the plan as body
  mark-ready <id>  flip the PR from draft to ready for review
  checks <id>      report the PR's CI status
  diff <id>        print the PR's full diff
  post-review <id> --body-file F   post a summary review comment on the PR
  merge <id>       squash-merge the PR, delete the branch, reset local main

Consolidates what were three per-skill scripts (push-draft.py, pr-ready.py,
merge-pr.py). Invoked via the façade `skills/work-tracking/review.py`.

All subprocess calls use argument LISTS (no shell) so the adapter runs identically
on Linux, macOS, and Windows — no reliance on POSIX utilities like head/tail/pipes.
"""

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


def run(args, check=True):
    """Run a command given as a list (no shell) and return stripped stdout."""
    result = subprocess.run(args, capture_output=True, text=True, check=check)
    return (result.stdout or "").strip()


def _find_legacy_file(story_id):
    for root in ("specs/done", "specs/cancelled"):
        for ext in ("feature", "md"):
            for p in Path(root).rglob(f"{story_id}-*.{ext}"):
                return p
    return None


def _story_title(story_id):
    """Story title from its GitHub issue; legacy file, then the bare id, as fallbacks."""
    out = run(
        ["gh", "issue", "list", "--state", "all", "--search", f"{story_id} in:title",
         "--json", "title", "--jq",
         f'.[] | select(.title | startswith("{story_id}:")) | .title'],
        check=False,
    )
    if out:
        first = out.splitlines()[0]
        if ":" in first:
            return first.split(":", 1)[1].strip()
    path = _find_legacy_file(story_id)
    if path:
        for line in path.read_text().splitlines():
            if line.strip().startswith("Feature:"):
                return line.strip().removeprefix("Feature:").strip()
            if line.strip().startswith("## "):
                return line.strip().removeprefix("## ").strip()
    return story_id


def _find_pr_number(story_id):
    branch = run(["git", "branch", "--show-current"])
    output = run(["gh", "pr", "list", "--head", branch, "--json", "number",
                  "--jq", ".[0].number"], check=False)
    if output:
        return output
    output = run(["gh", "pr", "list", "--search", f"head:{story_id}", "--json", "number",
                  "--jq", ".[0].number"], check=False)
    return output or None


def cmd_open_draft(story_id):
    """Push the current branch and open a draft PR with the plan as body."""
    title = _story_title(story_id)
    plan_file = Path(f"docs/plans/{story_id}.md")
    branch = run(["git", "branch", "--show-current"])
    run(["git", "push", "-u", "origin", branch])
    if plan_file.exists():
        run(["gh", "pr", "create", "--draft", "--title", f"{story_id}: {title}",
             "--body-file", str(plan_file)])
    else:
        run(["gh", "pr", "create", "--draft", "--title", f"{story_id}: {title}",
             "--body", f"Plan: see docs/plans/{story_id}.md"])
    pr_url = run(["gh", "pr", "view", "--json", "url", "--jq", ".url"])
    print(f"Draft PR opened: {pr_url}")


def cmd_mark_ready(story_id):
    """Flip the story's PR from draft to ready for review."""
    pr_number = _find_pr_number(story_id)
    if not pr_number:
        print(f"error: no open PR found for {story_id}", file=sys.stderr)
        sys.exit(1)
    uncommitted = run(["git", "status", "--porcelain"], check=False)
    tracked_changes = "\n".join(l for l in uncommitted.splitlines() if not l.startswith("??"))
    if tracked_changes:
        print(f"error: uncommitted changes present — commit or stash before marking ready:\n"
              f"{tracked_changes}", file=sys.stderr)
        sys.exit(1)
    branch = run(["git", "branch", "--show-current"])
    run(["git", "push", "origin", branch])
    run(["gh", "pr", "ready", str(pr_number)])
    print(f"{story_id} PR #{pr_number} marked ready for review.")


def cmd_checks(story_id):
    """Report the CI status of the story's PR."""
    pr_number = _find_pr_number(story_id)
    if not pr_number:
        print(f"error: no open PR found for {story_id}", file=sys.stderr)
        sys.exit(1)
    # `gh pr checks` exits non-zero when checks are pending/failing; surface output either way.
    output = run(["gh", "pr", "checks", str(pr_number)], check=False)
    print(output or f"(no checks reported for PR #{pr_number})")


def cmd_diff(story_id):
    """Print the change request's full diff (what a reviewer reads)."""
    pr_number = _find_pr_number(story_id)
    if pr_number:
        output = run(["gh", "pr", "diff", str(pr_number)], check=False)
        if output:
            print(output)
            return
    # Fallback: local diff against origin/main when no PR / gh is unavailable.
    print(run(["git", "diff", "origin/main...HEAD"], check=False) or "")


def cmd_post_review(story_id, body_file):
    """Post a summary review comment on the change request (event: comment only)."""
    pr_number = _find_pr_number(story_id)
    if not pr_number:
        print(f"error: no open PR found for {story_id}", file=sys.stderr)
        sys.exit(1)
    if not Path(body_file).exists():
        print(f"error: body file not found: {body_file}", file=sys.stderr)
        sys.exit(1)
    run(["gh", "pr", "review", str(pr_number), "--comment", "--body-file", body_file])
    print(f"posted review comment on PR #{pr_number} for {story_id}")


def cmd_merge(story_id):
    """Squash-merge the PR, delete the branch, reset local main."""
    pr_number = _find_pr_number(story_id)
    if not pr_number:
        print(f"error: no open PR found for {story_id}", file=sys.stderr)
        sys.exit(1)
    run(["gh", "pr", "merge", str(pr_number), "--squash", "--delete-branch"])
    run(["git", "checkout", "main"])
    run(["git", "fetch", "origin"])
    run(["git", "reset", "--hard", "origin/main"])
    short_sha = run(["git", "rev-parse", "--short", "HEAD"])
    subject = run(["git", "log", "-1", "--format=%s"])
    print(f"{story_id} merged. main is at {short_sha}: {subject}")


# Simple commands: take a single <story-id> argument.
SIMPLE_COMMANDS = {
    "open-draft": cmd_open_draft,
    "mark-ready": cmd_mark_ready,
    "checks": cmd_checks,
    "diff": cmd_diff,
    "merge": cmd_merge,
}

USAGE = """\
Usage: review.py <command> <story-id> [flags]   (GitHub adapter for the work-tracking contract)

Invoke through the façade: python3 .claude/skills/work-tracking/review.py <command> <id>

Commands:
  open-draft <id>                push the branch, open a draft PR with the plan as body
  mark-ready <id>                flip the PR from draft to ready for review
  checks <id>                    report the PR's CI status
  diff <id>                      print the PR's full diff
  post-review <id> --body-file F post a summary review comment on the PR
  merge <id>                     squash-merge the PR, delete the branch, reset local main"""


def _parse_body_file(args):
    """Extract --body-file F from trailing args."""
    for i, a in enumerate(args):
        if a in ("--body-file", "-body-file") and i + 1 < len(args):
            return args[i + 1]
    return None


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(USAGE)
        sys.exit(1)
    command, story = sys.argv[1], sys.argv[2]
    if command in SIMPLE_COMMANDS:
        SIMPLE_COMMANDS[command](story)
    elif command == "post-review":
        body_file = _parse_body_file(sys.argv[3:])
        if not body_file:
            print("error: post-review requires: <id> --body-file F", file=sys.stderr)
            sys.exit(1)
        cmd_post_review(story, body_file)
    else:
        print(USAGE)
        sys.exit(1)
