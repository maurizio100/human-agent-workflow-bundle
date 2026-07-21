#!/usr/bin/env python3
"""Story management via GitHub issues.

GitHub issues are the single source of truth for story state (status, epic,
context, layer, type) AND for story spec content — the issue body holds the
Gherkin / chore spec (see ADR-0021). There are no authored story files: content
is composed into the issue on `create` and edited in place with `update-body`.

`specs/done/` and `specs/cancelled/` remain as legacy pre-migration archives and
are still consulted by `next-id` so IDs are never reused.
"""

import json
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

# Legacy archives — no new files are written here; kept only so `next-id` never
# reuses an ID that a pre-migration file already claimed.
LEGACY_DIRS = (Path("specs/done"), Path("specs/cancelled"), Path("specs/stories"))

# Label colours (hex, no leading #).
LABEL_COLORS = {
    "epic": "1d76db",
    "context": "0e8a16",
    "layer": "5319e7",
    "type": "bfdadc",
    "status:draft": "fbca04",
    "status:ready": "0e8a16",
    "status:in-progress": "1d76db",
    "status:done": "c2e0c6",
    "status:superseded": "cccccc",
    "status:cancelled": "cccccc",
}
# Statuses that mean the issue should be closed rather than left open.
CLOSED_STATUSES = {"done", "superseded", "cancelled"}
ALL_STATUS_LABELS = [
    "status:draft", "status:ready", "status:in-progress",
    "status:done", "status:superseded", "status:cancelled",
]

# Controlled vocabulary for the `layer:` and `type:` labels. The `context:`
# vocabulary is derived from the bounded-context files in docs/domain/contexts/
# (see `_valid_contexts`) so it tracks the domain model rather than a hardcoded
# list.
VALID_LAYERS = {"frontend", "backend", "fullstack", "infra"}
VALID_TYPES = {"feature", "chore"}
CONTEXTS_DIR = Path("docs/domain/contexts")

# Leading classification-header lines (`# STORY-NNN`, `# Epic:`, `# Layer:`,
# `# Context:`, `# Type:`). If a supplied body still carries them (e.g. pasted
# from a legacy file) they are stripped — that classification lives on the
# labels, and GitHub would otherwise render them as H1 headings. Matches `#`
# (one hash) only, so real `##`/`###` Markdown headings in a chore body survive.
_HEADER_LINE = re.compile(r"^#\s*(STORY-\d+\b|Epic:|Layer:|Context:|Type:)")


# --- ID allocation ----------------------------------------------------------

def _legacy_story_ids():
    """Every STORY-NNN id claimed by a legacy archive file."""
    ids = set()
    for root in LEGACY_DIRS:
        if root.exists():
            for path in root.rglob("STORY-*"):
                m = re.match(r"STORY-(\d+)", path.name)
                if m:
                    ids.add(int(m.group(1)))
    return ids


def _github_story_ids():
    """Every STORY-NNN id that has a GitHub issue (open OR closed).

    Returns an empty set when gh is unavailable, so `next-id` can still fall
    back to the legacy files (with a warning) rather than fail outright.
    """
    if not _gh_available():
        return set()
    result = _gh("issue", "list", "--state", "all", "--search", "STORY in:title",
                 "--json", "title", "--limit", "1000", check=False)
    if result.returncode != 0:
        return set()
    ids = set()
    try:
        for issue in json.loads(result.stdout or "[]"):
            m = re.match(r"STORY-(\d+)\b", issue["title"])
            if m:
                ids.add(int(m.group(1)))
    except json.JSONDecodeError:
        pass
    return ids


def cmd_next_id(args):
    """Next available STORY-NNN — the max over GitHub issues AND legacy files.

    Both are consulted so an ID is never reused, even if an old issue was
    closed/superseded or a legacy file was never mirrored.
    """
    gh_ids = _github_story_ids()
    if not gh_ids and not _gh_available():
        print("warning: gh unavailable; allocating from legacy files only — "
              "the result may collide with issues not present locally",
              file=sys.stderr)
    ids = gh_ids | _legacy_story_ids()
    next_num = max(ids) + 1 if ids else 1
    print(f"STORY-{next_num:03d}")


# --- GitHub issues ----------------------------------------------------------

def _gh_available():
    """True if the gh CLI is installed and authenticated."""
    from shutil import which
    if which("gh") is None:
        print("note: gh CLI not found; skipping GitHub issue sync", file=sys.stderr)
        return False
    result = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
    if result.returncode != 0:
        print("note: gh CLI not authenticated; skipping GitHub issue sync", file=sys.stderr)
        return False
    return True


