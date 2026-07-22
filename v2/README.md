# Claude Workflow Bundle

This directory contains a reusable agent workflow for domain-driven software projects.
It combines skills (user-invocable), subagents (spawned by skills), and helper scripts
into a single portable bundle.

The bundle is **forge-agnostic**: where work is tracked (stories, epics, status) and how
changes are reviewed and merged is a pluggable choice behind the `work-tracking` contract.
GitHub ships as the only concrete adapter today; see [Work tracking](#work-tracking).

---

## Workflow sequence

```
init-project          → minimal PROJECT.md, folder structure
domain-storytelling   → glossary, bounded contexts, relationships, seed stories
arc42-authoring       → first-class chapters (03, 04, 05, 06, 08, 09, 10)
init-project (again)  → full PROJECT.md written from domain + architecture
gherkin-story-authoring → Gherkin authored into tracked work items
plan-story            → plan + test plan, draft change request
implement-story       → tests (red), implementation (green), self-review
merge-story-pr        → squash merge, status flip, cleanup
```

`init-project` runs twice: once at the start to create a skeleton, once after
`domain-storytelling` and `arc42-authoring` to write the real content.

---

## Work tracking

Everything to do with **where stories/epics/status live** and **how change requests are
opened, reviewed, and merged** goes through the `work-tracking` contract — a
forge-agnostic seam that mirrors the `domain-artifacts` ↔ discovery-adapter seam.

- **Skills and agents call only the façade:**
  `python3 .claude/skills/work-tracking/tracker.py <cmd>` (work items & epics) and
  `python3 .claude/skills/work-tracking/review.py <cmd>` (change integration). They never
  call a forge CLI directly.
- **The active backend is one line** in `.claude/skills/work-tracking/adapter.conf`
  (defaults to `github`). The dispatchers forward each command to
  `adapters/<name>/{tracker,review}.py`.
- **Adding a backend** (GitLab, Jira, local files, …) means dropping in
  `adapters/<name>/` implementing the contract CLI and setting `adapter.conf` — **no skill
  or agent changes**. See `skills/work-tracking/SKILL.md` for the operation vocabulary and
  `skills/work-tracking/adapters/github/README.md` for how GitHub maps to it.

Concepts (backend-neutral): a **story** is a work item `STORY-NNN` whose body is its spec
content and whose metadata carries status/epic/context/layer/type; an **epic** is a
grouping `EPIC-NNN`; a **change request** (a PR on GitHub, an MR on GitLab, …) carries a
story branch from draft → ready → merged.

---

## Required folder conventions

The skills and scripts assume this structure. Create it once at project start.

```
.claude/
  agents/       — subagent definitions (this bundle)
  skills/       — skill definitions (this bundle, incl. work-tracking contract + adapters)

docs/
  arc42/        — architecture documentation (arc42 chapters)
  adr/          — architecture decision records
  domain/
    contexts/   — one .md per bounded context; tactical model lives here
    glossary.md — ubiquitous language; single source of truth for terms
    context-map.md — bounded contexts and their relationships

specs/
  done/, cancelled/ — legacy archives of pre-migration story files (not written to;
                      still scanned so story IDs are never reused)
```

Stories and epics live entirely in the **configured work-tracking backend** — one work
item per story (`STORY-NNN: <title>`, body = Gherkin / chore spec, metadata = state), and
one grouping per epic (`EPIC-NNN: <name>`, description = goal/stories/scope). The work item
is the single source of truth for both state and spec content. There is no `specs/stories/`
directory and no in-repo story index.

`docs/plans/` is created by `plan-story` when the first story is planned.

---

## What PROJECT.md must contain

`PROJECT.md` is the central conventions file read by every skill. A minimal first-pass
version is enough to start; the full version is written after `domain-storytelling` and
`arc42-authoring`. (If you also want it auto-loaded into agent context, keep a one-line
`CLAUDE.md` that points at `PROJECT.md`.)

**Minimal (first pass — enough to begin):**
- Project name and one-line description
- How to run tests (`cd backend && ./gradlew test`, `npm test`, etc.)
- Story/Epic/ADR ID conventions
- Branch and commit message conventions
- Work-tracking backend (from `adapter.conf`)

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
| `init-project` | Run 1: scaffolds folder structure + minimal PROJECT.md. Run 2: discusses implementation conventions (packages, tests, DB, API, errors, events) and writes full PROJECT.md + pattern files |
| `domain-storytelling` | Analyzes Egon .dst exports → glossary, context candidates, relationships, seed stories |
| `arc42-authoring` | Designs and maintains arc42 chapters collaboratively |
| `adr-writing` | Writes Architecture Decision Records in `docs/adr/` |
| `gherkin-story-authoring` | Authors and refines story Gherkin as tracked work items |
| `backlog-grooming` | Reviews project state, suggests next stories, hands off to gherkin-story-authoring |
| `plan-story` | Reads docs, produces Plan + Test Plan, creates branch and draft change request |
| `implement-story` | Writes failing tests, implements, runs suite, self-reviews, marks change request ready |
| `merge-story-pr` | Flips story to done, squash-merges change request, cleans up branches |
| `work-tracking` | **Contract** (not user-invoked): defines the forge-agnostic tracker/change-request operations and the façade skills call |
| `domain-artifacts` | **Contract** (not user-invoked): the shared output contract for domain discovery |

---

## Subagents

| Agent | Color | Used by | What it reads |
|---|---|---|---|
| `story-researcher` | purple | `plan-story` | story work item (via façade), epic, domain context, building blocks, test strategy, ADRs |
| `adr-researcher` | orange | `adr-writing` | existing ADRs, relevant arc42 chapters; runs next-ID script |
| `project-state-reader` | green | `backlog-grooming` | live backlog (via façade), epics, all domain contexts, relationships, building blocks |
| `domain-reader` | cyan | `gherkin-story-authoring`, `plan-story` | glossary, context file(s), context map |
| `code-reviewer` | red | `implement-story` | change-request diff (via façade), story intent, project conventions from PROJECT.md |

---

## Helper scripts

The **work-tracking** façade and its adapters own all tracker/change-request scripts;
skills call the façade, never an adapter directly.

| Script | Role | What it does |
|---|---|---|
| `work-tracking/tracker.py` | façade | dispatches tracker commands to the active adapter |
| `work-tracking/review.py` | façade | dispatches change-request commands to the active adapter |
| `work-tracking/adapters/github/tracker.py` | GitHub adapter | `next-id` · `create` · `update-body` · `set-status` · `resolve` · `list` · `epic` · `create-epic` · `comment` (issues/labels/milestones) |
| `work-tracking/adapters/github/review.py` | GitHub adapter | `open-draft` · `mark-ready` · `checks` · `diff` · `post-review` · `merge` (pull requests) |
| `adr-writing/next-adr-id.py` | adr-writing | returns next sequential 4-digit ADR ID (documentation, not forge) |
