---
name: backlog-grooming
description: Collaborative backlog refinement — reads the current project state, identifies gaps, and suggests new stories to discuss with the user. Use this skill whenever the user wants to think about what to build next, asks for story suggestions, wants to review the backlog, or says something like "what should we work on next?" or "let's plan the next stories". Ends by handing agreed stories off to gherkin-story-authoring.
model: sonnet
allowed-tools: Read
---

# Backlog Grooming

## What this skill does

Reads the current state of the project and engages in a discussion with the user to identify and agree on the next stories worth building. Suggestions are grounded in what is already implemented, what the domain model anticipates, and what context boundaries still need work.

## What this skill does NOT do

- It does not write `.feature` files itself. Once a story is agreed, it hands off to `gherkin-story-authoring`.
- It does not prioritise autonomously. Priority is a human decision; the skill surfaces options and trade-offs.
- It does not invent domain concepts. Suggestions stay within the bounded contexts, glossary, and building blocks already defined.

## What to read before suggesting

Spawn the `project-state-reader` subagent. It reads the **live backlog from GitHub issues**
(the single source of truth for story state — every story is an issue), plus epics, domain
contexts, relationships, and building blocks, and returns a compact project state snapshot.

Wait for the snapshot before saying anything to the user.

## The grooming session, step by step

### 1. Build the project state snapshot

After reading, produce a compact snapshot covering:

```markdown
## Project state

### Done
- STORY-001: ...
- STORY-002: ...

### In progress
- STORY-NNN: ... (branch open)

### Planned (ready/draft)
- STORY-NNN: ... [ready]
- STORY-NNN: ... [draft]

### Context coverage
| Context       | Status                                         |
|---------------|------------------------------------------------|
| <context-A>   | No stories yet — building block exists         |
| <context-B>   | Partially built (STORY-NNN, NNN done)          |
| <context-C>   | No stories yet — event consumer anticipated    |

### Unimplemented relationships
- <context-B> → <context-C>: event published but nothing consumes it
- <context-A> → <context-B>: read model not yet wired
```

Show this snapshot to the user before suggesting anything. It lets them correct any misreading before the discussion goes further.

### 2. Suggest candidate stories

Based on the snapshot, propose 3–6 story candidates. For each:

```markdown
### Candidate: <working title>

**Context:** <which bounded context>
**Rationale:** <why this makes sense now — dependency satisfied, logical next step, gap in a context>
**Rough scope:** <1–3 sentences on what it would cover>
**Depends on:** <any stories that should ship first, or "none">
**Unlocks:** <what becomes possible after this>
```

Prioritise candidates by:
1. **Unblocked next steps** — stories whose dependencies are already done
2. **Relationship completion** — stories that wire up an existing but unused context relationship
3. **Context coverage** — stories that start a context with no implementation yet
4. **Depth** — stories that extend a partially built context

Do not present more candidates than the user can reasonably discuss in one session. Six is usually the ceiling.

### 3. Discuss

Let the user react. They may:
- Accept a candidate as-is → add to the agreed list
- Reshape a candidate → refine the scope together, update the candidate
- Reject a candidate → note why (useful context for future sessions)
- Raise a story idea not in the candidates → explore it together using the same candidate format

Keep the discussion grounded. If a new idea references a concept not in the glossary or a context not in the relationships map, flag it — that may be domain modelling work before a story can be written.

### 4. Agree and hand off

Once the user is satisfied with one or more stories, confirm the agreed list:

```markdown
## Agreed stories for authoring

1. <working title> — <one-line scope>
2. <working title> — <one-line scope>
```

Then hand each agreed story off to `gherkin-story-authoring` in turn. The working title and rough scope from the discussion become the seed input for that skill.

If the user wants to author only one story now and revisit the rest later, that is fine — the discussion itself is the output; the candidates list does not need to be persisted unless the user asks for it.

## When to push back

Stop and flag to the user if:
- A candidate story would require a building block that does not exist in `docs/arc42/05-building-blocks.md` — architecture work may be needed first
- A candidate crosses multiple bounded contexts in a way that looks like two stories — propose the split
- A candidate references a term not in the glossary — domain modelling may be needed first (hand off to `domain-storytelling`)
- The user proposes a story that would contradict an existing ADR — surface the conflict before agreeing
