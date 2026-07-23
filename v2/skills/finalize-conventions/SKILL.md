---
name: finalize-conventions
description: Finalize implementation conventions after domain-storytelling and arc42-authoring are complete. Reads the architecture documentation, discusses conventions with the user, and writes the full CLAUDE.md plus layer-specific pattern files. Run this once arc42 content exists.
allowed-tools: Read Edit Write Bash
---

# Finalize Conventions

## What this skill does

Reads the architecture documentation produced by `domain-storytelling` and `arc42-authoring`, leads a focused discussion about implementation conventions, and writes:

- the full `CLAUDE.md`
- `docs/arc42/backend-test-patterns.md` (if the project has a backend)
- `docs/arc42/frontend-patterns.md` (if the project has a frontend)

Run this once after `arc42-authoring` is complete.

---

## Step 1 — Read the architecture

Read in order:
1. `CLAUDE.md` — current state of the project's navigation index and always-on rules
2. `docs/arc42/04-solution-strategy.md` — technology choices and structural decisions
3. `docs/arc42/05-building-blocks.md` — building blocks and their responsibilities
4. `docs/arc42/08-crosscutting.md` — test strategy, error handling, security, logging
5. `docs/domain/contexts/*.md` — all bounded contexts (for naming the package structure)
6. `docs/domain/glossary.md` and `docs/domain/relationships.md`

## Step 2 — Discuss implementation conventions

Based on what you read, lead a focused discussion with the user. Cover each area in turn — propose a convention, wait for the user to confirm or adjust before moving to the next.

### Tech stack and how to run things
The solution strategy should already name the stack. Confirm with the user:
- Backend language/framework, frontend framework (if any), database, deployment target
- Test commands (e.g. `cd backend && ./gradlew test`, `npm test`)

### Story, branch, and commit conventions
Propose the defaults and let the user correct any of them:
- Story/Epic/ADR ID format: `STORY-NNN` / `EPIC-NNN` / `NNNN`
- Branch naming: `STORY-NNN-kebab-case-title`
- Commit messages: Conventional Commits with `Refs: STORY-NNN` footer
- One PR per story, draft while in progress, squash on merge

### Building block structure
Propose how the building blocks map to the actual code structure. Base this on the solution strategy and building block names.

Example for a Spring Boot modular monolith:
> "Your building blocks are Catalog, Preference, and Ordering. Shall we organise them as top-level packages — e.g. `com.example.catalog`, `com.example.preference` — each containing their own domain, application, and infrastructure sub-packages?"

Example for an Angular SPA:
> "For the frontend, shall we mirror the bounded contexts as Angular feature modules — `CatalogModule`, `PreferenceModule` — each with their own components, services, and routes?"

### Test organisation
Propose how tests are structured, based on the test strategy in `08-crosscutting.md`.

Example:
> "Your test strategy defines Unit, Repository, API/Acceptance, and Frontend component levels. Shall we put step definitions in `src/test/kotlin/<context>/steps/`, fixtures in `src/test/kotlin/<context>/fixtures/`, and feature files picked up from `specs/stories/`?"

Ask about:
- Where step definition classes live and how they're named
- How fixture/builder classes are named (e.g. `aUser()`, `anOrder()`)
- How the test context is set up (e.g. `@SpringBootTest`, `TestBed`)
- Whether there's a `DatabaseCleaner` or equivalent between tests

### Database conventions
Only relevant for projects with a backend database. Ask about:
- Migration tool and file naming (e.g. Flyway `V1__description.sql`, Liquibase changesets)
- Table and column naming (snake_case? plural table names?)
- ID strategy (UUID, auto-increment sequence, domain-generated?)
- Whether JPA entities use a separate `@Column(name=...)` mapping or rely on naming conventions

Example:
> "You're using Spring Boot with JPA and PostgreSQL. Shall we use Flyway with the naming pattern `V<version>__<description>.sql`, snake_case column names, and UUIDs as primary keys?"

### API design conventions
Only relevant for projects with a REST API. Ask about:
- Base URL pattern (e.g. `/api/v1/`, `/api/`)
- Whether responses use an envelope (`{ data: ..., meta: ... }`) or return the resource directly
- How pagination is represented (query params, response headers, or body fields)
- HTTP verb and URL conventions for non-CRUD operations

Example:
> "Shall we use `/api/` as the base path, return resources directly without an envelope, and represent pagination as `?page=0&size=20` with total count in the response body?"

