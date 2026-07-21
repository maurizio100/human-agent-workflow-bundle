---
name: gherkin-story-authoring
description: Author and refine Gherkin user stories as GitHub issues with proper IDs, epic grouping, declarative steps, and acceptance criteria suitable for triggering an agent-driven TDD loop. Use this skill whenever the user wants to write a new user story from a product goal or feature request, refine an existing story, group stories into epics, or split a story that's too large. Trigger this even when the user says "let's write a story" or "draft a feature file" without naming Gherkin explicitly. Use this skill whenever a story's Gherkin needs to be created or edited.
model: sonnet
allowed-tools: Read Edit Write Bash
---

# Gherkin Story Authoring

## What this skill does

Produces and maintains **GitHub issues** whose body holds the story's Gherkin, grouped by epics that live as GitHub milestones. The issue is the single source of truth for the story's spec content (ADR-0021) — there is no `.feature` file. Stories produced by this skill are the **trigger** for the agent's TDD execution loop — they need to be unambiguous enough that the planner can derive a test plan from them without guessing.

## What this skill does NOT do

- It does not invent domain language. It uses terms from `docs/domain/glossary.md` and flags missing terms back to the `domain-storytelling` skill.
- It does not write step definitions. That's an implementation concern handled in the TDD loop.
- It does not estimate stories or assign them to sprints. Pure authoring.

## What to read before authoring

Spawn the `domain-reader` subagent with the bounded context name(s) relevant to the story
being authored. It reads the glossary, context file(s), and the context map and returns a
domain summary.

Wait for the summary before writing anything. If the story crosses more than one context,
pass all relevant context names so the subagent reads them together.

## Conventions

### IDs and titles

