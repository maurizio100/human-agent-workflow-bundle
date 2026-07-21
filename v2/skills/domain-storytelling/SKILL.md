---
name: domain-storytelling
model: sonnet
description: Analyze finished Domain Storytelling stories (typically Egon .dst exports) and produce the downstream domain artifacts — bounded context candidates, glossary entries, and the context map. Use this skill whenever the user shares an Egon .dst file, a domain story write-up, a numbered actor/work-object/activity narrative, or asks to analyze, decompose, or extract structure from a domain story. Trigger this even if the user just says "here's a domain story" or "look at this workshop output" without explicitly asking for analysis — the analysis is what they want. Do NOT use this skill to facilitate or simulate a workshop; the user runs workshops themselves and brings the finished story to the agent.
allowed-tools: Read Edit Write
---

# Domain Storytelling Analysis

This skill is the **Domain Storytelling adapter** for domain discovery. It knows how to read a Domain Storytelling source and *what to extract* from it. The artifacts it produces — their formats, file locations, and invariants — are defined by the shared **`domain-artifacts` output contract** at `skills/domain-artifacts/SKILL.md` (a sibling of this skill). **Read that contract and its `assets/` before writing anything.** This file covers only what is specific to Domain Storytelling.

## What this skill does

Takes a finished domain story (the output of a Domain Storytelling workshop) and extracts:

1. **Glossary entries** — the actors and work objects, defined in the story's own words
2. **Bounded context candidates** — clusters of language and activity that suggest a context boundary
3. **The context map** — how the candidate contexts interact

It then writes these as specified by the `domain-artifacts` contract.

## What this skill does NOT do

- It does not run or simulate a workshop. The user facilitates workshops and provides finished stories.
- It does not invent actors, work objects, or activities not present in the source story.
- It does not finalize bounded contexts. It produces *candidates* for human review.
- It does not derive user stories or Gherkin. Story authoring is a separate, decoupled session (`gherkin-story-authoring`), not part of discovery.

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

Parse the JSON, walk activities in numerical order, and treat the `label` on each activity as the verb phrase, `from`/`to` as the participants.

If the user provides a different format (prose write-up, photo, numbered sentences), accept it but ask once whether an Egon export is available — it's structured and removes ambiguity.

## How to analyze a story

Work through these passes in order. Do not skip ahead.

### Pass 1 — Read the story end to end

Before producing anything, walk through the activities in sequence and narrate what happens in plain language. This forces you to actually understand the flow rather than pattern-matching on individual sentences. If anything is ambiguous (a missing actor, an unnamed work object, an activity label that could mean two things), flag it now and ask the user before proceeding. Do not guess.

### Pass 2 — Extract glossary terms

The Domain Storytelling terms are its **actors** and **work objects**. For every distinct actor and work object, produce a glossary entry: the term as written, a one-sentence definition from how it's used, and the activity numbers where it appears. Follow the glossary rules in the contract (alphabetical append, conflict flagging, no silent unification of two names for one concept).

### Pass 3 — Identify bounded context candidates

Look for clusters where:
- The same actors and work objects appear together repeatedly
- The same vocabulary is used consistently
- Activities form a self-contained sub-flow with a clear input and output

Each cluster is a **candidate** bounded context. Give it a provisional name based on the dominant activity or work object. Present candidates as proposals with the evidence (which activities, which actors); do not commit to boundaries. Write each as a context file per the contract's `context-file-template.md` — map Domain Storytelling **actors → Participants** and **work objects → Concepts**, and summarize the in-context activities (with activity numbers) under Behaviour.

Once contexts are assigned, backfill the glossary's `Context` column for each term (the terms collected in Pass 2 get their context membership here). A term used in several contexts with the same meaning stays one row; a term that means something different per context splits into a row per context.

A story with fewer than ~8 activities usually yields one context. Don't force a split.

### Pass 4 — Build the context map

For each pair of candidate contexts where an **activity crosses the boundary**, add a relationship row to the context map. The map's format — the exact `Type`-column grammar, the canonical DDD pattern vocabulary, the `Clarity`/`Notes` columns, the merge rules, and the `## Summary` — is defined in the contract and its `context-map-template.md`. Follow it exactly; the string is machine-parsed by a visualizer.

## Where output goes

Everything is written per the `domain-artifacts` contract: the analysis record at `docs/domain/stories/<story-name>.analysis.md`, the glossary, one context file per candidate, and the merged `docs/domain/context-map.md`. Finish with the contract's CLAUDE.md `## Domain at a glance` update and the closing summary.

## When to push back

Domain Storytelling is permissive on naming and definitions (draft material) but **strict on bounded-context boundaries** (see the contract invariants). Ask the human before proceeding if:

- An actor or work object's name is ambiguous or appears inconsistently
- An activity's verb phrase could mean two materially different things
- A candidate context boundary cuts across what looks like a single transaction or a single actor's responsibility
- The story references something outside its own scope (a foreign system, an unmentioned actor) without explanation

For everything else (glossary phrasing, choice of a clearly-correct relationship label), proceed and let the human correct on review.

## Worked outline of a session

1. User drops `docs/domain/stories/checkout.dst` into the repo and says "analyze this."
2. Read the `domain-artifacts` contract and its templates.
3. Read the story. Walk activities 1..N. Narrate the flow back to the user in 3–5 sentences. Confirm understanding.
4. If anything is ambiguous, ask once and wait. Otherwise proceed.
5. Extract glossary terms (Pass 2).
6. Identify candidate contexts and write their context files (Pass 3).
7. Build/merge the context map (Pass 4).
8. Update the `## Domain at a glance` section in `CLAUDE.md` per the contract.
9. Summarize what was produced and where, in 5–10 lines, and call out anything that needs human review.
