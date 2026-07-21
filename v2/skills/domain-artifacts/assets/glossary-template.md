# Glossary

The ubiquitous language of the domain. One row per term, sorted alphabetically
by Term. This file is append-merged across discovery sessions.

<!-- Conventions (see the domain-artifacts contract for the full rules):

     Term       The term EXACTLY as written in the source — preserve casing,
                spacing, and language (e.g. German domain nouns stay German).
                Do not translate or normalise.

     Context    The bounded context(s) where the term is used. This is the
                single source of truth for a term's context membership — a
                per-context view is just this table filtered by Context.
                - Same meaning across several contexts: ONE row, list them
                  comma-separated (e.g. "ContextA, ContextB").
                - Different meaning per context: ONE ROW PER CONTEXT (same Term,
                  different Context, different Definition) — never merge them.
                Use "-" if the term is not yet assigned to a context.

     Definition One sentence, in the domain's own words, derived from how the
                term is actually used. Not a dictionary definition.

     Source     Provenance — which analyzed source and which numbered elements
                it appears in (e.g. "checkout §3,7" or "billing-ES: cmd-2").

     Notes      Aliases ("also called X"), see-also links to related terms, and
                review flags. When two sources define a term differently, keep
                both, cross-link them here, and flag: "⚠ conflicts with row N".

     Add new terms in alphabetical position; never overwrite an existing
     definition — resolve divergence via a new row + a Notes flag. -->

| Term | Context | Definition | Source | Notes |
|------|---------|------------|--------|-------|
| <TermA> | <ContextOne> | <One-sentence definition in the domain's words.> | <source §refs> | - |
| <TermB> | <ContextOne>, <ContextTwo> | <Same meaning in both contexts — one row.> | <source §refs> | - |
| <TermC> | <ContextTwo> | <Definition as used in this context.> | <source §refs> | also called <Alias>; ⚠ see row for <TermC> / <ContextThree> |
| <TermC> | <ContextThree> | <Definition as used in this other context.> | <source §refs> | ⚠ diverges from <ContextTwo> meaning |
