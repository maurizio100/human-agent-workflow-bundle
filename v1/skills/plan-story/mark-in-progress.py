#!/usr/bin/env python3
"""Mark a story as in-progress in specs/STORIES.md."""

import os
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

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: mark-in-progress.py <story-id>", file=sys.stderr)
        sys.exit(1)
    story_id = sys.argv[1]
    lines = INDEX.read_text().splitlines()
    found = False
    for i, line in enumerate(lines):
        if line.startswith(f"| {story_id} |"):
            parts = [p.strip() for p in line.split("|")]
            parts[-2] = "in-progress"
            lines[i] = "| " + " | ".join(parts[1:-1]) + " |"
            found = True
            break
    if not found:
        print(f"error: {story_id} not found in {INDEX}", file=sys.stderr)
        sys.exit(1)
    INDEX.write_text("\n".join(lines) + "\n")
