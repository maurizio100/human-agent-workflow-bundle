---
name: plan-story
model: opus
description: Plan a user story — read all relevant docs, produce the Plan + Test Plan artifact, write it to docs/plans/STORY-NNN.md and the change-request body, create the story branch. Ends at the Plan human gate; does not touch any production code. Use this when the user wants to plan a story before implementing it, or when plan-story and implement-story are being run as separate steps.
---

# Plan Story

## What this skill does

Covers Steps 0–3 of the TDD loop: story selection, full reading pass, Plan + Test Plan
production, story refinement (if needed), branch creation, and draft change-request opening.

**Ends at the Plan gate.** The agent posts the plan, writes it to `docs/plans/STORY-NNN.md`,
and waits for human approval. It does not write any tests or production code.

The output of this skill is the input to `implement-story`.

All tracker / change-request operations go through the `work-tracking` façade
(`python3 .claude/skills/work-tracking/tracker.py` and `.../review.py`); never call a forge CLI
directly.

## What this skill does NOT do

- It does not write tests or implementation code.
- It does not modify Gherkin stories. If the story needs refinement, it stops and hands
  back to `gherkin-story-authoring`.
- It does not merge change requests.

## Step 0 — Story selection (only if no story was specified)

If the user invoked the skill without naming a specific story:

1. List the open backlog from the tracker (the source of truth for story state):

   ```bash
   cd "$(git rev-parse --show-toplevel)" && python3 .claude/skills/work-tracking/tracker.py list --state open
   ```

   This returns JSON, one object per story: `{ref, title, state, labels, epic}`. The `status:…`
   value is in `labels`. If the tracker is unavailable, tell the user story selection needs the
   work-tracking backend and stop.
2. Filter to stories whose status is `draft`, `ready`, or `in-progress`.
3. Present a numbered list grouped by status:
   - `ready` — fully eligible, no caveats
   - `draft` — selectable, but labelled _(draft — planner may discover refinement is needed)_
   - `in-progress` — not selectable; show with a note that a branch is already open for it
4. Ask the user to pick one. Wait for the answer before doing anything else.

If no stories are `ready` or `draft`, tell the user and stop.

If the user named a story, skip this step.

## Step 1 — Research

Spawn the `story-researcher` subagent with the story ID. It reads the story spec, epic,
domain context, glossary, relationships, building blocks, test strategy, and relevant ADRs,
and returns a structured summary.

Wait for the summary before proceeding. Use it as the basis for the plan — do not re-read
the same files yourself unless the summary is missing a specific detail you need.

After the summary arrives, read the existing codebase areas the plan's "Affected files" will
touch — for exact signatures and field names not covered by the summary. Limit exploration
to the packages or modules that correspond to the story's bounded context.

## Step 2 — Plan + Test Plan

Produce the plan artifact using the template below. Write it to **`docs/plans/STORY-NNN.md`**
on the story branch (created in Step 3). Also display it in the conversation so the human
can read it without opening the file.

```markdown
## Story
STORY-NNN: <title>
Link: <work-item ref/URL>

## Understanding
<2-4 sentences restating what the story asks for, in the agent's own words.
Proves understanding; mismatches are caught cheaply here.>

## Approach
<3-8 bullets describing the implementation. Names the affected building blocks
from docs/arc42/05-building-blocks.md. References relevant ADRs from docs/adr/.>

## Test Plan
<For each Gherkin scenario: the test name, the test level and framework as defined in
docs/arc42/08-crosscutting.md. Use the story's `layer:` value to determine
which section of the test strategy applies. Also list additional unit tests not tied to
a scenario.>

## Tactical model changes
<Aggregates, entities, value objects, and domain services introduced or modified.
Scoped per bounded context. This is the primary review point for tactical DDD decisions.>

Context: `docs/domain/contexts/<context-name>.md`

New aggregates:
- <Name> — <one-line responsibility>. Invariants: <what it enforces>.

Modified aggregates:
- <Name> — <what changes and why>.

New entities (non-aggregate roots):
- <Name> — belongs to <aggregate>. Identity: <how identified>.

New value objects:
- <Name> — <shape and constraints>.

New domain services:
- <Name> — <what it does>.

<Use "(none this story)" for any subsection where nothing changes.
If this story does not touch any tactical model, say so explicitly.>

## Affected files
<Best-effort list of files to create or modify. Must include
docs/domain/contexts/<name>.md if there are any tactical model changes.>

## Risks and out of scope
<What the agent is deliberately not doing, and what might go wrong.>
```

**This is a human gate.** Post the plan and wait. Do not proceed to implementation.

## Step 3 — Story refinement (feedback edge, only if needed)

If, while writing the plan, the agent discovers:
- The story is ambiguous in a way that materially affects implementation
- The story is too large for one TDD loop iteration
- The story references concepts not in the glossary

Stop. Write what is understood and what is missing into a refinement note. Hand back to
`gherkin-story-authoring`. Do not guess.

## Step 4 — Branch and draft change request

After the human approves the plan:

1. Verify the story's status is `ready` or `draft`. If `in-progress`, stop — a branch already exists.
2. Move the story to in-progress: `cd "$(git rev-parse --show-toplevel)" && python3 .claude/skills/work-tracking/tracker.py set-status STORY-NNN in-progress`. This is a tracker operation — there is no file or index status to edit, and nothing to commit for it.
3. Create branch `STORY-NNN-<slug>` from the default branch.
4. Write the plan to `docs/plans/STORY-NNN.md` and commit: `docs: add plan for STORY-NNN`.
5. Run `cd "$(git rev-parse --show-toplevel)" && python3 .claude/skills/work-tracking/review.py open-draft STORY-NNN` — pushes the branch and opens a draft change request with the plan as body.

After pushing the branch and opening the draft change request, invoke the `implement-story` skill to
continue autonomously — or stop here if the user has asked to plan only.

## When to push back

Stop and ask the human if:
- The story is ambiguous enough that you cannot write the Plan without guessing
- The story requires a building block not in arc42 (architecture work is needed first)
- The story requires touching a foreign system not listed in `03-context.md`
- The Plan grows beyond ~10 affected files (likely too large; split the story)
