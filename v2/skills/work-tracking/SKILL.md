---
name: work-tracking
model: sonnet
description: The forge-agnostic contract for tracking work and integrating changes. Defines the work-item model (stories, epics, status lifecycle), the change-request model (draft → ready → merged), the exact CLI every backend adapter must implement, and how skills call it through a stable façade. This skill is NOT invoked directly by users — it is referenced by the workflow skills (gherkin-story-authoring, plan-story, implement-story, merge-story-pr, …) which call the façade scripts rather than any specific forge. The active backend is a project choice, recorded once in adapter.conf.
allowed-tools: Read Bash
---

# Work Tracking — forge contract

## Purpose

This is the **backend-agnostic contract** for where work lives and how changes are
integrated. However a project tracks its work — GitHub issues + PRs, GitLab issues + MRs,
Jira + a git host, or plain in-repo files — the workflow skills interact with it through the
**same operations, the same vocabulary, and the same façade**. This skill owns that contract.

It mirrors the domain seam: just as `domain-artifacts` is the method-agnostic *output*
contract that discovery adapters (e.g. `domain-storytelling`) write to, `work-tracking` is the
forge-agnostic *tracking* contract that a **backend adapter** (e.g. `adapters/github/`)
implements. Keep the seam clean:

- **The workflow skills decide** *what* to do — allocate an id, create a story, move a status,
  open a change request for review, merge it. They never name a specific forge.
- **This contract decides** the operation vocabulary, the work-item / change-request model,
  the status lifecycle, and the façade skills call.
- **An adapter decides** *how* those operations map to a concrete backend.

## Choosing the backend

The active backend is named in **`adapter.conf`** (a single line, e.g. `github`), sibling to
this file. The dispatcher scripts read it; if the file is absent they default to `github`.
Change the backend for the whole project by editing that one line (and providing a matching
`adapters/<name>/` directory). No skill or agent changes are needed — that is the point of the
façade.

Only the **GitHub** adapter ships today. To add another (GitLab, Jira, local files, …), create
`adapters/<name>/tracker.py` and `adapters/<name>/review.py` implementing the CLI below, then set
`adapter.conf` to `<name>`.

## The façade (what skills call)

Skills and agents call **only** these two stable paths — never a forge CLI directly:

```
python3 .claude/skills/work-tracking/tracker.py <command> [args]   # work items & epics
python3 .claude/skills/work-tracking/review.py  <command> [args]   # change integration
```

Each is a thin dispatcher: it resolves the active adapter from `adapter.conf` and forwards the
command to `adapters/<active>/{tracker,review}.py`. Always invoke from the repo root
(`cd "$(git rev-parse --show-toplevel)"`); the adapters re-anchor to the repo root themselves.

## The work-item model

- A **story** is one tracked work item, identified `STORY-NNN` (zero-padded to 3 digits). Ids
  are sequential and never reused. Its **body is the spec content** (Gherkin for a feature, a
  what/why for a chore); its **classification** (epic, layer, context, type) and **status** are
  metadata, not part of the body. **The work item is the single source of truth for both the
  story's state and its spec content** — there is no separate `.feature` file, no `# Status:`
  header, and no in-repo story index.
- An **epic** is a grouping of stories, identified `EPIC-NNN`, carrying a goal / stories /
  out-of-scope description.
- **Layer** ∈ {`frontend`, `backend`, `fullstack`, `infra`}; **type** ∈ {`feature`, `chore`};
  **context** is a bounded-context name (validated against `docs/domain/contexts/*.md`) or `—`.

### Status lifecycle

```
(created) → draft → ready → in-progress → done
                ▲        │         │
                └────────┴─── (planner hands back) ──┘
any → superseded   (story split into smaller stories)
```

Each transition is owned by exactly one skill; no skill flips a status it does not own (see the
individual skills). The status is metadata on the work item — moving it is a tracker operation,
never a repo commit.

## The change-request model

A **change request** (a pull request on GitHub, a merge request on GitLab, etc.) carries a
story's branch through review to merge:

```
open as draft → (implementation + automated review) → mark ready → (human approval) → merge
```

The branch is `STORY-NNN-<slug>`; the change request's body is the plan; merge is a squash that
deletes the branch and resets local `main`. "Merge" is a human-approved action.

## Operation vocabulary (the CLI every adapter implements)

### `tracker.py` — work items & epics

| Command | Effect | Output |
|---|---|---|
| `next-id` | Next available `STORY-NNN` (max over all known ids + 1; never reuses) | `STORY-NNN` |
| `create --title T --body-file F [--epic E] [--layer L] [--context C] [--type feature\|chore]` | Allocate the next id and create the story as `status:draft` with `F` (or `-` for stdin) as its spec body; validate + apply classification metadata; attach the epic grouping | allocated `STORY-NNN` + ref/URL |
| `update-body <id> --body-file F` | Replace the story's spec content (the refinement path) | confirmation |
| `set-status <id> <status>` | Move the status metadata and open/closed state; no-op if the backend is unavailable | confirmation |
| `resolve <id>` | The story as JSON `{ref, title, body, labels}` — the one "id → work item" lookup | JSON |
| `list [--state open\|all]` | Backlog listing as JSON, one object per story: `{ref, title, state, labels, epic}` (metadata only; no bodies) | JSON array |
| `epic <EPIC-NNN>` | The epic grouping's description (empty if absent) | text |
| `create-epic --title T --body-file F` | Create an epic grouping titled `EPIC-NNN: <name>` with `F` as its description | confirmation |
| `comment <id> --body B` | Append a note to the story (e.g. a glossary flag or a split trail) | confirmation |

### `review.py` — change integration

| Command | Effect | Output |
|---|---|---|
| `open-draft <id>` | Push the current story branch and open a **draft** change request with `docs/plans/STORY-NNN.md` as its body | change-request ref/URL |
| `mark-ready <id>` | Flip the story's change request from draft to ready for review (refuses if tracked changes are uncommitted) | confirmation |
| `checks <id>` | The CI status of the story's change request | status lines |
| `diff <id>` | The change request's full diff (the scope a reviewer reads) | unified diff |
| `post-review <id> --body-file F` | Post a summary review comment on the change request (never an approve/block — the merge decision is the human's) | confirmation |
| `merge <id>` | Squash-merge the change request, delete the branch, check out `main`, reset it to `origin/main` | confirmation |

> Per-line **inline** review comments are an optional, backend-specific capability. A reviewer
> should always post its findings via `post-review` (which every adapter supports) and treat inline
> comments as best-effort — falling back to `path:line` references inside the summary when the
> active adapter can't place them.

## Graceful degradation

Read-only or state-only operations (`set-status`, `comment`) must **degrade gracefully** when
the backend is unavailable (print a note, exit 0) so a status flip never blocks the workflow.
Content operations (`create`, `update-body`, `resolve`, `open-draft`, `merge`) **require** the
backend and should exit non-zero with a clear message when it is missing — there is nowhere else
to put the content.

## Invariants (hold regardless of backend)

- **The work item is the single source of truth** for a story's state *and* spec content.
- **Ids are sequential and never reused** — always allocate via `next-id` / `create`, never by hand.
- **Classification is metadata, not body text.** Epic/layer/context/type/status live as the
  backend's metadata (labels, fields, front-matter), never as header lines in the spec body.
- **Skills call the façade, never a forge CLI.** Any raw forge command in a skill is a leak.
- **The backend is a project choice**, recorded once in `adapter.conf`.
