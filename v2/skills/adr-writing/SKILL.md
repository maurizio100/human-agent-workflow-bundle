---
name: adr-writing
model: sonnet
description: Capture architectural decisions as lightweight, consistent Architecture Decision Records (ADRs) in docs/adr/, following a context/decision/consequences structure with sequential numeric IDs. Use this skill whenever the user wants to record a decision, says "let's write an ADR", says "this needs to be documented as a decision", surfaces an architectural learning during PR review, or mentions a choice that should be remembered (e.g., "we decided to use X because Y"). Trigger this even when the user just says "we should write this down" in an architectural context.
allowed-tools: Read Edit Write Bash
---

# ADR Writing

## What this skill does

Creates and maintains Architecture Decision Records in `docs/adr/`. ADRs are short, immutable, timestamped records of architectural choices and their rationale. They are the project's memory: when someone (human or agent) asks "why did we do it this way?" six months from now, the answer lives here.

## What this skill does NOT do

- It does not record every choice. Trivial decisions (variable names, file organization within a module) do not get ADRs.
- It does not edit ADRs after they're accepted. ADRs are immutable. To change a decision, write a new ADR that **supersedes** the old one.
- It does not duplicate content from arc42 chapters. ADRs capture the *decision moment*; arc42 chapters describe the *current state*. They link to each other.

## When to write an ADR

Write an ADR when **all** of these are true:

1. **There was a real choice.** Multiple options were considered, and the decision could reasonably have gone the other way.
2. **It's architectural.** It affects more than one component, or it sets a precedent that future work will follow.
3. **It's not obvious.** Six months from now, someone reading the code will wonder "why this and not that?"
4. **It's stable.** It's not a temporary workaround; it's an intended state.

If any of those is false, do not write an ADR. Document the decision in a code comment, a chapter of arc42, or a PR description instead.

Examples of good ADR topics:
- "Use eventual consistency between Order and Inventory contexts"
- "Adopt PostgreSQL JSONB for the audit log instead of a separate document store"
- "Authenticate to the partner API via mTLS rather than OAuth"

Examples of things that should NOT be ADRs:
- "Name the discount class `DiscountCalculator`"  (code comment)
- "Use Spring Boot"  (Solution Strategy chapter)
- "Quick fix: hard-code the tax rate until configuration is in place" (TODO + ticket)

### Tactical DDD choices: when they earn an ADR

Every story that touches a bounded context adds or modifies aggregates, entities, value objects, or domain services. Those additions are documented in the context file by `implement-story` — **they are not ADRs by default**. An ADR for every new value object would flood `docs/adr/` with noise and defeat the purpose of the folder.

A tactical choice earns an ADR only when it passes the same four tests above, with particular attention to test #1 (there was a real choice) and #3 (it's not obvious). Concretely:

- **ADR-worthy**: "We modeled Discount as a value object rather than an entity, even though it has a database ID, because its identity is defined by its value not its row." This is a real choice between two defensible options with downstream consequences.
- **ADR-worthy**: "We split Order into Cart and Order aggregates after story 4 revealed the invariants are incompatible." This is a reversal of an earlier decision.
- **NOT ADR-worthy**: "We added a `Money` value object with amount and currency." This is routine — the context file entry is enough.
- **NOT ADR-worthy**: "We added a `LineItem` entity belonging to Order." Routine tactical modeling.

When in doubt, prefer the context file entry. An ADR can always be written later if the choice turns out to be contested. Writing an ADR preemptively for every tactical decision makes the ADR folder unusable.

## Before you draft

Spawn the `adr-researcher` subagent with the decision topic and the relevant arc42 chapters
(use the References guidance below to select them). It returns the next ADR ID, related
existing ADRs, and key context from the architecture documentation.

Wait for the research summary before drafting.

## Human gate

Draft the complete ADR in your response and wait for explicit human approval before writing `docs/adr/NNNN-slug.md` or updating `docs/arc42/09-decisions.md`.

## File format

```
docs/adr/NNNN-kebab-case-title.md
```

Where `NNNN` is zero-padded to 4 digits, sequential, never reused. Use the number returned by the script.

## ADR template

Every ADR follows this exact structure. No deviations.

