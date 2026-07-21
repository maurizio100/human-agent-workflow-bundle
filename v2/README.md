# Claude Workflow Bundle

This directory contains a reusable agent workflow for domain-driven software projects.
It combines skills (user-invocable), subagents (spawned by skills), and helper scripts
into a single portable bundle.

---

## Workflow sequence

```
init-project          → minimal CLAUDE.md, folder structure
domain-storytelling   → glossary, bounded contexts, relationships, seed stories
arc42-authoring       → first-class chapters (03, 04, 05, 06, 08, 09, 10)
init-project (again)  → full CLAUDE.md written from domain + architecture
gherkin-story-authoring → Gherkin authored into GitHub issues
plan-story            → plan + test plan, draft PR
implement-story       → tests (red), implementation (green), self-review
merge-story-pr        → squash merge, status flip, cleanup
```

`init-project` runs twice: once at the start to create a skeleton, once after
`domain-storytelling` and `arc42-authoring` to write the real content.

---

## Required folder conventions

The skills and scripts assume this structure. Create it once at project start.

```
.claude/
  agents/       — subagent definitions (this bundle)
  skills/       — skill definitions (this bundle)

docs/
  arc42/        — architecture documentation (arc42 chapters)
  adr/          — architecture decision records
  domain/
    contexts/   — one .md per bounded context; tactical model lives here
    glossary.md — ubiquitous language; single source of truth for terms
    relationships.md — cross-context dependencies and integration patterns

specs/
  done/, cancelled/ — legacy archives of pre-migration story files (not written to)
```

Epics are **GitHub milestones** titled `EPIC-NNN: <name>` (description = goal/stories/scope).

Stories live entirely in **GitHub issues** — one issue per story (`STORY-NNN: <title>`).
The issue is the single source of truth for both state (status/epic/context/layer/type
as labels) and spec content (the Gherkin / chore body), per ADR-0021. There is no
`specs/stories/` directory and no in-repo story index.

`docs/plans/` is created by `plan-story` when the first story is planned.

---

## What CLAUDE.md must contain

`CLAUDE.md` is read by every skill. A minimal first-pass version is enough to
start; the full version is written after `domain-storytelling` and `arc42-authoring`.

**Minimal (first pass — enough to begin):**
- Project name and one-line description
- How to run tests (`cd backend && ./gradlew test`, `npm test`, etc.)
- Story/Epic/ADR ID conventions
- Branch and commit message conventions

**Full (second pass — after domain and architecture sessions):**
- Tech stack (backend, frontend, deployment)
- Where things live (all folders above)
- Foreign systems (brief; detail lives in `docs/arc42/03-context.md`)
- Layer-specific conventions: frontend patterns file, backend test patterns file
- Any project-specific rules the agent must follow

---

## Skills

| Skill | What it does |
|---|---|
| `init-project` | Run 1: scaffolds folder structure + minimal CLAUDE.md. Run 2: discusses implementation conventions (packages, tests, DB, API, errors, events) and writes full CLAUDE.md + pattern files |
| `domain-storytelling` | Analyzes Egon .dst exports → glossary, context candidates, relationships, seed stories |
| `arc42-authoring` | Designs and maintains arc42 chapters collaboratively |
| `adr-writing` | Writes Architecture Decision Records in `docs/adr/` |
| `gherkin-story-authoring` | Authors and refines story Gherkin as GitHub issues |
| `backlog-grooming` | Reviews project state, suggests next stories, hands off to gherkin-story-authoring |
| `plan-story` | Reads docs, produces Plan + Test Plan, creates branch and draft PR |
| `implement-story` | Writes failing tests, implements, runs suite, self-reviews, marks PR ready |
| `merge-story-pr` | Flips story issue to done, squash-merges PR, cleans up branches |

---

## Subagents

| Agent | Color | Used by | What it reads |
|---|---|---|---|
| `story-researcher` | purple | `plan-story` | story issue (via gh), epic, domain context, building blocks, test strategy, ADRs |
| `adr-researcher` | orange | `adr-writing` | existing ADRs, relevant arc42 chapters; runs next-ID script |
| `project-state-reader` | green | `backlog-grooming` | live issue backlog, epics, all domain contexts, relationships, building blocks |
| `domain-reader` | cyan | `gherkin-story-authoring` | glossary, context file(s), relationships |

---

## Helper scripts

Each skill owns its scripts in its own directory under `.claude/skills/<skill>/`.
Scripts are called with `python3` from the repo root.

| Script | Owned by | What it does |
|---|---|---|
| `gherkin-story-authoring/story-index.py` | gherkin-story-authoring | `next-id`; `create`/`update-body` (issue = spec content); `gh-status` — manage the story's GitHub issue |
| `plan-story/push-draft.py` | plan-story | pushes branch, opens draft PR with plan as body |
| `implement-story/pr-ready.py` | implement-story | marks PR ready for review |
| `merge-story-pr/merge-pr.py` | merge-story-pr | squash-merges PR, deletes branch, resets local main |
| `adr-writing/next-adr-id.sh` | adr-writing | returns next sequential 4-digit ADR ID |
