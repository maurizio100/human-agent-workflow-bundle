---
name: domain-storytelling
description: Analyze finished Domain Storytelling stories (typically Egon .dst exports) and produce the downstream domain artifacts — bounded context candidates, glossary entries, relationship hints, and seed Gherkin stories. Use this skill whenever the user shares an Egon .dst file, a domain story write-up, a numbered actor/work-object/activity narrative, or asks to analyze, decompose, or extract structure from a domain story. Trigger this even if the user just says "here's a domain story" or "look at this workshop output" without explicitly asking for analysis — the analysis is what they want. Do NOT use this skill to facilitate or simulate a workshop; the user runs workshops themselves and brings the finished story to the agent.
allowed-tools: Read Edit Write
---

# Domain Storytelling Analysis

## What this skill does

Takes a finished domain story (the output of a Domain Storytelling workshop) and produces the four downstream artifacts that feed the rest of the workflow:

1. **Bounded context candidates** — clusters of language and activity that suggest a context boundary
2. **Glossary entries** — terms used in the story, defined in the actors' own words
3. **Relationships** — how candidate contexts interact (upstream/downstream, customer/supplier, conformist, anti-corruption layer)
4. **Seed Gherkin stories** — one or more rough acceptance scenarios derived from the activities

These outputs land in `docs/domain/` as Markdown so they stay in the agent's context for all downstream work.

## What this skill does NOT do

- It does not run or simulate a workshop. The user facilitates workshops and provides finished stories.
- It does not invent actors, work objects, or activities not present in the source story.
- It does not finalize bounded contexts. It produces *candidates* for human review.
- It does not write production-quality Gherkin. That's the `gherkin-story-authoring` skill's job. This skill produces *seeds*.

## Input format

The primary input is an **Egon `.dst` file** — a JSON document exported from the Domain Storytelling tool at https://egon.io. Structure (simplified):

```json
{
  "domain": "...",
  "description": "...",
  "actors":     [{ "id": "...", "name": "..." }],
  "workObjects":[{ "id": "...", "name": "..." }],
  "activities": [
    { "number": 1, "from": "actor:...", "to": "workObject:...", "label": "..." },
    { "number": 2, "from": "...", "to": "...", "label": "..." }
  ]
}
```

The skill should parse the JSON, walk activities in numerical order, and treat the `label` on each activity as the verb phrase, `from`/`to` as the participants.

If the user provides a different format (prose write-up, photo, numbered sentences), accept it but ask once whether an Egon export is available — it's structured and removes ambiguity.

## How to analyze a story

Work through these passes in order. Do not skip ahead.

### Pass 1 — Read the story end to end

Before producing anything, walk through the activities in sequence and narrate what happens in plain language. This forces you to actually understand the flow rather than pattern-matching on individual sentences. If anything is ambiguous (a missing actor, an unnamed work object, an activity label that could mean two things), flag it now and ask the user before proceeding. Do not guess.

### Pass 2 — Extract glossary terms

For every distinct **actor** and **work object** in the story, create a glossary entry with:
- The term as written in the story (preserve casing and spacing — this is the ubiquitous language)
- A one-sentence definition derived from how the term is used in the activities
- A list of the activity numbers where it appears

If the same concept appears under two different names in the story, do *not* unify them silently. Note both names and flag the inconsistency for human review — it might be intentional (two contexts) or a slip (rename needed).

### Pass 3 — Identify bounded context candidates

Look for clusters where:
- The same actors and work objects appear together repeatedly
- The same vocabulary is used consistently
- Activities form a self-contained sub-flow with a clear input and output

Each cluster is a **candidate** bounded context. Give it a provisional name based on the dominant activity or work object. Do not commit to boundaries — present them as proposals with the evidence (which activities, which actors).

A story with fewer than ~8 activities usually yields one context. Don't force a split.

### Pass 4 — Map relationships between candidate contexts

For each pair of candidate contexts that interact (an activity crosses the boundary), describe the relationship using DDD context-mapping language:
- **Customer/Supplier** — downstream depends on upstream, upstream accommodates downstream
- **Conformist** — downstream accepts upstream's model as-is
- **Anti-corruption layer** — downstream translates to protect its own model
- **Shared kernel** — both contexts share part of the model
- **Open host service** — upstream offers a stable interface to many downstreams

