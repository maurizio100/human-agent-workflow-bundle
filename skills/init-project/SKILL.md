---
name: init-project
description: Initialize a new project. Asks for a name and description, scaffolds the required folder structure, and writes a minimal CLAUDE.md — just enough to start domain modelling. Run once at project start.
allowed-tools: Read Edit Write Bash
---

# Init Project

## What this skill does

Scaffolds a new project: creates the standard folder structure, stub files, and a minimal `CLAUDE.md` with just the project name and description — enough to start domain modelling with `domain-storytelling`.

---

## Step 1 — Ask for project basics

Ask the user for only two things:
1. Project name
2. One-line description

Wait for the answer before creating any files.

## Step 2 — Create folder structure

Create the following folders. For folders that will start empty, add a `.gitkeep` so they are tracked by git from the first commit:

| Path | Seeded with |
|---|---|
| `docs/arc42/` | `.gitkeep` |
| `docs/adr/` | `.gitkeep` |
| `docs/domain/contexts/` | `.gitkeep` |
| `specs/epics/` | `.gitkeep` |
| `specs/stories/` | `.gitkeep` |
| `specs/done/` | `.gitkeep` |

Also create these stub files:

Create `specs/STORIES.md` with the table header:

```markdown
# Story Index

| ID | Epic | Title | Context | Layer | Status |
|---|---|---|---|---|---|
```

Create `docs/domain/glossary.md` with a header stub:

```markdown
# Glossary

> Terms are defined here as they emerge from domain storytelling sessions.
> Use only terms that appear in this file in Gherkin stories and plans.
```

Create `docs/domain/relationships.md` with a header stub:

```markdown
# Context Relationships

> Cross-context dependencies are documented here after domain storytelling.
```

## Step 3 — Write minimal CLAUDE.md

Write a `CLAUDE.md` with just the name and description:

```markdown
# <project name>

<one-line description>
```

## Step 4 — Tell the user what to do next

Summarise what was created and give the next steps in order:

```
Created: folder structure, specs/STORIES.md, docs/domain/glossary.md,
         docs/domain/relationships.md, CLAUDE.md

Next steps:
1. Add the skill bundle and any custom agents to the .claude/ directory
2. Add your domain story exports (Egon .dst files) to specs/stories/
3. Run domain-storytelling to analyse the stories and produce bounded contexts, glossary, and seed scenarios
4. Run arc42-authoring to design the architecture chapters
5. Run finalize-conventions to lock in implementation conventions and write the full CLAUDE.md
```
