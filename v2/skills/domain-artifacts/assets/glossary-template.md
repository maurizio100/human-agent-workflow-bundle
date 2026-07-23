# Glossary

The ubiquitous language of the domain, organized by Bounded Context. Each
context has its own `## <Context>` heading and a dedicated table of terms.
Terms used with the **same meaning** in two or more contexts live once in the
`## Shared / Cross-context` table instead of being repeated. This file is
append-merged across discovery sessions.

<!-- Conventions (see the domain-artifacts contract for the full rules):

     STRUCTURE
     - `## Shared / Cross-context` — terms with ONE identical meaning across 2+
       contexts. One row per term; list the contexts in the Contexts column.
       This table has an extra Contexts column; the per-context tables do not.
     - `## <Context>` — one section per bounded context, holding the terms
       specific to that context. The context is implied by the heading, so
       these tables have NO Context column.
     - `## Unassigned` — terms not yet mapped to any context (optional; omit the
       section when empty).
     Keep context sections in alphabetical order by context name; keep Shared
     first and Unassigned last. Within each table, sort rows alphabetically by
     Term.

     COLUMNS
     Term       The term EXACTLY as written in the source — preserve casing,
                spacing, and language (e.g. German domain nouns stay German).
                Do not translate or normalise.

     Contexts   (Shared table only) The bounded contexts that share this exact
                meaning, comma-separated (e.g. "Sales, Billing").

     Definition One sentence, in the domain's own words, derived from how the
                term is actually used. Not a dictionary definition.

     Source     Provenance — which analyzed source and which numbered elements
                it appears in (e.g. "checkout §3,7" or "billing-ES: cmd-2").

     Notes      Aliases ("also called X"), see-also links to related terms, and
                review flags. When the SAME term means DIFFERENT things in
                different contexts, it is NOT shared: put one row in each
                context's own table, and cross-link them here with a flag
                (e.g. "⚠ different meaning in <OtherContext>").

     MERGE RULES
     - A term shared identically across contexts → one row in Shared; add a
       context to its Contexts column when it later appears in a new context
       with the same meaning.
     - A term whose meaning diverges per context → NOT shared. One row in each
       relevant `## <Context>` table, cross-linked via Notes. Never merge them.
     - Add new terms in alphabetical position within the right table; never
       overwrite an existing definition — resolve divergence by moving the term
       out of Shared into per-context rows (+ a Notes flag). -->

## Shared / Cross-context

Terms used with the same meaning in two or more contexts.

| Term | Contexts | Definition | Source | Notes |
|------|----------|------------|--------|-------|
| <TermB> | <ContextOne>, <ContextTwo> | <Same meaning in both contexts — one row here.> | <source §refs> | - |

## <ContextOne>

| Term | Definition | Source | Notes |
|------|------------|--------|-------|
| <TermA> | <One-sentence definition in the domain's words.> | <source §refs> | - |
| <TermC> | <Definition as used in this context.> | <source §refs> | also called <Alias>; ⚠ different meaning in <ContextTwo> |

## <ContextTwo>

| Term | Definition | Source | Notes |
|------|------------|--------|-------|
| <TermC> | <Definition as used in this other context.> | <source §refs> | ⚠ different meaning in <ContextOne> |

## Unassigned

Terms not yet mapped to a context. Omit this section when empty.

| Term | Definition | Source | Notes |
|------|------------|--------|-------|
| <TermD> | <Definition; context still to be decided.> | <source §refs> | - |