def _gh(*args, check=True, capture=True):
    return subprocess.run(["gh", *args], text=True, check=check, capture_output=capture)


def _epic_milestone_title(epic):
    """Full milestone title for an epic id.

    Epics live as GitHub milestones (ADR-0021): the milestone titled
    `EPIC-NNN: <name>` carries the epic's description. Resolve the full title by
    querying milestones for one whose title starts with the epic id. Falls back
    to the bare epic id if no milestone exists yet (a new epic), in which case
    `_ensure_milestone` creates a placeholder the author can flesh out.
    """
    if _dash(epic):
        return None
    result = _gh("api", "repos/{owner}/{repo}/milestones?state=all&per_page=100",
                 "--jq", ".[].title", check=False)
    if result.returncode == 0:
        for title in (result.stdout or "").splitlines():
            if title.startswith(f"{epic}:") or title == epic:
                return title
    return epic


def _dash(value):
    return not value or value in ("—", "-")


def _valid_contexts():
    """Bounded-context vocabulary, derived from docs/domain/contexts/*.md stems.

    Returns an empty set when the directory is absent, in which case context
    validation is skipped (the tool still works in repos without domain docs).
    """
    if not CONTEXTS_DIR.exists():
        return set()
    return {p.stem.lower() for p in CONTEXTS_DIR.glob("*.md")}


def _validate_metadata(story_id, context, layer, story_type):
    """Fail loudly on unknown context/layer/type values instead of minting
    drifted labels. Comma-separated contexts are each checked; `—`
    (cross-cutting) is always allowed for context and layer."""
    errors = []
    valid_contexts = _valid_contexts()
    if valid_contexts and not _dash(context):
        allowed = ", ".join(sorted(valid_contexts))
        for ctx in context.split(","):
            ctx = ctx.strip().lower()
            if ctx and ctx not in valid_contexts:
                errors.append(
                    f"unknown context '{ctx}' (allowed: {allowed}, or —)")
    if not _dash(layer) and layer.strip().lower() not in VALID_LAYERS:
        allowed = ", ".join(sorted(VALID_LAYERS))
        errors.append(f"unknown layer '{layer}' (allowed: {allowed}, or —)")
    if story_type and story_type.strip().lower() not in VALID_TYPES:
        allowed = ", ".join(sorted(VALID_TYPES))
        errors.append(f"unknown type '{story_type}' (allowed: {allowed})")
    if errors:
        for e in errors:
            print(f"error: {story_id}: {e}", file=sys.stderr)
        sys.exit(1)


def _clean_body(text):
    """Drop a leading classification-header block from a supplied body.

    Only the contiguous run of header lines at the top (plus any blank lines
    before real content) is stripped, so `#` comments or Markdown headings later
    in the body are left intact.
    """
    out = []
    in_header = True
    for line in text.splitlines():
        if in_header and (_HEADER_LINE.match(line) or (not out and not line.strip())):
            continue
        in_header = False
        out.append(line)
    return "\n".join(out).lstrip("\n")


def _labels_for(epic, context, layer, story_type, status):
    labels = []
    if not _dash(epic):
        labels.append(f"epic:{epic}")
    if not _dash(context):
        for ctx in context.split(","):
            ctx = ctx.strip().lower()
            if ctx:
                labels.append(f"context:{ctx}")
    if not _dash(layer):
        labels.append(f"layer:{layer.strip().lower()}")
    if story_type:
        labels.append(f"type:{story_type.strip().lower()}")
    labels.append(f"status:{status}")
    return labels


def _color_for(label):
    if label in LABEL_COLORS:
        return LABEL_COLORS[label]
    prefix = label.split(":", 1)[0]
    return LABEL_COLORS.get(prefix, "ededed")


def _ensure_label(label):
    _gh("label", "create", label, "--color", _color_for(label),
        "--description", label, "--force", check=False)


def _ensure_milestone(title):
    if not title:
        return
    existing = _gh("api", "repos/{owner}/{repo}/milestones?state=all",
                   "--jq", ".[].title", check=False)
    if title in (existing.stdout or "").splitlines():
        return
    _gh("api", "repos/{owner}/{repo}/milestones", "-f", f"title={title}", check=False)


def _find_issue(story_id):
    """Return the issue number for STORY-NNN, or None."""
    result = _gh("issue", "list", "--state", "all", "--search",
                 f"{story_id} in:title", "--json", "number,title",
                 "--limit", "50", check=False)
    if result.returncode != 0:
        return None
    try:
        for issue in json.loads(result.stdout or "[]"):
            if issue["title"].startswith(f"{story_id}:"):
                return issue["number"]
    except json.JSONDecodeError:
        pass
    return None


