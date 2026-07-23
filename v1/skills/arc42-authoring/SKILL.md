---
name: arc42-authoring
description: Design, extend, and maintain arc42 architecture documentation in Markdown. Supports three operations: designing new chapters from scratch collaboratively, extending or editing existing chapters with new sections or content, and targeted mid-story edits invoked from implement-story. Use this skill whenever the user wants to draft, review, extend, or update architecture documentation, add a new chapter, add a section to an existing chapter, design a target architecture, capture quality attributes, document a runtime workflow, describe foreign systems, or discuss test strategy at the architecture level. Trigger this even when the user just says "let's think about the architecture", "we need to document how X talks to Y", "add deployment to our docs", or "extend the Building Blocks chapter" — all of those are architecture work.
allowed-tools: Read Edit Write
---

# arc42 Authoring

## What this skill does

Helps the user **design** and **document** software architecture using the arc42 template, with Markdown files in `docs/arc42/`. Architecture written in one shot is almost always wrong in subtle ways, so the skill defaults to proposing changes incrementally and asking for human input on anything non-trivial.

The seven chapters that matter most for this workflow (the ones the agent reads during planning) are first-class. The other arc42 chapters are supported but optional.

### The three operations

The skill has three operations. Pick the right one before doing any work — they have different weights and different ceremonies.

1. **Design a chapter.** Collaborative, section-by-section authoring. Used when a chapter is being **created from scratch** or when an existing chapter is being **restructured from the ground up**. Heavy mode; not for every edit.
2. **Extend or edit a chapter.** Lighter-weight authoring on an existing chapter. Used when adding a new section to an existing chapter, appending content to an existing section, or making a substantive but scoped change. This is the mode for "let's add deployment details to the Solution Strategy" or "the Building Blocks chapter needs a new level-3 view for the payment block."
3. **Targeted edit.** The narrowest mode. Invoked *by other skills* (typically `implement-story` from the Review learnings checklist) for small, specific updates that land on a story branch. Not user-facing; if a human is invoking the skill directly, they want one of the first two operations.

### How to pick the operation

Walk these questions in order. First "yes" wins.

1. Is the user asking to create a brand-new chapter, or to restructure an existing one from the ground up? → **Design a chapter.**
2. Is the invocation coming from `implement-story` mid-story? → **Targeted edit.**
3. Otherwise, the user wants to add to or modify an existing chapter. → **Extend or edit a chapter.**

## What this skill does NOT do

- It does not write architecture in isolation. Every non-trivial decision is offered for human input.
- It does not produce diagrams. If a diagram is needed, the skill describes what it should show and suggests a format (typically Mermaid or Structurizr DSL); the user creates it.
- It does not write code or define APIs. It defines the *shape* of the system, not the implementation.
- It does not capture point-in-time decisions. Those go in ADRs (`adr-writing` skill), which the relevant arc42 chapter then references.

## File layout

```
docs/arc42/
  01-introduction.md      # Goals, stakeholders, requirements overview
  02-constraints.md       # Technical, organizational, conventions
  03-context.md           # ★ core (System scope, external actors, foreign systems detail)
  04-solution-strategy.md # ★ core
  05-building-blocks.md   # ★ core (Target Architecture lives here)
  06-runtime.md           # ★ core (Workflow descriptions)
  07-deployment.md
  08-crosscutting.md      # ★ core (Test strategy, error handling, security conventions)
  09-decisions.md         # ★ core (links to docs/adr/)
  10-quality.md           # ★ core (Quality Attributes)
  11-risks.md
  12-glossary.md          # may symlink or reference docs/domain/glossary.md
```

★ = the seven chapters the agent treats as first-class. These are the ones to design with the user.

## Chapter priorities

### First-class (design collaboratively, never skip)

These chapters answer questions the planner agent will ask on every story. Get them right early.

