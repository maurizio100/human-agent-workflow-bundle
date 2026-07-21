---
name: merge-story-pr
description: Closes out an approved story — confirms CI, squash-merges the PR, closes the GitHub issue, cleans up branches.
model: haiku
allowed-tools: Read Edit Bash
---

# Merge Story PR

## What this skill does

Closes out a story that has been approved at the Review gate:

1. Confirms CI is green before merging (pauses for a fresh approval if CI is still running)
2. Squash-merges the PR via `gh`
3. Deletes the remote branch (included in the merge command)
4. Resets local `main` to `origin/main`
5. Closes the story's GitHub issue as `done` (via `story-index.py gh-status ... done`)

This is the **Merge gate** action. It is only triggered after the human has explicitly approved the PR ("looks good", "merge it", "ship it", etc.). The agent does not self-approve.

The GitHub issue is the story — both its state and its spec content (ADR-0021). There is no `# Status:` header, no `specs/STORIES.md` index, no `specs/done/` move, and no story file. Closing the issue as `status:done` is what records that the story is complete.

## What this skill does NOT do

- It does not review the PR. Review is a separate human gate.
- It does not pick which PR to merge. The human names the story or PR.
- It does not edit the story's spec content. That content lives in the issue body; this skill only flips state.

## Arguments

The skill expects the story ID (e.g. `STORY-003`) or PR number. Derive the missing one from the other if needed via `gh pr list` or the PR/branch name.

## Steps

### 1. Identify branch and PR

```bash
# Find open PR for the story branch
gh pr list --head STORY-NNN-<slug> --json number,headRefName
```

If a PR number was given directly, look up the branch name:

```bash
gh pr view <number> --json headRefName,state
```

Verify `state` is `OPEN` (or `MERGED` if this is a retry — handle gracefully).

### 2. Check CI status before merging

```bash
gh pr checks <number>
```

- **All checks pass**: proceed to step 3.
- **Any check is `pending` / `in_progress` / `queued`**: stop here. Report the current CI status to the user and wait for an explicit fresh approval before merging. Do **not** schedule a wakeup, do **not** poll until green, and do **not** auto-merge once CI completes. The earlier "merge it" approval does not authorize a merge that crosses a long-running CI gate.
- **Any check has failed**: stop. Report the failure to the user and wait for direction.

### 3. Squash-merge, delete branch, and reset local main

Run `cd "$(git rev-parse --show-toplevel)" && python3 .claude/skills/merge-story-pr/merge-pr.py STORY-NNN`. This squash-merges the PR, deletes the remote branch, checks out `main`, and resets it to `origin/main`. Prints a confirmation line.

### 4. Close the GitHub issue

Run `cd "$(git rev-parse --show-toplevel)" && python3 .claude/skills/gherkin-story-authoring/story-index.py gh-status STORY-NNN done`. This sets the issue's `status:done` label and closes it as completed. It is a no-op when `gh` is unavailable or no matching issue exists.

## Error handling

- **Branch already deleted**: the `--delete-branch` flag is idempotent — `gh` will not error if the branch is already gone.
- **PR already merged**: check `state` in step 1. If already `MERGED`, skip to step 3 (reset local main) and still run step 4 to ensure the issue is closed.
- **Rebase conflict on pull**: do not attempt to resolve — use `git reset --hard origin/main` instead. The squash merge contains all story commits; local divergence is expected and harmless.
- **Issue already closed**: `gh-status ... done` is safe to re-run; it just re-applies the label and closed state.