def _parse_flags(args, spec):
    """Tiny --key value parser. `spec` maps flag name -> required(bool)."""
    values = {k: None for k in spec}
    i = 0
    while i < len(args):
        key = args[i].lstrip("-")
        if key not in spec:
            print(f"error: unknown flag '{args[i]}'", file=sys.stderr)
            sys.exit(1)
        if i + 1 >= len(args):
            print(f"error: flag '{args[i]}' needs a value", file=sys.stderr)
            sys.exit(1)
        values[key] = args[i + 1]
        i += 2
    missing = [k for k, required in spec.items() if required and not values[k]]
    if missing:
        print(f"error: missing required flag(s): {', '.join('--' + m for m in missing)}",
              file=sys.stderr)
        sys.exit(1)
    return values


def _read_body(body_file):
    if body_file == "-":
        return _clean_body(sys.stdin.read())
    path = Path(body_file)
    if not path.exists():
        print(f"error: body file not found: {body_file}", file=sys.stderr)
        sys.exit(1)
    return _clean_body(path.read_text())


def cmd_create(args):
    """create --title T --body-file F [--epic E] [--layer L] [--context C] [--type feature|chore]

    Allocate the next STORY id and create its GitHub issue as `status:draft`,
    with the composed spec content as the body. The issue IS the story — no file
    is written. Prints the allocated id and the issue URL.
    """
    vals = _parse_flags(args, {
        "title": True, "body-file": True,
        "epic": False, "layer": False, "context": False, "type": False,
    })
    if not _gh_available():
        print("error: gh CLI required to create a story issue", file=sys.stderr)
        sys.exit(1)

    epic = vals["epic"] or "—"
    layer = vals["layer"] or "—"
    context = vals["context"] or "—"
    story_type = (vals["type"] or "feature").strip().lower()

    # Allocate the id (max over issues + legacy files, +1).
    ids = _github_story_ids() | _legacy_story_ids()
    story_id = f"STORY-{(max(ids) + 1 if ids else 1):03d}"

    _validate_metadata(story_id, context, layer, story_type)
    body = _read_body(vals["body-file"])
    if not body.strip():
        print(f"error: {story_id}: refusing to create an issue with an empty body",
              file=sys.stderr)
        sys.exit(1)

    labels = _labels_for(epic, context, layer, story_type, "draft")
    for label in labels:
        _ensure_label(label)
    milestone = _epic_milestone_title(epic)
    _ensure_milestone(milestone)

    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as tmp:
        tmp.write(body)
        body_path = tmp.name
    try:
        cmd = ["issue", "create", "--title", f"{story_id}: {vals['title']}",
               "--body-file", body_path, "--label", ",".join(labels)]
        if milestone:
            cmd += ["--milestone", milestone]
        result = _gh(*cmd, check=False)
    finally:
        os.unlink(body_path)

    if result.returncode == 0:
        print(f"created {story_id}: {result.stdout.strip()}")
    else:
        print(f"error: failed to create issue for {story_id}: {result.stderr.strip()}",
              file=sys.stderr)
        sys.exit(1)


def cmd_update_body(args):
    """update-body <id> --body-file F — replace the issue body (a refinement).

    This is the edit path that keeps content current: because the issue IS the
    source of truth, refining a story means editing its body here.
    """
    if not args or args[0].startswith("-"):
        print("error: update-body requires: <id> --body-file F", file=sys.stderr)
        sys.exit(1)
    story_id, rest = args[0], args[1:]
    vals = _parse_flags(rest, {"body-file": True})
    if not _gh_available():
        print("error: gh CLI required to update a story issue", file=sys.stderr)
        sys.exit(1)
    number = _find_issue(story_id)
    if number is None:
        print(f"error: no issue found for {story_id}", file=sys.stderr)
        sys.exit(1)
    body = _read_body(vals["body-file"])
    if not body.strip():
        print(f"error: {story_id}: refusing to set an empty body", file=sys.stderr)
        sys.exit(1)
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as tmp:
        tmp.write(body)
        body_path = tmp.name
    try:
        result = _gh("issue", "edit", str(number), "--body-file", body_path, check=False)
    finally:
        os.unlink(body_path)
    if result.returncode == 0:
        print(f"updated body of issue #{number} for {story_id}")
    else:
        print(f"error: failed to update issue #{number}: {result.stderr.strip()}",
              file=sys.stderr)
        sys.exit(1)


