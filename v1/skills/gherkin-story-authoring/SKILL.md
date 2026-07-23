---
name: gherkin-story-authoring
description: Author and refine Gherkin user stories as .feature files with proper IDs, epic grouping, declarative steps, and acceptance criteria suitable for triggering an agent-driven TDD loop. Use this skill whenever the user wants to write a new user story, promote a seed scenario from domain analysis into a real story, refine an existing story, group stories into epics, or split a story that's too large. Trigger this even when the user says "let's write a story" or "draft a feature file" without naming Gherkin explicitly. Use this skill whenever a .feature file needs to be created or edited.
model: sonnet
allowed-tools: Read Edit Write Bash
---

# Gherkin Story Authoring

## What this skill does

Produces and maintains `.feature` files in `specs/stories/` and epic descriptions in `specs/epics/`. Stories produced by this skill are the **trigger** for the agent's TDD execution loop — they need to be unambiguous enough that the planner can derive a test plan from them without guessing.

## What this skill does NOT do

- It does not invent domain language. It uses terms from `docs/domain/glossary.md` and flags missing terms back to the `domain-storytelling` skill.
- It does not write step definitions. That's an implementation concern handled in the TDD loop.
- It does not estimate stories or assign them to sprints. Pure authoring.

## What to read before authoring

Spawn the `domain-reader` subagent with the bounded context name(s) relevant to the story
being authored. It reads the glossary, context file(s), and relationships and returns a
domain summary.

Wait for the summary before writing anything. If the story crosses more than one context,
pass all relevant context names so the subagent reads them together.

## Conventions

### File naming and IDs

- Stories: `specs/stories/STORY-NNN-kebab-case-title.feature` where `NNN` is zero-padded to 3 digits.
- Epics: `specs/epics/EPIC-NNN-kebab-case-title.md`.
- IDs are sequential and never reused. Find the highest existing ID in the folder and use the next one.
- The kebab-case title in the filename is a slug; the human-readable title lives in the file's `Feature:` line.

### Structure of a `.feature` file

```gherkin
# STORY-042
# Epic: EPIC-007
# Layer: frontend | backend | fullstack
# Context: <bounded context name, or "—" if cross-cutting>
# Status: draft | ready | in-progress | done

Feature: Add customer discount at checkout
  As a cashier
  I want to apply a discount to a customer's order
  So that loyalty customers see their reduced price before paying

  Background:
    Given a customer with a loyalty card
    And an order containing at least one discountable item

  Scenario: Discount is applied to a single eligible item
    When the cashier scans the loyalty card
    Then the order total is reduced by the discount amount
    And the receipt shows the discount line

  Scenario: Discount does not apply to non-eligible items
    Given the order also contains a non-discountable item
    When the cashier scans the loyalty card
    Then only the eligible item's price is reduced
    And the non-eligible item's price is unchanged

  Scenario Outline: Discount tiers based on customer status
    Given the customer has loyalty status "<status>"
    When the cashier scans the loyalty card
    Then the discount percentage is "<percent>"

    Examples:
      | status | percent |
      | bronze | 5       |
      | silver | 10      |
      | gold   | 15      |
```

The header comments (`# STORY-042`, `# Epic: ...`, `# Status: ...`) are not standard Gherkin but they're tolerated by parsers and they keep metadata next to the content. Use them.

## Status lifecycle

Every story carries a status that reflects where it is in the workflow. The states and the transitions between them are:

```
          (created)                                    (planner sends back)
              │                                                 │
              ▼                                                 │
           draft ──── (human approves) ────► ready              │
              ▲                                │                │
              │                                │                │
              │                       (branch created,          │
              │                        tdd-loop starts)         │
              │                                │                │
              │                                ▼                │
              └──────────────────────── in-progress ◄───────────┘
                                               │
                                               │ (PR merged)
                                               ▼
                                              done
```

And the terminal side-state, for split stories:

```
any → superseded  (story split into smaller stories, original marked and kept for history)
```

### Who flips the status

Each transition is owned by exactly one skill. No skill flips a status it doesn't own.

| Transition | Owned by | When |
|---|---|---|
| *(none)* → `draft` | `gherkin-story-authoring` | On story creation from a seed scenario |
| `draft` → `ready` | `gherkin-story-authoring` | **On explicit human approval only.** The skill does not self-promote stories. |
| `ready` → `in-progress` | `tdd-loop-with-github` | At the branch-creation step, before any code is written |
| `in-progress` → `done` | `tdd-loop-with-github` | After the PR is merged (observed on the next agent run) |
| `in-progress` → `draft` | `tdd-loop-with-github` | When the planner hands back for story refinement |
| any → `superseded` | `gherkin-story-authoring` | When the story is split |

### The draft → ready gate

**This is a human gate, not an automated check.** The skill can verify that the quality bar is met (all terms in glossary, no technical leakage, right size, at least one negative scenario, etc.), but passing the quality bar is necessary, not sufficient. A story only becomes `ready` when the human explicitly says "this story is ready for implementation."

When the human asks the skill to promote a story to `ready`:

1. Run the quality checks first. If any fail, report what's wrong and stay at `draft`.
2. If the checks pass, ask the human for explicit confirmation: "Story STORY-NNN passes the quality checks. Mark as ready for implementation?"
3. Only on explicit confirmation, update the `# Status:` line.

This matches the pattern of the workflow's other human gates (Plan, Review, Merge): humans approve transitions, agents execute them.

### Status updates are commit-worthy

When a skill flips a status, it does so as a real edit to the `.feature` file, committed with a clear message (e.g. `docs: mark STORY-042 as ready`). The `.feature` file is the source of truth.

