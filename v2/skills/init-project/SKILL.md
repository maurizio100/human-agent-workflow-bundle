---
name: init-project
model: haiku
description: Initialize a new project or finalize its conventions. Run once at the start to scaffold the folder structure and a minimal PROJECT.md. Run again after domain-storytelling and arc42-authoring to discuss implementation conventions and write the full PROJECT.md. The skill detects which run is needed based on whether arc42 content exists.
allowed-tools: Read Edit Write Bash
---

# Init Project

## What this skill does

Runs in two modes depending on the project's state:

- **First run** (no arc42 content yet): scaffolds the required folder structure and writes a minimal `PROJECT.md` skeleton — just enough to start domain modelling and architecture work.
- **Second run** (after `domain-storytelling` and `arc42-authoring`): reads the architecture documentation, discusses implementation conventions with the user, and writes the full `PROJECT.md` plus any layer-specific pattern files.

`PROJECT.md` is the central conventions file the other skills read. (If you also want it
auto-loaded into agent context, keep a one-line `CLAUDE.md` that points at `PROJECT.md`.)

## Detecting which run

Check for `docs/arc42/04-solution-strategy.md` and `docs/arc42/08-crosscutting.md`.

- **Both exist with real content** → second run.
- **Either missing or still a stub** → first run.

---

## First run — Scaffold

### 1. Ask for project basics

Ask the user for **three things**:
1. Project name
2. One-line description
3. **Work-tracking backend** — where stories, epics, and change requests live (see the `work-tracking` contract). Only **`github`** is implemented today, and it is the default; other backends (GitLab, Jira, local files, …) require writing an adapter under `.claude/skills/work-tracking/adapters/<name>/` **before the first story is authored**. If the user is unsure, recommend `github`. This is the one workflow choice worth settling now, because it is recorded in `adapter.conf` and every tracking step honors it. Reassure the user it is not urgent: everything up to and including `domain-storytelling`, `arc42-authoring`, and `adr-writing` works with no backend at all — the choice only starts to matter when the first story is created.

That is all you need to scaffold. **Do not ask about tech stack, test commands, database, or deployment** — none of that is known at project start; it emerges from the architecture work and is captured on the second run. Workflow conventions (ID format, branch/commit style) use sensible defaults and are not worth asking about now.

Wait for the answers before creating any files.

### 2. Create folder structure

Create the following folders. For folders that will start empty, add a `.gitkeep`
so they are tracked by git from the first commit:

| Path | Seeded with |
|---|---|
| `docs/arc42/` | `.gitkeep` |
| `docs/adr/` | `.gitkeep` |
| `docs/domain/contexts/` | `.gitkeep` |

Stories and epics are tracked entirely in the **configured work-tracking backend** (see the `work-tracking` contract) — there is no `specs/` scaffolding for them. Each story is one work item titled `STORY-NNN: <title>` whose body holds the spec content (Gherkin / chore) and whose metadata holds state (status, epic, context, layer, type); each epic is a **grouping** titled `EPIC-NNN: <name>` whose description holds the epic goal/stories/scope. Managed via the façade `.claude/skills/work-tracking/tracker.py`.

**Record the chosen backend.** Write the name from step 1 as the single non-comment line of `.claude/skills/work-tracking/adapter.conf` (it already defaults to `github`; set it explicitly so the decision is recorded even when it matches the default). Then:
- If the choice is **`github`**: confirm the adapter is available — `gh` authenticated and Issues enabled on the repo. Labels, epic-groupings, and the backlog are created on demand on first use; no other GitHub setup is needed.
- If the choice is **anything else**: no adapter ships for it. Tell the user that `.claude/skills/work-tracking/adapters/<name>/tracker.py` and `review.py` must be written (against the contract CLI in `work-tracking/SKILL.md`) before the first story is authored, and that scaffolding, domain, and architecture work can proceed in the meantime.

Also create these stub files:

Create `docs/domain/glossary.md` with a header stub (the discovery-analysis skill fills the rows per the `domain-artifacts` glossary template):

```markdown
# Glossary

The ubiquitous language of the domain, organized by Bounded Context. Filled by
the discovery-analysis skill, which adds a `## Shared / Cross-context` table and
a `## <Context>` section per context (see the `domain-artifacts` glossary
template). Use only terms that appear here in Gherkin stories and plans.
```

Create `docs/domain/context-map.md` with a header stub (the discovery-analysis skill fills it per the `domain-artifacts` context-map template):

```markdown
# Context Map

