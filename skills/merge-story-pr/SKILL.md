---
name: merge-story-pr
description: Closes out an approved story — flips status, moves feature file, squash-merges PR, cleans up branches.
model: haiku
allowed-tools: Read Edit Bash
---

# Merge Story PR

## What this skill does

Closes out a story that has been approved at the Review gate:

1. Flips the story's `# Status:` from `in-progress` to `done` on the story branch
2. Moves the story file (`.feature` or `.md`) into the appropriate context directory under `specs/done/`
3. Updates the story's status to `done` in `specs/STORIES.md`
4. Commits and pushes those changes
5. Confirms CI is green before merging (pauses for a fresh approval if CI is still running)
6. Squash-merges the PR via `gh`
7. Deletes the remote branch (included in the merge command)
8. Resets local `main` to `origin/main`

This is the **Merge gate** action. It is only triggered after the human has explicitly approved the PR ("looks good", "merge it", "ship it", etc.). The agent does not self-approve.

## What this skill does NOT do

- It does not review the PR. Review is a separate human gate.
- It does not pick which PR to merge. The human names the story or PR.
- It does not push to any branch other than the story branch before merging.

## Arguments

The skill expects the story ID (e.g. `STORY-003`) or PR number. Derive the missing one from the other if needed via `gh pr list` or the feature file name.

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

### 2. Switch to the story branch

```bash
git checkout STORY-NNN-<slug>
git pull  # ensure local is up to date with remote
```

### 3. Flip story status, move file, update DONE list

**a) Find the story file**

Look for the story file in `specs/stories/` — it will be either `STORY-NNN-*.feature` (feature story) or `STORY-NNN-*.md` (chore story). Both use the same `# Status:` and `# Context:` header format.

**b) Flip status to `done`**

Edit the story file:
- Change `# Status: in-progress` to `# Status: done`

**c) Move the story file into the appropriate context directory**

Read the `# Context:` line from the story file. Move it into the matching subdirectory under `specs/done/` — pick a sensible directory name that reflects the context (check for an existing sibling directory if one already exists for that context; create one if not). Use `git mv` so the move is tracked:

```bash
git mv specs/stories/STORY-NNN-<slug>.<ext> specs/done/<context-dir>/STORY-NNN-<slug>.<ext>
```

**d) Update story index**

Run `cd "$(git rev-parse --show-toplevel)" && python3 .claude/skills/merge-story-pr/mark-done.py STORY-NNN`.

**e) Commit**

Stage all changes (`specs/stories/`, `specs/done/`, `specs/STORIES.md`) and commit:

```
docs: mark STORY-NNN as done

Refs: STORY-NNN
```

Push:

```bash
git push
```

### 4. Check CI status before merging

Before squash-merging, check the PR's CI status:

```bash
gh pr checks <number>
```

- **All checks pass**: proceed to step 5.
- **Any check is `pending` / `in_progress` / `queued`**: stop here. Report the current CI status to the user and wait for an explicit fresh approval before merging. Do **not** schedule a wakeup, do **not** poll until green, and do **not** auto-merge once CI completes. The earlier "merge it" approval covers preparing and pushing (steps 1–3); it does not authorize a merge that crosses a long-running CI gate.
- **Any check has failed**: stop. Report the failure to the user and wait for direction.

### 5. Squash-merge, delete branch, and reset local main

Run `cd "$(git rev-parse --show-toplevel)" && python3 .claude/skills/merge-story-pr/merge-pr.py STORY-NNN`. This squash-merges the PR, deletes the remote
branch, checks out `main`, and resets it to `origin/main`. Prints a confirmation line.

## Error handling

- **Branch already deleted**: the `--delete-branch` flag is idempotent — `gh` will not error if the branch is already gone.
- **PR already merged**: check `state` in step 1. If already `MERGED`, skip to step 5 (reset local main) and perform steps 3a–3c on `main` directly if not yet done.
- **Rebase conflict on pull**: do not attempt to resolve — use `git reset --hard origin/main` instead. The squash merge contains all story commits; local divergence is expected and harmless.
- **status already `done`**: no-op on the file edit; still move the file and update `specs/STORIES.md` if not yet done.
- **File already moved**: if `specs/stories/STORY-NNN-*` (`.feature` or `.md`) is not found, check `specs/done/` — it may already be there. Skip the `git mv` but still ensure `specs/STORIES.md` shows status `done`.