If you can't tell which pattern applies, say so and describe the interaction in plain language. Don't guess at a pattern label.

### Pass 5 — Derive seed Gherkin stories

For each significant sub-flow (typically 2–5 activities that achieve a goal for an actor), write a **seed** Gherkin scenario:

```gherkin
Feature: <short name derived from the goal>

  Scenario: <what the actor accomplishes>
    Given <starting state derived from the activities before this sub-flow>
    When <the actor's action, in the actor's words>
    Then <the resulting state, in the actor's words>
```

These are *seeds* — rough, incomplete, single-scenario. They have no story ID, no Background, no Examples table. The `gherkin-story-authoring` skill will turn them into proper stories later.

## Output: where things go

Write the analysis to these files in the repo. Create folders if they don't exist.

- `docs/domain/stories/<story-name>.analysis.md` — the full analysis: glossary entries, candidate contexts with evidence, relationships, seed scenarios. One file per analyzed story.
- `docs/domain/glossary.md` — append new glossary entries here, alphabetically. If a term already exists with a different definition, do not overwrite it; add a "see also" note and flag the conflict.
- `docs/domain/contexts/<context-name>.md` — one file per candidate context. See the template below.
- `docs/domain/relationships.md` — append a relationship entry per pair of contexts that interact.

### Context file template

Every context file created by this skill uses this structure:

```markdown
# Context: <name>

<2-4 sentence description derived from the domain story>

## Actors involved
- <actor name> — <role in this context>

## Work objects
- <work object name> — <role in this context>

## Activities
<compact summary of the activities that happen within this context,
with references to the source domain story's activity numbers>

## Tactical model

> Status: not yet discovered
> The tactical model emerges during implementation. Each story that
> touches this context adds or modifies entries below via the
> `implement-story` skill. Do not pre-populate from the domain
> story — tactical choices are made at code time, not at analysis time.

### Aggregates
_No entries yet._

### Entities (non-aggregate roots)
_No entries yet._

### Value objects
_No entries yet._

### Domain services
_No entries yet._
```

The Tactical model section is deliberately empty at creation. The `domain-storytelling` skill does **not** guess at aggregates from the domain story, even when work objects look like obvious aggregate candidates. Pre-committing to tactical boundaries before implementation is exactly the kind of up-front over-design the workflow avoids. The section exists as a waiting slot; the TDD loop fills it in as stories ship.

The seed Gherkin scenarios stay inside `docs/domain/stories/<story-name>.analysis.md` until the `gherkin-story-authoring` skill promotes them to `.feature` files. Do not create `.feature` files from this skill.

## When to push back

This skill is permissive on naming and definitions (it's draft material) but **strict on bounded-context boundaries**. Boundary mistakes are expensive to fix later. If you're not confident about a context split, present it as a question to the human, not as an answer.

Specifically, ask the human before proceeding if:
- An actor or work object's name is ambiguous or appears inconsistently
- An activity's verb phrase could mean two materially different things
- A candidate context boundary cuts across what looks like a single transaction or a single actor's responsibility
- The story references something outside its own scope (a foreign system, an unmentioned actor) without explanation

For everything else (glossary phrasing, seed scenario wording, choice of relationship label when one is clearly correct), proceed and let the human correct on review.

## Worked outline of a session

1. User drops `docs/domain/stories/checkout.dst` into the repo and says "analyze this."
2. Read the file. Walk activities 1..N. Narrate the flow back to the user in 3–5 sentences. Confirm understanding.
3. If anything is ambiguous, ask once and wait. Otherwise proceed.
4. Produce glossary entries (Pass 2).
5. Produce candidate contexts (Pass 3).
6. Produce relationships (Pass 4).
7. Produce seed Gherkin scenarios (Pass 5).
8. Write all four to the files listed above.
9. Update the `## Domain at a glance` section in `CLAUDE.md`. Read all context files in `docs/domain/contexts/`, the glossary, and the relationships file, then rewrite the section with a 3–5 line summary covering: what the system does, who the actors are, the bounded contexts by name, and the core workflow as a short flow. End with a pointer to `docs/domain/` for the full model. If the section does not exist yet, add it after the `## Where things live` section (or after `## Tech stack` if `Where things live` doesn't exist). If it already exists, replace it with the updated version.
10. Summarize what was produced and where, in 5–10 lines, and call out anything that needs human review.
