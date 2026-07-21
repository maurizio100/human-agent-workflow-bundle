---
name: implement-story
description: Implement a planned story — reads the plan from docs/plans/STORY-NNN.md on the current branch, writes failing tests, implements, runs the full test suite, self-reviews, and marks the PR ready for review. Assumes plan-story has already run and the plan file exists. Use this when picking up implementation after a plan has been approved, or when resuming a story that was already planned.
model: sonnet
allowed-tools: Edit Write mcp__ide__getDiagnostics
---

# Implement Story

## What this skill does

Covers Steps 4–7 of the TDD loop: write failing tests, implement (green), run full test
suite, self-review, automated code review (draft-until-clean), mark PR ready. Ends at the
Review gate.

**Runs autonomously through Steps 4–7.** Unexpected findings (broken pre-existing tests,
unplanned building blocks touched, divergence from the plan) are noted on the PR and raised
at Review — not used as a reason to pause and ask.

## What this skill does NOT do

- It does not produce the plan. Run `plan-story` first if no plan exists.
- It does not merge the PR. Merge is a human action.
- It does not modify Gherkin stories.

## Before starting — find the plan

1. Identify the current story branch (e.g. `STORY-NNN-<slug>` from `git branch --show-current`).
2. Extract the story ID from the branch name.
3. Read `docs/plans/STORY-NNN.md`. If the file does not exist, stop and tell the user to
   run `plan-story` first.
4. Read the story's Gherkin from its **GitHub issue** — the source of truth for spec content (ADR-0021):
   `python3 .claude/skills/gherkin-story-authoring/story-index.py resolve STORY-NNN` — returns `{number, title, body, labels}` as JSON.
   The `layer:` label gives the layer. (Fall back to `specs/done/`/`specs/cancelled/` for legacy pre-migration stories.)
5. Read `docs/arc42/08-crosscutting.md` — required to know how tests are structured.
6. For each file listed in the plan's "Affected files" section, read it for exact signatures
   and field names the plan does not already provide. Skip files that the plan fully describes.

Do not re-read the full docs suite — the plan already captures the relevant domain context.
Only open additional files when the plan's level of detail is insufficient.

## Step 4 — Write Tests (red)

Translate every Gherkin scenario from the issue body into an executable test, following
the structure from `docs/arc42/08-crosscutting.md`. The executable `.feature` copy lives in
the test tree (`backend/src/test/resources/features/` for backend); transcribe the scenarios
there — that is what Cucumber runs.

- Read the story's `layer:` label (`frontend`, `backend`, or `fullstack`)
  and use the corresponding test approach and framework defined in `08-crosscutting.md`.
- Acceptance tests: one test per scenario, using the layer-appropriate framework.
- Unit tests: any additional tests called out in the plan's Test Plan section.

**Tests must fail when first written.** If a test passes immediately, either the behavior
already exists or the test isn't testing new behavior — stop and investigate.

Commit: `test: add failing tests for STORY-NNN`

After committing, call `getDiagnostics` (errors only). Fix any compilation or type errors
before proceeding — a test that doesn't compile isn't meaningfully red.

## Step 5 — Execute (green)

Implement the minimum code needed to make the tests pass.

- Stay within the building blocks named in the plan. If a block not in the plan must be
  touched, note it in the PR body and continue.
- Use the ubiquitous language from `docs/domain/glossary.md` for all names.
- Do not write code that isn't covered by a test.

**Update the tactical model in the context file in the same commit as the code.** When a
commit adds an aggregate, entity, value object, or domain service, the same commit also
updates `docs/domain/contexts/<context-name>.md`.

Each new entry shape:
```markdown
- **Name** — description. *Introduced by STORY-NNN.*
```

When modifying an existing entry, append: `*Modified by STORY-NNN.*`
When deprecating, append: `*Deprecated by STORY-NNN.* Reason: ...`

Commit in small chunks with `feat:` or `fix:` messages referencing the story.

## Step 6 — Run Tests

Before running the full suite, call `getDiagnostics` (errors only). If any errors are
reported, fix them first — this avoids reading verbose test output for what is just a
compilation failure.

Run the full test suite using the command(s) from the "How to run things" section of
`CLAUDE.md`. If anything is red:

- **New tests still red**: keep working in Execute. Loop back to Step 5.
- **Pre-existing tests red**: fix if root cause is clear. If unclear, note it on the PR and
  continue — the human catches it at Review.

When everything is green, proceed.

## Step 7 — Self-review and mark PR ready

1. Read the diff end to end. Check for: dead code, debug prints, uncontextualised TODOs,
   accidentally committed files, secrets, magic numbers.
2. Run any linters or formatters configured in the repo.
3. **Verify tactical model alignment.** For each entry in the plan's "Tactical model changes"
   section:
   - The corresponding code exists and matches the description.
   - The corresponding entry exists in `docs/domain/contexts/<context-name>.md`.
   - The context file entry describes what was actually built (not what the plan predicted).
   If plan and reality diverged, update the context file and note the divergence in the PR body.

Update the PR body with a **Tactical model changes (as built)** section:

```markdown
## Tactical model changes (as built)

Context: `docs/domain/contexts/<context-name>.md`

- <Added / modified / deprecated elements>

See diff: docs/domain/contexts/<context-name>.md
```

Do **not** mark the PR ready yet — the automated review in Step 7.5 gates that, and the PR
stays in draft until review is clean.

## Step 7.5 — Automated code review (draft-until-clean)

Keep the PR in **draft** through this step. An independent `code-reviewer` agent reviews the
pushed PR before it ever reaches the human.

**When to run:** Always — every PR gets an automated review before it reaches the human,
regardless of layer or risk. Apply an extra **security lens** when the change touches
authentication, authorization, or security configuration (the story's `context:` / `layer:` /
`epic:` labels or the diff itself mark it as such).

**The loop (max 2 rounds):**
1. Spawn the `code-reviewer` agent (Agent tool) with the PR number and the story ID. It posts its
   findings to the PR and returns a verdict.
2. **HAND BACK** (blocking findings): address every blocking finding as the implementor — loop
   back to Step 5 for code or Step 4 for missing tests — then commit, push, and re-run the
   reviewer. Should-fix / nits do not require a round; apply them at your discretion.
3. **READY** (no blocking findings): proceed to Step 7.6.
4. **Still blocking after 2 rounds**: stop. Summarize the unresolved findings for the human and
   hand off. Do not loop further and do not mark the PR ready — the human decides.

## Step 7.6 — Mark PR ready

Once review is clean, run
`cd "$(git rev-parse --show-toplevel)" && python3 .claude/skills/implement-story/pr-ready.py STORY-NNN`
to flip the PR from draft to ready for review, then continue to Step 8.

## Step 8 — Review gate (human)

Prompt the human through the learnings checklist before they approve:

```
1. Did this PR reveal anything about the domain not in the glossary or context files?
2. Did any implementation decision warrant an ADR?
3. Did anything contradict an existing arc42 chapter or ADR?
4. Did the plan's tactical model match what got built? If not, is the divergence sound?
```

For each "yes", trigger the relevant skill on the same branch, committed into the same PR:
- Glossary / context update → `domain-storytelling` (targeted edit mode)
- New ADR → `adr-writing`
- Contradiction with an arc42 chapter → `arc42-authoring` (targeted edit mode)

Possible outcomes after review:
- **Approved** → human merges via `merge-story-pr`.
- **Changes requested** → loop back to Step 5. Push, request re-review.
- **Spec drift** → update `docs/domain/` or `docs/arc42/` on the branch, include in PR.