```markdown
# ADR-NNNN: <Short noun phrase describing the decision>

## Status
<one of: Proposed | Accepted | Superseded by ADR-MMMM | Deprecated>

## Date
YYYY-MM-DD

## Context
<2-6 sentences describing the situation that forced a decision. What changed?
What are the constraints? What forces are at play? Do not state the decision
here — only the situation that led to needing one.>

## Decision
<1-3 sentences stating, plainly, what was decided. Use active voice: "We
will use X." Not "X might be used." Decisions are commitments.>

## Consequences
<Bullets describing what becomes true as a result. Include both the good
(why we did this) and the bad (what we're giving up or taking on). An ADR
that lists only positives is hiding something.>

### Positive
- ...
- ...

### Negative
- ...
- ...

### Neutral
- ...

## Alternatives considered
<For each option that was on the table but not chosen, one sentence on
what it was and one sentence on why it was rejected. This is the section
that future readers will care about most — it tells them which paths
have already been explored and why they were closed.>

- **Option A**: <description>. Rejected because <reason>.
- **Option B**: <description>. Rejected because <reason>.

## References
<Links to related ADRs, arc42 chapters, external documents, issues, or
discussions. Optional but encouraged.>

- arc42: docs/arc42/...
- Related: ADR-NNNN
```

### References guidance

Pick only the chapters that genuinely bear on the decision — not all of them every time:

| Chapter | Link | Use when |
| --- | --- | --- |
| Solution Strategy | `docs/arc42/04-solution-strategy.md` | Cross-cutting strategic choices, quality tradeoffs |
| Building Blocks | `docs/arc42/05-building-blocks.md` | Decision affects component or module boundaries |
| Runtime | `docs/arc42/06-runtime.md` | Decision involves async flows, integration patterns, or system behavior |
| Foreign Systems | `docs/arc42/03-context.md` | Decision involves an external system (auth provider, notifications, supplier) |
| Quality Scenarios | `docs/arc42/10-quality.md` | Decision is primarily driven by a quality requirement |

## Status lifecycle

- **Proposed**: written but not yet agreed. The decision is on the table for discussion.
- **Accepted**: agreed and in effect. The default state for an ADR that's been merged.
- **Superseded by ADR-MMMM**: a newer ADR replaced this one. The old ADR remains in the repo, with its status updated to point at the new one. The old ADR's content is *not* edited beyond the status line.
- **Deprecated**: no longer in effect, but not directly replaced. Rare.

When superseding an ADR:
1. Write the new ADR with its own number.
2. In the new ADR's "Context" section, briefly note what the old ADR was and why it's being replaced.
3. Edit *only* the "Status" line of the old ADR to read `Superseded by ADR-MMMM`. Leave the rest untouched.

## Naming

Titles are short noun phrases describing the decision, not the question. Good: "Use mTLS for partner API authentication." Bad: "How should we authenticate to the partner API?"

Avoid passive titles ("Authentication approach for partner API"). Avoid vague titles ("Authentication"). The title should be readable in a list of 50 ADRs and tell the reader what was decided without opening the file.

## Maintaining the index

`docs/arc42/09-decisions.md` is the index of all ADRs. After creating or superseding an ADR:

1. Add or update the entry in the index.
2. Format: `- [ADR-NNNN: Title](../adr/NNNN-slug.md) — <Status> — <layer>[, <context>]`
   - `<layer>` is `backend`, `frontend`, or `fullstack`.
   - `<context>` is the bounded context name (e.g. `Catalog`, `Preference`). Only include it when the ADR is scoped to a specific context. Omit it for cross-cutting decisions.
3. Sort by ADR number, ascending.

## When to push back

Ask the human before writing if:
- The proposed ADR doesn't pass the four "when to write" tests above (it might be a code comment or an arc42 update instead)
- The "Decision" section can't be stated in 1–3 sentences (the decision is probably actually multiple decisions; write multiple ADRs)
- There are no "Alternatives considered" — if no alternative was on the table, there wasn't really a decision; document it elsewhere

For everything else (phrasing, level of detail in Consequences, what to put in References), proceed and let the human edit before merge.

## Common failure modes to avoid

- **Retrofitting ADRs.** Writing an ADR for a decision made months ago, when nobody remembers the alternatives. The result is a document that says "we use X" with no real Context or Alternatives. Better to skip it and update arc42 instead.
- **ADR for a non-decision.** "We will follow standard REST conventions." This isn't a decision; it's a default. Don't write an ADR for it.
- **ADR as a design document.** ADRs are decision records, not designs. If the file is more than ~150 lines, it's probably a design document in disguise. Move the design content to an arc42 chapter and keep the ADR as a thin record of the choice.
- **Hidden negatives.** Every real decision has tradeoffs. An ADR with no negative consequences is either trivial or dishonest.
