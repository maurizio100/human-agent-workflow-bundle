---
name: domain-artifacts
model: sonnet
description: The shared output contract for domain-discovery analysis. Defines the domain artifacts (glossary, bounded-context files, the consolidated context map), where they live under docs/domain/, their exact formats and templates, the invariants that must hold, and the CLAUDE.md update. This skill is NOT invoked directly by users — it is referenced by discovery-analysis skills (domain-storytelling, eventstorming, …) which know how to read a specific discovery method's output and then write the artifacts as specified here. If you are analyzing a discovery source, use the matching method skill; it will point you here for the output contract.
allowed-tools: Read Edit Write
---

# Domain Artifacts — output contract

## Purpose

This is the **method-agnostic output contract** for domain discovery. However a domain was discovered — Domain Storytelling, EventStorming, Example Mapping, interviews — the resulting artifacts have the same shape, the same locations, and the same invariants. This skill owns all of that.

A **discovery-analysis skill** (the "adapter") knows how to read one method's output and *what to extract* from it. It then produces the artifacts defined here. Keep the seam clean:

- **The adapter decides** what counts as a term, a participant, a candidate context, an interaction, a sub-flow — using its method's vocabulary.
- **This contract decides** the artifact set, file layout, formats/templates, invariants, and the final CLAUDE.md update.

Do not duplicate this contract into an adapter. Reference it.

## The artifacts and where they go

Write to these files in the repo. Create folders if they don't exist. `<source-name>` is the name of the analyzed discovery source (e.g. a story or workshop board).

| Artifact | Location | Cardinality |
|---|---|---|
| Analysis record | `docs/domain/stories/<source-name>.analysis.md` | one per analyzed source |
| Glossary | `docs/domain/glossary.md` | one, append-merged |
| Bounded-context file | `docs/domain/contexts/<context-name>.md` | one per candidate context |
| Context map | `docs/domain/context-map.md` | one, merge-updated |

> The folder is `docs/domain/stories/` regardless of discovery method — it holds the analysis record for whatever source was analyzed. Keep the source file (e.g. an Egon `.dst`, an EventStorming export) next to its analysis record.

## Glossary

**The global glossary is the single source of truth for the ubiquitous language.** There are no separate per-context glossary files — a per-context view is this table filtered by its `Context` column. Bounded-context files therefore *name* their terms and link here; they do not restate definitions (see the context-file template).

`docs/domain/glossary.md`, following `assets/glossary-template.md`. Read that template before writing — it defines the table columns and conventions. Each row has:
- **Term** — exactly as written in the source (preserve casing, spacing, and language — this is the ubiquitous language; do not translate or normalise).
- **Context** — the bounded context(s) where the term is used. Same meaning across several contexts → one row, comma-separated. Divergent meaning → one row per context (see below).
- **Definition** — one sentence derived from how the term is used.
- **Source** — provenance, which numbered elements of the source it appears in.
- **Notes** — aliases, see-also links, review flags.

**Insert** new rows at their alphabetical position — do not re-sort or rewrite existing rows. **Never overwrite an existing definition.** Because the same word can mean different things in different bounded contexts, divergent meanings get **one row per context** (same Term, different Context), cross-linked in Notes with a `⚠` conflict flag. If the same concept appears under two names in one source, do not unify silently — record both and flag it.

## Bounded-context files

One file per candidate context, following `assets/context-file-template.md`. Read that template before writing.

The **Tactical model section is deliberately empty at creation.** Do not guess at aggregates, entities, or value objects from the discovery source, even when a concept looks like an obvious aggregate. Pre-committing to tactical boundaries before implementation is exactly the up-front over-design this workflow avoids. The section is a waiting slot; the TDD loop fills it in as stories ship (via `implement-story`).

## Context map

A single consolidated `docs/domain/context-map.md`, following `assets/context-map-template.md`. Read that template before writing — it defines the section layout and, critically, the exact `Type`-column grammar.

Direction is **Upstream → Downstream**: the upstream context provides, the downstream consumes.

The `Type` column **must** follow this exact grammar — a downstream tool parses the string to visualize the map, so spelling, capitalisation, and spacing matter:

```
<Pattern Name> (<CODE>)  [ U:<CODE> D:<CODE> ]
```

Classify each edge using the **canonical DDD context-mapping patterns** (from the theory, not an ad-hoc list):