> Bounded contexts and their relationships, discovered and merged by the
> discovery-analysis skill (e.g. domain-storytelling).

## Bounded Contexts

## Relationships

| # | Upstream | Downstream | Type | Clarity | Notes |
|---|----------|------------|------|---------|-------|

## Summary
```

### 3. Write minimal PROJECT.md

Write a `PROJECT.md` with just the name and description from step 1, using this structure. There is **no Tech stack or How to run things section yet** — those are added on the second run once the architecture is known.

```markdown
# <project name>

<one-line description>

## Where things live

- `docs/domain/` — bounded contexts, glossary, context map
- `docs/arc42/` — architecture documentation
- `docs/adr/` — architecture decision records
- **Stories live entirely in the configured work-tracking backend** — one work item per story, titled `STORY-NNN: <title>`; the body is the spec content (Gherkin / chore) and the metadata is the state (status, epic, context, layer, type). **Epics are groupings** titled `EPIC-NNN: <name>`. Managed via `.claude/skills/work-tracking/tracker.py`. There is no `specs/stories/` or `specs/epics/` directory and no in-repo index.

## Domain at a glance

<!-- Owned and kept current by the discovery-analysis skill (via the domain-artifacts
     contract). Filled on the first discovery session; do not write it by hand. -->
_Not yet discovered — run a discovery-analysis skill (e.g. domain-storytelling)._

## Conventions

- **Every source code change must be motivated by a story.** Use `gherkin-story-authoring` for behavioral changes (new features, rule changes) and `chore-story` for non-behavioral changes (layout tweaks, refactorings, dependency updates, tooling).
- Story IDs: `STORY-NNN` / Epic IDs: `EPIC-NNN` / ADR IDs: `NNNN`
- Branch names: `STORY-NNN-kebab-case-title`
- Commit messages: Conventional Commits with `Refs: STORY-NNN` in footer
- One change request per story, draft while in progress, squash on merge
- Default branch: `main`
- Each story is a work item: the body holds the Gherkin / chore spec, and `status:` / `epic:` / `layer:` / `context:` / `type:` metadata hold its classification
- Work tracking backend: `<chosen backend>` (recorded in `.claude/skills/work-tracking/adapter.conf`)
```

### 4. Tell the user what to do next

Summarise what was created and suggest the next steps:

```
Created: folder structure, docs/domain/glossary.md,
         docs/domain/context-map.md, PROJECT.md
Backend: <chosen> (recorded in .claude/skills/work-tracking/adapter.conf)