- **Context and Scope** (`03-context.md`) — the system boundary: who is outside the system, what they do with it, and how they connect. Two logical sections: (1) a context view listing the system's actors and external systems; (2) a **Foreign Systems** subsection with operational detail for every external integration — protocol, data exchanged, authentication, SLA/availability expectations, contact for outages, and known quirks. Referenced by the planner whenever a story touches an external system.
- **Solution Strategy** (`04-solution-strategy.md`) — top-level technology and structural choices, in 1–2 pages. The "we are building a Spring Boot service with PostgreSQL, deployed to Kubernetes, integrating with X via Y." Justify each choice in one or two sentences.
- **Building Blocks / Target Architecture** (`05-building-blocks.md`) — the system's internal decomposition. At minimum: a level-1 view (the system as a black box with its neighbors) and a level-2 view (the system broken into its main building blocks). Each building block gets a name, a responsibility, and an interface description. No code, no schemas — *responsibilities and interfaces*.
- **Runtime / Workflow descriptions** (`06-runtime.md`) — the most important runtime scenarios, described as sequences. One sub-section per scenario. Cover the happy paths first; come back for error and edge scenarios after the happy paths are stable.
- **Crosscutting Concepts** (`08-crosscutting.md`) — concerns that apply across the entire system. The primary subsection for this workflow is **Test Strategy**: what is tested at each level, which tools are used, how acceptance tests derive from Gherkin stories, what test environments exist, and what coverage is expected. Additional crosscutting concerns (error handling, logging, security conventions) are added as they emerge. Read by the `implement-story` skill during the Write Tests step.
- **Decisions** (`09-decisions.md`) — index of ADRs from `docs/adr/`. The skill maintains this index but does not write ADR content; that's the `adr-writing` skill.
- **Quality Attributes** (`10-quality.md`) — measurable, testable quality requirements. Use a quality attribute scenario format: stimulus, environment, response, response measure. "Vague" quality attributes ("the system should be fast") are not acceptable; rewrite them as scenarios ("under 500 concurrent users, p95 response time for the search endpoint is under 300ms").

### Skippable (write only when needed)

The other arc42 chapters are *available* but should not be created proactively. Write them when the user explicitly asks, or when their absence is causing real confusion. A small project may never need `07-deployment.md` or `11-risks.md`; that's fine.

When the user asks to skip a chapter, do not silently ignore it. Note in the chapter file that it was deliberately skipped, so future readers don't think it was forgotten.

## Operation: Design a chapter

Design mode is for creating a new chapter or restructuring an existing one from the ground up. It is the heaviest of the three user-facing operations. Do not use it for small additions — use "Extend or edit a chapter" for those.

Run this loop:

