---
name: chore-story
description: Create lightweight chore stories for non-behavioral changes — layout tweaks, refactorings, dependency updates, tooling, or documentation. Use this when the change doesn't warrant Gherkin scenarios but still needs traceability. Trigger when the user says "quick fix", "chore", "refactor", "tweak", or describes a change that has no observable behavioral acceptance criteria.
model: sonnet
allowed-tools: Read Edit Write Bash
---

# Chore Story

## What this skill does

Creates a lightweight **work item** (with a Markdown body) for non-behavioral changes that don't warrant Gherkin scenarios. The work item is the single source of truth for the chore's spec content — there is no `.md` file in `specs/stories/`. Chore stories provide traceability (every code change links to a story) without the overhead of writing Given/When/Then for things like CSS tweaks or rename refactorings.

All tracker operations go through the `work-tracking` façade
(`python3 .claude/skills/work-tracking/tracker.py <command>`); never call a forge CLI directly.

## What this skill does NOT do

- It does not create Gherkin stories. If the change has observable behavioral acceptance criteria, use `gherkin-story-authoring` instead.
- It does not run `plan-story`. Chores go straight to implementation.

## When to use chore vs. feature

| Use **chore-story** | Use **gherkin-story-authoring** |
|---|---|
| Layout / styling adjustments | New user-facing behavior |
| Rename / extract / restructure refactorings | Changed business rules |
| Dependency updates | New API endpoints with domain logic |
| CI / tooling / build changes | Cross-context integrations |
| Documentation-only changes | Anything with testable acceptance criteria |
| Tech debt cleanup | |

When in doubt, ask the user.

## Conventions

### IDs and titles

- Each chore is one work item titled `STORY-NNN: <human-readable title>`. IDs are sequential and shared with feature stories — never reuse an ID. Always allocate with `tracker.py create` (it picks the next id for you).
- Classification (`epic`, `layer`, `context`, `type:chore`) is passed as flags and becomes work-item metadata — not header comments in the body.

### Structure of a chore body

The body is Markdown — no classification-header comments (those go to flags/metadata):

```markdown
## <Human-readable title>

### What
Brief description of the change — what files/areas are affected.

### Why
Motivation — what prompted this. A sentence or two is enough.
```

### Status lifecycle

Status lives on the work item (the `status:` value + open/closed state), not in a file. Chores follow a simplified lifecycle — no plan phase:

```
draft → ready → in-progress → done
```

- `draft`: work item created by this skill
- `ready`: human approves (same gate as feature stories)
- `in-progress`: branch created, work starts
- `done`: change request merged (work item closed)

Every transition is applied with `tracker.py set-status STORY-NNN <status>`; the status lives only on the work item.

### Who flips the status

| Transition | Owned by | When |
|---|---|---|
| *(none)* → `draft` | `chore-story` | On creation |
| `draft` → `ready` | `chore-story` | On explicit human approval |
| `ready` → `in-progress` | human / agent | When implementation starts on the branch |
| `in-progress` → `done` | `merge-story-pr` | After the change request is merged |

## Steps

### 1. Discuss the chore with the user

Understand:
- **What** is changing (files, areas, scope)
- **Why** (what motivates the change)
- **Context** (which bounded context, or cross-cutting)
- **Layer** (frontend, backend, fullstack, infra)
- **Epic** (existing epic or — if standalone)

Keep the discussion brief. Chores are small by definition.

### 2. Create the story

Write the `### What` / `### Why` Markdown body to a scratch file, then create the work item:

```
cd "$(git rev-parse --show-toplevel)" && python3 .claude/skills/work-tracking/tracker.py create \
  --title "<title>" --epic EPIC-NNN --layer <layer> --context "<context or —>" --type chore \
  --body-file <scratch-file>
```

This allocates the next id and creates a work item titled `STORY-NNN: <title>` with the body as content and `epic:`/`context:`/`layer:`/`type:chore` metadata plus `status:draft` (and the epic grouping). It prints the allocated `STORY-NNN` and the work-item ref/URL. The same helper backs feature stories, so chores and features land in one unified backlog — the work item **is** the story record. There is nothing to commit at this step.

### 3. Await approval

Present the story to the user. Only flip to `ready` on explicit human approval (same gate as feature stories). On approval:

```
cd "$(git rev-parse --show-toplevel)" && python3 .claude/skills/work-tracking/tracker.py set-status STORY-NNN ready
```

### 4. Create branch and start

Once `ready`, create the story branch and move the work item to `in-progress`:

```bash
git checkout -b STORY-NNN-kebab-title main
cd "$(git rev-parse --show-toplevel)" && python3 .claude/skills/work-tracking/tracker.py set-status STORY-NNN in-progress
```

Status changes are tracker operations, not commits — there is no file or index edit to make.

The user (or agent) then implements the change directly — no plan-story or implement-story needed.

### 5. Implement

Make the changes described in the story's `### What` section.

**Tests:** Chores don't add new behaviour, but they must not break existing tests. After making changes:
- Remove or update any tests that directly assert the thing being changed (e.g. a deleted nav item, a renamed selector).
- Do not add new test coverage beyond what's needed to keep the suite coherent.
- Run the affected test files locally to check for obvious failures. Pre-existing failures unrelated to this story are acceptable — note them but do not fix them here.

**Commit message:** follow Conventional Commits, referencing the story:
```
chore: <short description>

Refs: STORY-NNN
```
Use `feat:` if the change adds something visible (even if non-behavioral), `refactor:` for pure restructuring, `chore:` for everything else.

### 6. Open a change request and mark ready

Push the branch and open a change request:
- Title: `STORY-NNN: <human-readable title>`
- Body: brief summary of what changed and a short manual test plan.
- Open as **ready for review** (not draft) — chores are small and implementation is complete at this point.

### 7. Await merge approval

Per the `merge-story-pr` skill: surface CI status to the user and wait for explicit approval before merging. Do not self-merge.
