#!/usr/bin/env python3
"""Print the next sequential 4-digit ADR ID (zero-padded).

Scans docs/adr/*.md for the highest `NNNN-*.md` id and prints that + 1 (or 0001
when none exist). Repo-root anchored and cross-platform (no shell utilities).
"""

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

adr_dir = Path("docs/adr")
highest = 0
if adr_dir.exists():
    for path in adr_dir.glob("*.md"):
        m = re.match(r"(\d{4})-", path.name)
        if m:
            highest = max(highest, int(m.group(1)))

print(f"{highest + 1:04d}")