### Error handling shape
Ask about:
- What HTTP status codes map to what domain errors (404 for not found, 409 for conflict, 422 for validation failures?)
- What the error response body looks like (RFC 9457 Problem Details? Custom shape?)
- Whether validation errors include field-level detail

Example:
> "For error responses, shall we use RFC 9457 Problem Details (`type`, `title`, `status`, `detail`) with an additional `errors` array for field-level validation failures?"

### Domain events and cross-context communication
Only relevant if the architecture has multiple bounded contexts. Ask:
- How do contexts communicate? (In-process application events, message broker, shared DB read model?)
- If using events, what's the naming convention for event classes?
- Are events synchronous or asynchronous, and does that affect test setup?

Skip this topic if the architecture has only one bounded context or if contexts are fully independent.

### Additional layer-specific patterns
If the project has both a backend and a frontend, ask about each separately. Ask whether there are routing conventions, HTTP client patterns, auth handling patterns, or component naming rules worth capturing.

## Step 3 — Write the full CLAUDE.md

Replace `CLAUDE.md` with a complete version that mirrors this structure:

```markdown
# <project name>

<one-line description>

## Tech stack

<tech stack bullets>

## How to run things

```
<test commands>
```

## Domain at a glance

<3–5 lines distilled from the domain artifacts: what the system does, who the actors are, the bounded contexts by name, and the core workflow as a short flow. End with a pointer to `docs/domain/` for the full model.>

## Where things live

- `docs/domain/` — bounded contexts, glossary, relationships
- `docs/arc42/` — architecture documentation
- `docs/adr/` — architecture decision records
- `specs/stories/` — open story files (`.feature` for behavioral stories, `.md` for chores)
- `specs/done/` — completed story files
- `specs/epics/` — epic descriptions
- `specs/STORIES.md` — story index (ID, epic, title, context, layer, status)

## Foreign systems

<one-liner per external system; detail lives in `docs/arc42/03-context.md`>

## Frontend design conventions

<only if the project has a frontend>
For frontend or fullstack stories, read both of these before writing any component code:
- `docs/adr/<NNN>-frontend-design-system.md` — colors, typography, component patterns
- `docs/arc42/frontend-patterns.md` — signals, HTTP, test setup, `data-testid` conventions

## Backend test conventions

<only if the project has a backend>
For backend or fullstack stories, read this before writing any step definitions:
- `docs/arc42/backend-test-patterns.md` — fixture builder, DatabaseCleaner, step class structure

## Conventions

- **Every source code change must be motivated by a story.** Use `gherkin-story-authoring` for behavioral changes (new features, rule changes) and `chore-story` for non-behavioral changes (layout tweaks, refactorings, dependency updates, tooling).
- Story IDs: `STORY-NNN` / Epic IDs: `EPIC-NNN` / ADR IDs: `NNNN`
- Branch names: `STORY-NNN-kebab-case-title`
- Commit messages: Conventional Commits with `Refs: STORY-NNN` in footer
- One PR per story, draft while in progress, squash on merge
- Default branch: `main`
- Every story file (`.feature` or `.md`) carries `# Layer:` and `# Context:` headers
```

Omit the **Frontend design conventions** section if there is no frontend. Omit the **Backend test conventions** section if there is no backend. Omit the **Foreign systems** section if there are none.

## Step 4 — Write layer-specific pattern files (if needed)

If the discussion produced enough detail, create one or both of:

**`docs/arc42/backend-test-patterns.md`** — covering:
- Fixture builder pattern and naming (e.g. `aUser()`)
- `DatabaseCleaner` / between-test reset approach
- Step definition class structure
- How the Spring Boot test context is wired
- Database migration conventions (tool, naming pattern, ID strategy)
- API URL base path and error response shape
- Domain event naming and test setup (if applicable)

**`docs/arc42/frontend-patterns.md`** — covering:
- Signal and state management patterns
- HTTP client conventions
- `data-testid` attribute conventions
- `TestBed` setup approach for component tests

Only create these files if there is enough to say. A half-empty pattern file is worse than no file — it creates false confidence. If the discussion didn't produce enough detail, note in CLAUDE.md that the pattern file will be created after the first story is implemented.

## Step 5 — Tell the user what was written

Summarise the changes and suggest next steps:

```
Updated: CLAUDE.md
Created: <list any pattern files>

Next steps:
1. Run gherkin-story-authoring to write the first stories
2. Run backlog-grooming if you want help deciding where to start
```
