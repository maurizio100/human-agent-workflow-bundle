---
name: chore-story
description: Create lightweight chore stories for non-behavioral changes — layout tweaks, refactorings, dependency updates, tooling, or documentation. Use this when the change doesn't warrant Gherkin scenarios but still needs traceability. Trigger when the user says "quick fix", "chore", "refactor", "tweak", or describes a change that has no observable behavioral acceptance criteria.
model: sonnet
allowed-tools: Read Edit Write Bash
---

# Chore Story

## What this skill does

Creates a lightweight `.md` story file in `specs/stories/` for non-behavioral changes that don't warrant Gherkin scenarios. Chore stories provide traceability (every code change links to a story) without the overhead of writing Given/When/Then for things like CSS tweaks or rename refactorings.

## What this skill does NOT do

- It does not create Gherkin `.feature` files. If the change has observable behavioral acceptance criteria, use `gherkin-story-authoring` instead.
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

### File naming and IDs

- File: `specs/stories/STORY-NNN-kebab-case-title.md` (same directory as feature stories, `.md` extension).
- IDs are sequential and shared with feature stories — never reuse an ID. Use `story-index.py next-id` to find the next one.
- The kebab-case title in the filename is a slug; the human-readable title lives in the `## Title` heading.

### Structure of a chore `.md` file

```markdown
# STORY-NNN
# Epic: EPIC-NNN (or —)
# Layer: frontend | backend | fullstack | infra
# Context: <bounded context name, or — if cross-cutting>
# Status: draft
# Type: chore

## <Human-readable title>

### What
Brief description of the change — what files/areas are affected.

### Why
Motivation — what prompted this. A sentence or two is enough.
```

### Status lifecycle

Chores follow a simplified lifecycle — no plan phase:

```
draft → ready → in-progress → done
```

- `draft`: created by this skill
- `ready`: human approves (same gate as feature stories)
- `in-progress`: branch created, work starts
- `done`: PR merged

### Who flips the status

| Transition | Owned by | When |
|---|---|---|
| *(none)* → `draft` | `chore-story` | On creation |
| `draft` → `ready` | `chore-story` | On explicit human approval |
| `ready` → `in-progress` | human / agent | When implementation starts on the branch |
| `in-progress` → `done` | `merge-story-pr` | After the PR is merged |

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

1. Get next ID: `cd "$(git rev-parse --show-toplevel)" && python3 .claude/skills/gherkin-story-authoring/story-index.py next-id`
2. Write the `.md` file to `specs/stories/STORY-NNN-kebab-title.md`
3. Add to index: `cd "$(git rev-parse --show-toplevel)" && python3 .claude/skills/gherkin-story-authoring/story-index.py add STORY-NNN <epic> "<title>" <context> <layer> draft`

### 3. Commit

```
docs: add chore STORY-NNN — <title>

Refs: STORY-NNN
```

### 4. Await approval

Present the story to the user. Only flip to `ready` on explicit human approval (same gate as feature stories). On approval, update status:

```
cd "$(git rev-parse --show-toplevel)" && python3 .claude/skills/gherkin-story-authoring/story-index.py update-status STORY-NNN ready
```

### 5. Create branch and start

Once `ready`, create the story branch and flip to `in-progress`:

```bash
git checkout -b STORY-NNN-kebab-title main
```

Update status to `in-progress` in both the `.md` file and the index. Commit:

```
docs: mark STORY-NNN as in-progress

Refs: STORY-NNN
```

The user (or agent) then implements the change directly — no plan-story or implement-story needed.

### 6. Implement

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

### 7. Open a PR and mark ready

Push the branch and open a PR:
- Title: `STORY-NNN: <human-readable title>`
- Body: brief summary of what changed and a short manual test plan.
- Open as **ready for review** (not draft) — chores are small and implementation is complete at this point.

### 8. Await merge approval

Per the `merge-story-pr` skill: surface CI status to the user and wait for explicit approval before merging. Do not self-merge.
