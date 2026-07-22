---
name: merge-story-pr
description: Closes out an approved story — confirms CI, squash-merges the change request, marks the story done, cleans up branches.
model: haiku
allowed-tools: Read Edit Bash
---

# Merge Story

## What this skill does

Closes out a story that has been approved at the Review gate:

1. Confirms CI is green before merging (pauses for a fresh approval if CI is still running)
2. Squash-merges the change request
3. Deletes the remote branch (included in the merge command)
4. Resets local `main` to `origin/main`
5. Marks the story `done` (via `tracker.py set-status ... done`)

This is the **Merge gate** action. It is only triggered after the human has explicitly approved the change request ("looks good", "merge it", "ship it", etc.). The agent does not self-approve.

The work item is the story — both its state and its spec content. There is no `# Status:` header, no `specs/STORIES.md` index, no `specs/done/` move, and no story file. Marking the story `status:done` (which closes the work item) is what records that the story is complete.

All tracker / change-request operations go through the `work-tracking` façade
(`python3 .claude/skills/work-tracking/tracker.py` and `.../review.py`); never call a forge CLI
directly.

## What this skill does NOT do

- It does not review the change request. Review is a separate human gate.
- It does not pick which change request to merge. The human names the story.
- It does not edit the story's spec content. That content lives in the work-item body; this skill only flips state.

## Arguments

The skill expects the story ID (e.g. `STORY-003`). The façade resolves the story's branch and
change request from that ID.

## Steps

### 1. Check CI status before merging

```bash
cd "$(git rev-parse --show-toplevel)" && python3 .claude/skills/work-tracking/review.py checks STORY-NNN
```

- **All checks pass**: proceed to step 2.
- **Any check is `pending` / `in_progress` / `queued`**: stop here. Report the current CI status to the user and wait for an explicit fresh approval before merging. Do **not** schedule a wakeup, do **not** poll until green, and do **not** auto-merge once CI completes. The earlier "merge it" approval does not authorize a merge that crosses a long-running CI gate.
- **Any check has failed**: stop. Report the failure to the user and wait for direction.

### 2. Squash-merge, delete branch, and reset local main

Run `cd "$(git rev-parse --show-toplevel)" && python3 .claude/skills/work-tracking/review.py merge STORY-NNN`. This squash-merges the change request, deletes the remote branch, checks out `main`, and resets it to `origin/main`. Prints a confirmation line.

### 3. Mark the story done

Run `cd "$(git rev-parse --show-toplevel)" && python3 .claude/skills/work-tracking/tracker.py set-status STORY-NNN done`. This sets the story's status to `done` and closes the work item as completed. It is a no-op when the tracker is unavailable or no matching work item exists.

## Error handling

- **Branch already deleted**: the merge command's branch deletion is idempotent — it will not error if the branch is already gone.
- **Change request already merged**: if the merge step reports it is already merged, still run step 3 to ensure the story is marked done, and reset local main.
- **Rebase conflict on pull**: do not attempt to resolve — the merge step uses `git reset --hard origin/main` instead. The squash merge contains all story commits; local divergence is expected and harmless.
- **Story already done**: `set-status ... done` is safe to re-run; it just re-applies the status and closed state.