Next steps:
1. Run domain-storytelling with your Egon .dst export
2. Run arc42-authoring to design the first-class chapters
3. Run init-project again to finalise implementation conventions
```

---

## Second run — Finalise conventions

### 1. Read the architecture

Read in order:
1. `PROJECT.md` — current state (the minimal version from the first run)
2. `docs/arc42/04-solution-strategy.md` — technology choices and structural decisions
3. `docs/arc42/05-building-blocks.md` — building blocks and their responsibilities
4. `docs/arc42/08-crosscutting.md` — test strategy, error handling, security, logging
5. `docs/domain/contexts/*.md` — all bounded contexts (for naming the package structure)

### 2. Discuss implementation conventions

Based on what you read, lead a focused discussion with the user. Cover each area in turn — propose a convention, wait for the user to confirm or adjust before moving to the next.

#### Building block structure
Propose how the building blocks map to the actual code structure. Base this on the solution strategy and building block names.

Example for a Spring Boot modular monolith:
> "Your building blocks are Catalog, Preference, and Ordering. Shall we organise them as top-level packages — e.g. `com.example.catalog`, `com.example.preference` — each containing their own domain, application, and infrastructure sub-packages?"

Example for an Angular SPA:
> "For the frontend, shall we mirror the bounded contexts as Angular feature modules — `CatalogModule`, `PreferenceModule` — each with their own components, services, and routes?"

#### Test organisation
Propose how tests are structured, based on the test strategy in `08-crosscutting.md`.

Example:
> "Your test strategy defines Unit, Repository, API/Acceptance, and Frontend component levels. Shall we put step definitions in `src/test/kotlin/<context>/steps/`, fixtures in `src/test/kotlin/<context>/fixtures/`, and the executable `.feature` files in `src/test/resources/features/` (transcribed from the story work items)?"

Ask about:
- Where step definition classes live and how they're named
- How fixture/builder classes are named (e.g. `aUser()`, `anOrder()`)
- How the test context is set up (e.g. `@SpringBootTest`, `TestBed`)
- Whether there's a `DatabaseCleaner` or equivalent between tests

#### Database conventions
Only relevant for projects with a backend database. Ask about:
- Migration tool and file naming (e.g. Flyway `V1__description.sql`, Liquibase changesets)
- Table and column naming (snake_case? plural table names?)
- ID strategy (UUID, auto-increment sequence, domain-generated?)
- Whether JPA entities use a separate `@Column(name=...)` mapping or rely on naming conventions

Example:
> "You're using Spring Boot with JPA and PostgreSQL. Shall we use Flyway for migrations with the naming pattern `V<version>__<description>.sql`, snake_case column names, and UUIDs as primary keys?"

#### API design conventions
Only relevant for projects with a REST API. Ask about:
- Base URL pattern (e.g. `/api/v1/`, `/api/`)
- Whether responses use an envelope (`{ data: ..., meta: ... }`) or return the resource directly
- How pagination is represented (query params, response headers, or body fields)
- HTTP verb and URL conventions for non-CRUD operations

Example:
> "Shall we use `/api/` as the base path, return resources directly without an envelope, and represent pagination as `?page=0&size=20` with total count in the response body?"

#### Error handling shape
Ask about:
- What HTTP status codes map to what domain errors (404 for not found, 409 for conflict, 422 for validation failures?)
- What the error response body looks like (RFC 9457 Problem Details? Custom shape?)
- Whether validation errors include field-level detail

Example:
> "For error responses, shall we use RFC 9457 Problem Details (`type`, `title`, `status`, `detail`) with an additional `errors` array for field-level validation failures?"

#### Domain events and cross-context communication
Only relevant if the architecture has multiple bounded contexts. Ask:
- How do contexts communicate? (In-process application events, message broker, shared DB read model?)
- If using events, what's the naming convention for event classes?
- Are events synchronous or asynchronous, and does that affect test setup?

Skip this topic if the architecture has only one bounded context or if contexts are fully independent.

#### Additional layer-specific patterns
If the project has both a backend and a frontend, ask about each separately. Ask whether there are routing conventions, HTTP client patterns, auth handling patterns, or component naming rules worth capturing.

### 3. Write the full PROJECT.md

Update `PROJECT.md` with everything agreed in the discussion. Add sections for:
- **Tech stack** — the backend language/framework, frontend framework, database, and deployment target, as established in `docs/arc42/04-solution-strategy.md` (confirm with the user if anything is unstated).
- **How to run things** — the test/build/run commands for the stack (e.g. `./gradlew test`, `npm test`). Ask the user for these now; they weren't known at scaffold time.
- **Domain at a glance** — **do not write or regenerate this section.** It is owned and kept current by the discovery-analysis skill (via the `domain-artifacts` contract), which rewrites it after every discovery session. Leave whatever is already there untouched. (If the section is somehow missing entirely, leave the placeholder be — the discovery skill will fill it on its next run.)
- **Foreign systems** (one-liner per system; detail lives in `docs/arc42/03-context.md`)
- **Frontend design conventions** (if applicable — link to pattern file)
- **Backend test conventions** (if applicable — link to pattern file)
- Any project-specific rules the agent must follow

### 4. Write layer-specific pattern files (if needed)

If the discussion produced enough detail, create one or both of:

**`docs/arc42/backend-test-patterns.md`** — covering:
- Fixture builder pattern and naming (e.g. `aUser()`)
- `DatabaseCleaner` / between-test reset approach
- Step definition class structure
- How the test context is wired (e.g. Spring Boot)
- Database migration conventions (tool, naming pattern, ID strategy)
- API URL base path and error response shape
- Domain event naming and test setup (if applicable)

**`docs/arc42/frontend-patterns.md`** — covering:
- Signal and state management patterns
- HTTP client conventions
- `data-testid` attribute conventions
- Component test setup approach (e.g. `TestBed`)

Only create these files if there is enough to say. A half-empty pattern file is worse than no file — it creates false confidence. If the discussion didn't produce enough detail, note in PROJECT.md that the pattern file will be created after the first story is implemented.

### 5. Tell the user what was written

Summarise the changes and suggest next steps:

```
Updated: PROJECT.md
Created: <list any pattern files>

Next steps:
1. Run gherkin-story-authoring to write the first stories
2. Run backlog-grooming if you want help deciding where to start
```