| Pattern | Code | Meaning |
|---|---|---|
| Open Host Service | OHS | upstream exposes a stable public interface |
| Published Language | PL | shared, well-documented interchange format |
| Anti-Corruption Layer | ACL | downstream translates to protect its own model |
| Conformist | CF | downstream accepts upstream's model as-is |
| Customer-Supplier | CS | downstream needs feed upstream planning |
| Shared Kernel | SK | both contexts share a subset of the model |
| Partnership | P | both contexts succeed or fail together |
| Separate Ways | SW | deliberately no integration |

Two accepted `Type` forms:
1. **A single pattern standalone** — e.g. `Open Host Service (OHS)` or `Conformist (CF)`. Use when one pattern characterises the whole edge.
2. **A relationship pattern plus per-side roles** — e.g. `Customer-Supplier (CS) U:OHS D:ACL` or `Customer-Supplier (CS) U:OHS D:CF`. Use when upstream and downstream each implement a distinct integration role.

Use `Clarity` for confidence (`-` when unset, or `assumed` / `confirmed` / `needs review`). If you can't tell which pattern applies, put `-` in `Clarity`, describe the interaction plainly in `Notes`, and don't guess at a pattern label. Fill the `## Summary` counts from what you produced.

**Merging:** if `context-map.md` already exists, merge into it — add newly discovered contexts and relationship rows, renumber consistently, recompute the `## Summary`. Do not silently drop existing rows; if a new source contradicts an existing relationship, keep both and flag the conflict for human review.

## Re-analysis: adding a source later

Analyzing a second (or third…) discovery source is a **merge-in-place**, never a rebuild. Existing content stays stable; you only add what's new. Per artifact:

- **Glossary** — insert new terms at their alphabetical position; existing rows are untouched. The only edit to an existing row is extending its `Context` column when a known term now appears in a new context with the same meaning, or adding a new row (+ `⚠` flag) when the meaning diverges.
- **Context files** — open only the contexts the new source actually touches: extend Behaviour, add Participants/Concepts as needed. Untouched contexts are left alone. A genuinely new context is a new file. Never touch the Tactical model section.
- **Context map** — add new contexts and relationship rows, then renumber the `#` column and recompute the `## Summary`. This is the only artifact where existing rows change (their `#` index), and it's cosmetic — identity is the Upstream/Downstream pair, not the number.
- **Analysis record** — always a new file (`docs/domain/stories/<source-name>.analysis.md`), one per source; never edited to fold in another source.
- **CLAUDE.md "Domain at a glance"** — regenerated from the merged artifacts (see Finalize).

Aim for the smallest correct diff: don't reformat, re-sort, or renumber anything the new source didn't affect (except the context-map `#`/Summary, which must stay consistent).

## Not part of discovery: user stories

Discovery and extraction stop at the domain model. **Do not derive user stories, acceptance scenarios, or Gherkin from a discovery source** — describing stories is a separate, decoupled session (the `gherkin-story-authoring` skill), driven by product goals rather than by the discovery output. A discovery-analysis skill never writes `.feature` files or seed scenarios.

## Invariants (hold regardless of discovery method)

- **Candidates, not decisions.** Bounded contexts are proposals for human review, never finalized here.
- **No invention.** Only record participants, concepts, and interactions present in the source.
- **Empty tactical model.** Never pre-populate aggregates/entities/value objects.
- **Ubiquitous language is sacred.** Preserve the source's exact terms; flag inconsistencies, never silently unify or rename.
- **Strict on boundaries, permissive on drafts.** Boundary mistakes are expensive. If unsure about a context split, ask the human. For glossary phrasing, context descriptions, and a clearly-correct relationship label, proceed and let the human correct on review.

## Finalize: update CLAUDE.md

**This contract is the single owner of the `## Domain at a glance` section in `CLAUDE.md`.** No other skill writes or regenerates it — `init-project` only scaffolds an empty placeholder. Regenerate it here after every discovery session so it always reflects the current artifacts.

Read all context files in `docs/domain/contexts/`, the glossary, and `docs/domain/context-map.md`, then rewrite the section with a 3–5 line summary covering: what the system does, who the actors are, the bounded contexts by name, and the core workflow as a short flow. End with a pointer to `docs/domain/` for the full model. If the section does not exist, add it after `## Where things live` (or after `## Tech stack` if that section doesn't exist). If it exists, replace it in place.

Finally, summarize what was produced and where in 5–10 lines, and call out anything that needs human review.
