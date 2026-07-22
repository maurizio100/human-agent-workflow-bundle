# GitHub adapter

Implements the `work-tracking` contract (see `../../SKILL.md`) on top of GitHub via the
`gh` CLI. This is the adapter selected when `adapter.conf` contains `github` (the default).

## How the contract maps to GitHub

| Contract concept | GitHub |
|---|---|
| Story (work item) | Issue titled `STORY-NNN: <title>`; body = spec content (Gherkin / chore) |
| Status | `status:<...>` label + open/closed state |
| Classification (epic / context / layer / type) | `epic:` / `context:` / `layer:` / `type:` labels |
| Epic (grouping) | Milestone titled `EPIC-NNN: <name>`; description = goal / stories / scope |
| Change request | Pull request (draft while in progress, squash on merge) |
| Story `ref` | Issue number |

The issue is the single source of truth for both story state and spec content. There are no
authored story files; `specs/done/` and `specs/cancelled/` remain only as legacy archives that
`next-id` still scans so ids are never reused.

## Files

- `tracker.py` — `next-id`, `create`, `update-body`, `set-status`, `resolve`, `list`, `epic`,
  `create-epic`, `comment`
- `review.py` — `open-draft`, `mark-ready`, `checks`, `merge`

## Requirements

`gh` installed and authenticated (`gh auth status`), with Issues enabled on the repo. State-only
operations (`set-status`, `comment`) degrade to a no-op with a note when `gh` is unavailable;
content operations (`create`, `update-body`, `resolve`, `list`, `open-draft`, `merge`) require it.

## Writing another adapter

Copy this directory to `adapters/<name>/`, reimplement `tracker.py` and `review.py` against the
same CLI (same commands, same stdout shapes — `resolve` prints `{ref,title,body,labels}`, `list`
prints `[{ref,title,state,labels,epic}]`), then set `adapter.conf` to `<name>`. No skill or agent
changes are required.
