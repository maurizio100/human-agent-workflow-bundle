# Context Map

## Bounded Contexts

<!-- One numbered entry per candidate context. The heading is the context
     name (the ubiquitous-language term). The blockquote is a 1-2 sentence
     description in the domain's own words, derived from the analyzed source. -->

### 1. <ContextName>
> <One or two sentences describing what this context is responsible for.>

### 2. <ContextName>
> <Description.>

---

## Relationships

<!-- One row per pair of candidate contexts that interact (an interaction or a
     dependency crosses the boundary). Direction is Upstream -> Downstream:
     the Upstream context provides, the Downstream context consumes.

     The Type column MUST follow this exact grammar (a downstream tool parses it):

         <Pattern Name> (<CODE>)  [ U:<CODE> D:<CODE> ]

     i.e. a full pattern name, then its CODE in parentheses, optionally followed
     by a space and per-side role codes "U:<upstream> D:<downstream>". Keep the
     spelling, capitalisation, and spacing exactly as below.

     Canonical DDD context-mapping patterns and their CODES:
       Open Host Service (OHS)      -- upstream exposes a stable public interface
       Published Language (PL)      -- shared, well-documented interchange format
       Anti-Corruption Layer (ACL)  -- downstream translates to protect its model
       Conformist (CF)              -- downstream accepts upstream's model as-is
       Customer-Supplier (CS)       -- downstream needs feed upstream planning
       Shared Kernel (SK)           -- both contexts share a subset of the model
       Partnership (P)              -- both contexts succeed or fail together
       Separate Ways (SW)           -- deliberately no integration

     Two accepted forms for the Type value:
       1. A single pattern used standalone, e.g. "Open Host Service (OHS)" or
          "Conformist (CF)" -- use when one pattern characterises the whole edge.
       2. A relationship pattern plus per-side roles, e.g.
          "Customer-Supplier (CS) U:OHS D:ACL" or
          "Customer-Supplier (CS) U:OHS D:CF" -- use when upstream and downstream
          each implement a distinct integration role.

     Clarity: confidence in this relationship. Use "-" when unset, or a note
     like "assumed", "confirmed", "needs review". Leave "-" if you are unsure
     rather than guessing.

     Notes: short rationale, or "New"/"Future" markers for relationships that
     do not exist yet in the current source but are anticipated. -->

| # | Upstream | Downstream | Type | Clarity | Notes |
|---|----------|------------|------|---------|-------|
| 1 | <ContextName> | <ContextName> | Open Host Service (OHS) | - | <why they interact> |
| 2 | <ContextName> | <ContextName> | Customer-Supplier (CS) U:OHS D:ACL | - | <why they interact> |

---

## Summary

- **Total Bounded Contexts:** <n>
- **Total Relationships:** <n>
- **Relationship Breakdown:** <e.g. Open Host Service: 23, Customer-Supplier: 4, Conformist: 1>
