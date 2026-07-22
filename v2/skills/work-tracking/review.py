#!/usr/bin/env python3
"""Work-tracking façade — change integration (open-draft / mark-ready / checks / merge).

Skills call THIS script, never a forge CLI directly. It resolves the active
backend adapter (from adapter.conf, default "github") and forwards the command to
adapters/<active>/review.py. See SKILL.md for the operation vocabulary.
"""

import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))


def _active_adapter():
    conf = os.path.join(_HERE, "adapter.conf")
    if os.path.exists(conf):
        with open(conf) as fh:
            for line in fh:
                line = line.split("#", 1)[0].strip()
                if line:
                    return line
    return "github"


def main():
    adapter = _active_adapter()
    target = os.path.join(_HERE, "adapters", adapter, "review.py")
    if not os.path.exists(target):
        sys.stderr.write(
            f"error: work-tracking adapter '{adapter}' has no review.py at {target}\n"
        )
        sys.exit(1)
    # subprocess (not os.execv) so this works identically on Windows.
    result = subprocess.run([sys.executable, target, *sys.argv[1:]])
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
