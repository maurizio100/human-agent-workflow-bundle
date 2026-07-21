#!/bin/bash
# Returns the next sequential 4-digit ADR ID (zero-padded).
# Run from the repository root.
highest=$(ls docs/adr/*.md 2>/dev/null | grep -oE '/[0-9]{4}-' | grep -oE '[0-9]{4}' | sort -n | tail -1)
if [ -z "$highest" ]; then
  echo "0001"
else
  printf "%04d\n" $((10#$highest + 1))
fi