def cmd_gh_status(args):
    """gh-status <id> <status> — set the status label and open/closed state."""
    if len(args) != 2:
        print("error: gh-status requires 2 arguments: <id> <new-status>", file=sys.stderr)
        sys.exit(1)
    story_id, new_status = args
    if not _gh_available():
        return
    number = _find_issue(story_id)
    if number is None:
        print(f"note: no issue found for {story_id}; nothing to sync")
        return
    new_label = f"status:{new_status}"
    _ensure_label(new_label)
    # Add the new label first, then remove stale ones in a SEPARATE call:
    # `gh issue edit` silently drops a --remove-label when combined with
    # --add-label in the same invocation. Only remove labels actually present.
    _gh("issue", "edit", str(number), f"--add-label={new_label}", check=False)
    view = _gh("issue", "view", str(number), "--json", "labels",
               "--jq", "[.labels[].name]", check=False)
    current = set(json.loads(view.stdout or "[]")) if view.returncode == 0 else set()
    stale = [l for l in ALL_STATUS_LABELS if l != new_label and l in current]
    if stale:
        _gh("issue", "edit", str(number),
            *[f"--remove-label={l}" for l in stale], check=False)
    if new_status in CLOSED_STATUSES:
        _gh("issue", "close", str(number), "--reason",
            "not planned" if new_status != "done" else "completed", check=False)
    else:
        _gh("issue", "reopen", str(number), check=False)
    print(f"synced issue #{number} for {story_id} -> {new_status}")


def cmd_resolve(args):
    """resolve <id> — print the story's issue as JSON {number,title,body,labels}.

    One source of truth for "STORY-NNN -> issue", replacing the hand-rolled
    `gh issue list --search ... | jq startswith | head -1` pipeline that was
    duplicated across skills and agents.
    """
    if len(args) != 1:
        print("error: resolve requires 1 argument: <id>", file=sys.stderr)
        sys.exit(1)
    story_id = args[0]
    if not _gh_available():
        sys.exit(1)
    number = _find_issue(story_id)
    if number is None:
        print(f"error: no issue found for {story_id}", file=sys.stderr)
        sys.exit(1)
    result = _gh("issue", "view", str(number), "--json",
                 "number,title,body,labels", check=False)
    if result.returncode != 0:
        print(f"error: could not read issue #{number} for {story_id}", file=sys.stderr)
        sys.exit(1)
    sys.stdout.write(result.stdout)


def cmd_epic(args):
    """epic <EPIC-NNN> — print the epic milestone's description (empty if absent)."""
    if len(args) != 1:
        print("error: epic requires 1 argument: <EPIC-NNN>", file=sys.stderr)
        sys.exit(1)
    epic = args[0]
    if not _gh_available():
        sys.exit(1)
    result = _gh("api", "repos/{owner}/{repo}/milestones?state=all&per_page=100",
                 "--jq", f'.[] | select(.title | startswith("{epic}")) | .description',
                 check=False)
    if result.returncode != 0:
        print(f"error: could not query milestones for {epic}", file=sys.stderr)
        sys.exit(1)
    sys.stdout.write(result.stdout or "")


COMMANDS = {
    "next-id": cmd_next_id,
    "create": cmd_create,
    "update-body": cmd_update_body,
    "gh-status": cmd_gh_status,
    "resolve": cmd_resolve,
    "epic": cmd_epic,
}

USAGE = """\
Usage: story-index.py <command> [args]

GitHub issues are the single source of truth for story state AND spec content
(ADR-0021). This helper allocates IDs and creates / edits the issues.

Commands:
  next-id
      Print the next available STORY-NNN ID (max over GitHub issues and the
      legacy specs/done, specs/cancelled archives, +1).

  create --title T --body-file F [--epic E] [--layer L] [--context C] [--type feature|chore]
      Allocate the next id and create the story's GitHub issue as draft, using
      the file's contents (or - for stdin) as the spec-content body. Validates
      context/layer/type and applies epic/context/layer/type labels plus the
      epic milestone. Prints the allocated STORY-NNN and issue URL. Needs gh.

  update-body <id> --body-file F
      Replace the issue body with new spec content (the refinement path). Needs gh.

  gh-status <id> <new-status>
      Set the issue's status label and open/closed state.
      No-op if gh is unavailable or no matching issue exists.

  resolve <id>
      Print the story's GitHub issue as JSON: {number, title, body, labels}.
      One source of truth for "STORY-NNN -> issue"; exits non-zero if not found.

  epic <EPIC-NNN>
      Print the epic milestone's description (empty if the milestone is absent)."""

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(USAGE)
        sys.exit(1)
    COMMANDS[sys.argv[1]](sys.argv[2:])