- Each story is one GitHub issue titled `STORY-NNN: <human-readable title>`, where `NNN` is zero-padded to 3 digits.
- IDs are sequential and never reused. Always allocate with `story-index.py next-id` (it takes the max over existing issues **and** the legacy archives, so a superseded/closed ID is never reused). Never hand-pick an ID.
- Epics: GitHub milestones titled `EPIC-NNN: <name>` (see [Epics](#epics)).

### Structure of the issue body

The issue body is **pure Gherkin** — no classification-header comments. The story's identity and classification (`STORY-NNN`, epic, layer, context, type) live on the issue title and its `epic:` / `layer:` / `context:` / `type:` labels, applied automatically by `story-index.py create`. So the body is just:

```gherkin
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

You pass the classification (`--epic`, `--layer`, `--context`, `--type`) to `story-index.py create` as flags; the script turns them into labels and drops any stray `# STORY-NNN` / `# Epic:` header lines from the body. **Status is not passed in:** every story starts as `status:draft` and later transitions go through `gh-status` (see [Story state lives on the issue](#story-state-lives-on-the-github-issue)).

## Status lifecycle

Every story carries a status that reflects where it is in the workflow. **The status lives on the GitHub issue** — as a `status:` label plus the open/closed state — and nowhere else. The states and the transitions between them are:

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
| *(none)* → `draft` | `gherkin-story-authoring` | On story creation |
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
3. Only on explicit confirmation, run `cd "$(git rev-parse --show-toplevel)" && python3 .claude/skills/gherkin-story-authoring/story-index.py gh-status STORY-NNN ready`.

This matches the pattern of the workflow's other human gates (Plan, Review, Merge): humans approve transitions, agents execute them.

## Story state lives on the GitHub issue

GitHub issues are the **single source of truth** for both story state and spec content (ADR-0021). Each story is one issue titled `STORY-NNN: <title>`; its `status:` label and open/closed state ARE the status, and its body IS the Gherkin. There are no story files — no `.feature`, no `# Status:` header, no `STORIES.md` index. Everything is managed through `story-index.py`; never hand-craft `gh issue` calls, and never re-create a `specs/stories/` file.

- **On creation**, compose the Gherkin body (see below), write it to a scratch file, then run:

  ```
  cd "$(git rev-parse --show-toplevel)" && python3 .claude/skills/gherkin-story-authoring/story-index.py create \
    --title "<human-readable title>" --epic EPIC-NNN --layer <layer> --context "<context or —>" --type feature \
    --body-file <scratch-file>
  ```

  It allocates the next id, creates the issue as `status:draft` with the body as content, applies `epic:` / `context:` / `layer:` / `type:` labels, attaches the epic milestone, and prints the allocated `STORY-NNN` and the issue URL. (You can pass `--body-file -` to pipe the body on stdin instead.)
- **To refine** an existing story, edit its Gherkin and run `story-index.py update-body STORY-NNN --body-file <scratch-file>` to replace the issue body. This is the only correct edit path — editing the issue in the GitHub UI works too, but going through the script keeps behaviour consistent.
- **On every status transition**, run `gh-status STORY-NNN <status>`. It swaps the `status:` label and closes the issue for terminal states (`done`, `superseded`, `cancelled`) or reopens it otherwise.
- `create` and `update-body` **require** the `gh` CLI (there is nowhere else to put the content); `gh-status` degrades gracefully if `gh` is missing.

## How to write good Gherkin

These are the rules. Follow them; they are the difference between executable specifications and decorative ones.

### Use ubiquitous language from the glossary

Every noun and verb in the story should either already exist in `docs/domain/glossary.md` or be a candidate for addition. If you find yourself reaching for a synonym ("client" when the glossary says "customer"), stop and use the glossary term. If a needed term is not in the glossary, add a comment on the story issue (`gh issue comment <number> --body 'Glossary: needs term "X"'`) and continue. This becomes feedback for the `domain-storytelling` skill.

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

## Authoring a story from a product goal

Stories originate from a **product goal or feature request** — something the product wants the system to do — not from the domain-discovery output. Discovery (`domain-storytelling` and the `domain-artifacts` model) supplies the *language and boundaries* you write within; it does not hand you scenarios. Ground each story in the domain artifacts via the `domain-reader` subagent (see [What to read before authoring](#what-to-read-before-authoring)), then:

1. Clarify the goal — what capability does the user want, and for which bounded context? If the context isn't obvious from the request, use the `domain-reader` summary to place it.
2. Decide the epic (existing or new).
3. Compose the Gherkin body (no header comments — classification goes to flags):
   - Write the `Feature:` description (As a / I want / So that) from the goal
   - Add Background if needed
   - Write the scenarios: at least one happy path **and** at least one negative or edge case
   - Add Scenario Outlines for any parameterized variation
4. Verify every term is in the glossary (from the `domain-reader` summary); flag missing terms back per [Use ubiquitous language](#use-ubiquitous-language-from-the-glossary).
5. Write the composed body to a scratch file, then create the issue (it allocates the id for you):

   ```
   cd "$(git rev-parse --show-toplevel)" && python3 .claude/skills/gherkin-story-authoring/story-index.py create \
     --title "<title>" --epic EPIC-NNN --layer <layer> --context "<context or —>" --type feature \
     --body-file <scratch-file>
   ```

   This registers the story in the backlog — the issue, created as `status:draft`, is the record. Note the `STORY-NNN` it prints.
6. The issue stays at `status:draft` until the human explicitly approves it for implementation (see Status lifecycle above).

## Splitting an existing story

When the `tdd-loop-with-github` planner reports a story is too large (the "story refinement" feedback edge):

1. Read the original issue's body.
2. Identify the natural split — usually behaviors that share Background but have independent scenarios.
3. Create a new issue per split (`story-index.py create ...`); each allocates its own new ID. Do not reuse the original ID.
4. Group the new stories under the same epic (or a new epic if the split reveals a larger structure).
5. Close the original as superseded (`cd "$(git rev-parse --show-toplevel)" && python3 .claude/skills/gherkin-story-authoring/story-index.py gh-status STORY-NNN superseded`) and record the split on it: `gh issue comment <number> --body 'Split into STORY-051, STORY-052, STORY-053'`.

The closed `superseded` issue, with its comment, is the trail — there is no file to annotate.

## Epics

An epic is a GitHub **milestone** titled `EPIC-NNN: <name>` (ADR-0021) — there is no epic file. Its description holds the epic's goal, stories, and out-of-scope notes; `story-index.py create` attaches each story to the milestone derived from its `--epic` flag, so the milestone both describes the epic and groups its stories on the board.

Create a new epic by creating its milestone, with a description in this shape:

```markdown
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

```
gh api repos/{owner}/{repo}/milestones -f title="EPIC-NNN: <name>" -F description=@<file-or-->
```

Then reference it from stories with `--epic EPIC-NNN`. Epics are flat — don't nest them.

## When to push back

Ask the human before writing if:
- The request references a term that isn't in the glossary and you can't tell whether it's a new domain concept or a slip
- The goal describes something that crosses bounded contexts (it might need to be two stories, one per context)
- You can't write a meaningful negative or edge case because the request is too vague about what "wrong" looks like

For everything else (phrasing, scenario count, Background placement), make the call and let the human correct.
