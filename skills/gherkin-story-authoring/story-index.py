#!/usr/bin/env python3
"""Manage the story index at specs/STORIES.md."""

import os
import re
import subprocess
import sys
from pathlib import Path

try:
    _repo_root = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True, stderr=subprocess.DEVNULL
    ).strip()
except subprocess.CalledProcessError:
    print("error: not in a git repository", file=sys.stderr)
    sys.exit(1)
os.chdir(_repo_root)

INDEX = Path("specs/STORIES.md")


def read_lines():
    return INDEX.read_text().splitlines()


def write_lines(lines):
    INDEX.write_text("\n".join(lines) + "\n")


def cmd_add(args):
    if len(args) != 6:
        print("error: add requires 6 arguments: <id> <epic> <title> <context> <layer> <status>", file=sys.stderr)
        sys.exit(1)
    story_id, epic, title, context, layer, status = args
    row = f"| {story_id} | {epic} | {title} | {context} | {layer} | {status} |"
    with INDEX.open("a") as f:
        f.write(row + "\n")


def cmd_update_status(args):
    if len(args) != 2:
        print("error: update-status requires 2 arguments: <id> <new-status>", file=sys.stderr)
        sys.exit(1)
    story_id, new_status = args
    lines = read_lines()
    found = False
    for i, line in enumerate(lines):
        if line.startswith(f"| {story_id} |"):
            parts = [p.strip() for p in line.split("|")]
            parts[-2] = new_status
            lines[i] = "| " + " | ".join(parts[1:-1]) + " |"
            found = True
            break
    if not found:
        print(f"error: {story_id} not found in {INDEX}", file=sys.stderr)
        sys.exit(1)
    write_lines(lines)


def cmd_next_id(args):
    text = INDEX.read_text()
    ids = [int(m) for m in re.findall(r"STORY-(\d+)", text)]
    next_num = max(ids) + 1 if ids else 1
    print(f"STORY-{next_num:03d}")


COMMANDS = {
    "add": cmd_add,
    "update-status": cmd_update_status,
    "next-id": cmd_next_id,
}

USAGE = """\
Usage: story-index.py <command> [args]

Commands:
  add <id> <epic> <title> <context> <layer> <status>
      Append a row to the story index.
      Use "—" for empty epic or context.

  update-status <id> <new-status>
      Change the status column for an existing story.

  next-id
      Print the next available STORY-NNN ID."""

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(USAGE)
        sys.exit(1)
    COMMANDS[sys.argv[1]](sys.argv[2:])