**Also update the index** in the same commit: `cd "$(git rev-parse --show-toplevel)" && python3 .claude/skills/gherkin-story-authoring/story-index.py update-status STORY-NNN <new-status>`. The index must stay in sync with the `.feature` files.

## How to write good Gherkin

These are the rules. Follow them; they are the difference between executable specifications and decorative ones.

### Use ubiquitous language from the glossary

Every noun and verb in the story should either already exist in `docs/domain/glossary.md` or be a candidate for addition. If you find yourself reaching for a synonym ("client" when the glossary says "customer"), stop and use the glossary term. If a needed term is not in the glossary, add a note at the end of the story file: `# Glossary: needs term "X"` and continue. This becomes feedback for the `domain-storytelling` skill.

### Declarative, not imperative

A scenario describes **what** the user accomplishes, not **how** the UI works. Bad: "When the cashier clicks the loyalty button and types the card number and presses Enter." Good: "When the cashier scans the loyalty card." If the test later needs to drive a UI, that's the step definition's problem, not the story's.

### One behavior per scenario

A scenario tests one behavior. If you find yourself writing a scenario with three `Then` clauses that test different things, split it. Multiple `Then` clauses are fine when they describe one cohesive outcome ("the order total is reduced AND the receipt shows the discount line"); they're not fine when they describe two unrelated outcomes.

### Background sparingly

Use `Background` only for setup that *every* scenario in the file needs. If half the scenarios need different setup, do not put it in Background; put it in those scenarios as `Given`.

### Scenario Outline for true variation, not for laziness

Use `Scenario Outline` when the same logic applies to a parameter set (discount tiers, validation rules, currency conversions). Do not use it just to combine scenarios that happen to have similar structure but test different things.

### Independent scenarios

Each scenario must be runnable in isolation. No "this scenario continues from the previous one." If two scenarios need shared state, that state goes in Background or in the test fixtures, not in execution order.

### No technical details

Stories do not mention databases, API endpoints, HTTP status codes, frameworks, libraries, or file formats. If a story does, it has leaked into solution space and needs rewriting.

### Right size

A story should be implementable in roughly one TDD loop iteration — typically 2–6 scenarios, deliverable in a few hours to a day. If a story has more than ~8 scenarios or covers multiple distinct behaviors, split it. The split usually falls naturally: each cluster of 2–4 related scenarios becomes its own story. Group the resulting stories under a shared epic.

## Promoting a seed scenario from domain analysis

When `domain-storytelling` produces seed scenarios in `docs/domain/stories/<name>.analysis.md`, promote them like this:

1. Read the seed.
2. Pick the next available STORY ID.
3. Decide the epic (existing or new).
4. Expand the seed:
   - Add the `Feature:` description (As a / I want / So that)
   - Add Background if needed
   - Add the missing scenarios (the seed is usually one happy path; you need at least one negative or edge case)
   - Add Scenario Outlines for any parameterized variation
5. Verify every term is in the glossary; flag missing terms.
6. Pick the next available ID: `cd "$(git rev-parse --show-toplevel)" && python3 .claude/skills/gherkin-story-authoring/story-index.py next-id`
7. Write to `specs/stories/STORY-NNN-<slug>.feature` with `# Status: draft`.
8. Add to the index: `cd "$(git rev-parse --show-toplevel)" && python3 .claude/skills/gherkin-story-authoring/story-index.py add STORY-NNN <epic> "<title>" <context> <layer> draft`
9. Mark the seed as promoted in the analysis file.
10. The story stays at `draft` until the human explicitly approves it for implementation (see Status lifecycle above).

## Splitting an existing story

When the `tdd-loop-with-github` planner reports a story is too large (the "story refinement" feedback edge):

1. Read the story.
2. Identify the natural split — usually behaviors that share Background but have independent scenarios.
3. Create new stories with new IDs (use `cd "$(git rev-parse --show-toplevel)" && python3 .claude/skills/gherkin-story-authoring/story-index.py next-id`). Do not reuse the original ID; mark the original as superseded.
4. Group the new stories under the same epic (or a new epic if the split reveals a larger structure).
5. Add rows for the new stories (`cd "$(git rev-parse --show-toplevel)" && python3 .claude/skills/gherkin-story-authoring/story-index.py add ...`) and update the original (`cd "$(git rev-parse --show-toplevel)" && python3 .claude/skills/gherkin-story-authoring/story-index.py update-status STORY-NNN superseded`).
6. In the original file, replace the content with a header noting the split and the new IDs:

```
# STORY-042
# Status: superseded
# Split into: STORY-051, STORY-052, STORY-053
```

Do not delete the original file. The trail matters.

## Epics

An epic is a thin Markdown file in `specs/epics/`:

```markdown
# EPIC-007: Loyalty discounts

## Goal
Loyalty customers see and receive their tier-based discount during checkout.

## Stories
- STORY-042: Add customer discount at checkout
- STORY-043: Configure discount tiers
- STORY-044: Audit log of applied discounts

## Out of scope
- Loyalty enrollment (covered by EPIC-005)
- Discount on subscriptions (separate epic, future)
```

Epics are flat. Don't nest them. If you find yourself wanting to, you probably want a milestone instead.

## When to push back

Ask the human before writing if:
- The seed scenario references a term that isn't in the glossary and you can't tell whether it's a new domain concept or a slip
- The seed describes something that crosses bounded contexts (it might need to be two stories, one per context)
- You can't write a meaningful negative or edge case because the seed is too vague about what "wrong" looks like

For everything else (phrasing, scenario count, Background placement), make the call and let the human correct.