1. **Ask what already exists.** Before writing anything, check whether a draft of this chapter already exists. If it does, read it. (If the user is restructuring, read the current version to understand what's being replaced.)
2. **Propose a structure.** Offer the section structure for the chapter (e.g., for Building Blocks: "Level 1 — system context, Level 2 — main building blocks, Level 3 — only for blocks that need it"). Wait for the user to approve or adjust.
3. **Propose content section by section.** For each section, draft 5–15 lines of content and ask for feedback. Do not produce a full chapter draft in one go.
4. **Capture decisions as you go.** Whenever a section requires a real choice (e.g., "we'll use eventual consistency for X"), pause and ask whether this decision warrants an ADR. If yes, hand off to the `adr-writing` skill — the chapter then *references* the ADR rather than restating it.
5. **Mark uncertainty explicitly.** If a section depends on something not yet decided, write `> TODO: depends on decision about X` rather than guessing. The TODOs are the agenda for the next session.

Design mode is a conversation, not a one-shot generation. Expect it to take multiple turns per chapter.

---

## Operation: Extend or edit a chapter

Extend mode is for adding to or modifying an **existing** chapter. It's lighter than design mode — no section-structure proposal, no ceremony about laying out the chapter from scratch — because the chapter already exists and you're just making it more complete.

Use this mode when:
- Adding a new section to a chapter that already has other sections.
- Appending content to an existing section (a new quality attribute, a new building block, a new foreign system entry, another runtime scenario).
- Revising an existing section's content without changing its purpose.
- Adding level-3 detail under a level-2 building block that already exists.

Do **not** use this mode for:
- Creating a chapter that doesn't yet have a file — that's design mode (preceded by adjust-focus if the chapter wasn't in focus).
- Completely restructuring a chapter — that's design mode on an existing file.
- Small edits triggered by the TDD loop's Review checklist — that's targeted-edit mode.

### The extend loop

1. **Read the current chapter.** Load the whole file. Understand the existing structure before proposing changes.
2. **Ask what the user wants to add or change.** Specific section? General area? A new section? A rewrite of an existing one? Get explicit intent before writing.
3. **Propose the change.** Write the addition or modification. For additions, show where in the chapter structure it lands. For modifications, show before/after. Keep the proposal scoped — don't quietly rewrite unrelated sections.
4. **Offer to capture decisions.** If the addition involves a real choice that passes the ADR-worthiness tests, pause and offer to write an ADR via `adr-writing`. Most extend-mode changes do *not* warrant an ADR — extend mode is for filling in known territory, not for making new decisions.
5. **Check for knock-on updates.** When a chapter is extended, related chapters sometimes need small updates too. A new Building Block often means a new Runtime scenario that uses it. A new Quality Attribute often means a new test strategy entry. Ask the user whether any related chapter needs a corresponding update — but do not make those updates silently.
6. **Commit the change.** Present the diff, let the user confirm, write the file.

### When extend mode should become design mode

Sometimes what starts as "let me just add a section" turns into "actually, this whole chapter needs to be rethought." When that happens:

- If the user explicitly asks for a restructure, switch to design mode.
- If the proposed addition contradicts the chapter's existing structure in a way that can't be resolved with a local edit, flag it and ask: "This addition doesn't fit cleanly into the current structure. Do you want to restructure the chapter (design mode) or should I fit the addition into the existing shape (extend mode, with some awkwardness)?"

Don't silently slide from extend mode into design mode — the user should know they've committed to the heavier operation.

---

## Operation: Targeted edit (invoked by other skills)

When `arc42-authoring` is triggered *from within* a story branch (specifically, when `implement-story`'s Review learnings checklist discovered an architectural learning that needs to land in an arc42 chapter), the skill operates in **targeted-edit mode**. This is the narrowest of the four operations and is not user-facing — users should use extend mode for similar-sounding but larger changes.

Targeted-edit mode rules:

- The scope is narrow: one specific change, identified by the learning that triggered the skill.
- No collaborative back-and-forth. Make the edit, present the diff, commit on the story branch.
- The edit is reviewed together with the implementation PR, not as a separate session.
- If the mid-story edit reveals that a bigger design conversation is needed ("this learning suggests our whole Building Blocks view is wrong"), do not attempt that conversation inline. Flag it, make the minimal edit needed for *this* story to ship, and note that a follow-up design-mode session is needed.

The distinction between the modes is about **ceremony weight**: design mode has the most, extend mode has moderate, targeted-edit has the least. Pick the lightest mode that fits the actual change.

## Quality bars

Each first-class chapter has a minimum bar before it counts as "done enough to use":

- **Context and Scope**: context view present with all external actors listed; every foreign system entry has protocol, auth, and contact for outages
- **Solution Strategy**: less than 2 pages, every technology choice has a one-sentence justification
- **Building Blocks**: at least levels 1 and 2; every block has a stated responsibility
- **Runtime**: at least the top 3 scenarios for the system, in sequence form
- **Crosscutting Concepts**: Test Strategy subsection present; every test level has a stated tool and scope
- **Decisions index**: every ADR file in `docs/adr/` is listed
- **Quality Attributes**: at least 5 testable scenarios, no vague adjectives

Below the bar = the chapter exists but is not yet usable. Above the bar = the agent can rely on it during planning. Track this state in the chapter's first line: `> Status: draft | usable | stable`.

## Keeping the documentation alive

The biggest failure mode of arc42 is "write once, never update." Counter this with two habits:

1. **Spec drift feedback** — the workflow's Review→Spec feedback edge feeds learnings back into these chapters. When the user surfaces a learning during PR review, ask which chapter it affects and update it.
2. **ADR backflow** — when the `adr-writing` skill creates a new ADR, ask whether any first-class chapter needs to reference it. Usually yes.

## When to push back

Ask before proceeding if:
- The user wants to write a Quality Attribute that has no testable measure
- The user wants to add a Building Block whose responsibility overlaps with an existing one (the model is drifting)
- The user wants to skip a first-class chapter for a non-trivial project (small projects can skip; complex ones cannot)
- The user wants to put a decision in a chapter rather than in an ADR (decisions belong in ADRs; chapters reference them)

For everything else — phrasing, section ordering inside a chapter, choice of diagram format — proceed and let the user correct.
