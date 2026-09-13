---
name: statistical-census-html
description: Generate searchable HTML census reports with By paper and Top APIs views, original source statements before related theorems, and source-backed highlighting on every API detail page. Owns the reusable Python generator and templates.
---

# Statistical Census HTML

Generate the report from `$statistical-paper-census` and its completed `$ranked-mathlib-audit`.
Write report content in English; follow the user's latest language preference in conversation.
Preserve all archived definition and theorem statements verbatim.

This skill owns presentation, search and navigation. Source extraction, keyword grouping,
theorem relationships and highlight selection belong to the census stage. Library searches
and verdicts belong to the audit stage. Never invent either inside the renderer.

## Required inputs

Use the finalized census and its exact audited counterpart. The audit validator checks their
identity and source hash. Keep all main-text Theorems, including those with no linked APIs;
appendices remain excluded. No ranking or library verdict removes an archived theorem.

Every interface requires source-backed `source_keywords` and complete `theorem_explanations`;
legacy input must be backfilled before publication. Never substitute generic direct/indirect-use
sentences for an explanation of the actual symbol or referenced assumption. The census
validator rejects null explanation objects and known retired boilerplate captions before rendering.

Every source member must have inspected `source_kind` and `source_heading` metadata. Preserve
its original Definition/Assumption label and number; identify excerpts by their source theorem.
Never infer the source type from `lean_role` or treat every API as a definition.

Every paper-local source statement must supply `highlight_symbols` and/or `highlight_phrases`, with
at least one nonempty list. Backfill missing annotations from the original source before
rendering older data. There is no exception for less prominent APIs or later-ranked results.
Each paper must supply `source_url` pointing to its inspected original PDF version. Make
paper titles links to that PDF. Keep original-paper links at the paper level only; omit
links and PDF page labels beside individual source statements and theorems. Evidence locations
remain in the data for verification. Missing or unsafe source URLs fail generation; never guess links.

See [references/report-contract.md](references/report-contract.md) for the full contract.

## Reading layout

Preserve the approved white/blue visual style, typography and spacing. Read
[references/approved-style.md](references/approved-style.md) when changing the UI.

- Use readable natural-language API titles grounded in source terminology. Keep notation in
  the detail page. Do not invent an umbrella concept or rewrite definitions when grouping.
- Treat **By paper** and **Top APIs** as peer search tabs. Keep contextual text search and API-kind
  filtering. Omit introductory/helper sentences beneath the title and search controls.
- Keep API rows compact: rank, name, a **Theorems / Papers** count column and a separate **Status** column; add a rank-group label only when
  necessary. Paper rows use “n theorems”. Explain ranking/count scope once in collapsed
  **About ranking**. Use `semantic_rank` within `rank_group`, never build order or filtered ranks.
- Open results in independent right-side reading pages. Preserve filters, scroll and focus;
  provide Back, Close, Escape and Open separately. On narrow screens the reader fills the screen.
- Group API details by paper. Show each original source statement first in a light block with
  a blue left border. Use its stored source heading: for example **Definition**, **Assumption
  4.1**, or **Theorem 5.2 — assumption**. Do not impose one statement type on a shared layout.
  Follow with a separate white **Theorems** section, heading and divider. Keep individual
  theorem labels one heading level below. Backlinks use the corresponding source heading.
- Omit generic relationship captions such as “This theorem directly uses the API.” and
  “Through another definition”. Display only source-specific explanations with useful content.
- Show full original statements and typeset math. Preserve Roman/alphabetic list labels,
  numbering offsets and per-item numbering so internal references stay meaningful. Do not hide
  original definitions under “Variants”. Keep local source labels; notes on actual mathematical
  differences stay separate.
- Use stored `theorem_explanations` to identify the exact symbol or reference linking each
  theorem to the API. Link back to the corresponding definition. Do not fabricate explanations
  or imply an indirect dependency is explicitly written in the theorem.
- Show audited **Use mathlib** (green), **Small adaptation** (yellow) and
  **New infrastructure** (red) labels in API rows, readers and theorem requirement lists.
  Provide three colored toggle buttons in Top APIs, with visible text and `aria-pressed`;
  clicking the selected button clears the filter. Preserve filtering across reload/navigation.
  In collapsed **About ranking**, explain the three meanings and that the boundary concerns
  missing mathematical content, not code length or a missing same-name declaration. Direct
  composition can be green; local bridges are yellow; essential missing theory is red.
  These are scoped work estimates, not certification of related theorem proofs.
  Read `library_audit.work_status` and its reason from the completed audit. Never classify
  inside the renderer. Keep the four legacy research categories internal.
  Counts include all related theorems and distinct papers, each counted once. Keep count and
  status cells side by side on narrow layouts, with their own labels. End with inspected
  **Related mathlib** links and the concrete comparison gap.
- Keep pseudo-Lean shapes and canonical semantic requirements out of the report. Preserve
  paper/theorem search, deduplicated API counts and the final scope note.

## Highlight every API

Apply these rules uniformly to every API reader and every paper-local definition it contains:

1. Read the stored source selectors; never choose highlights from an API name, guess from a
   letter, or special-case a particular API in Python.
2. Highlight mathematical selectors by exact MathML structure, including subscripts, accents
   and any specified expression sequence. Treat scripted or accented atoms as complete units;
   a selector for a base letter must not match inside a differently scripted symbol. Inline/display
   operator placement and delimiter sizing may differ without changing the notation. Highlight prose selectors at word boundaries outside
   MathML, including explicit assumption references. Never alter TeX annotations or source text.
3. Apply a definition's own selectors to that definition. Apply only the current paper's
   selectors to its related theorem statements and explanatory notes. Do not borrow notation
   from another paper or highlight unrelated same-letter variables.
4. Every original definition or its source label must visibly match at least one selector.
   Every supplied selector must match that definition, its source label, or a related theorem
   in the same paper. Generation fails with the API/paper/local ID if either check fails.
5. An indirect theorem may contain no target symbol. Highlight an actual referenced condition
   when present; otherwise preserve its statement and use the recorded relationship explanation.
   Never insert a missing symbol or force a highlight into every theorem.

Paper-only readers have no selected API and retain unhighlighted source statements. Search
indexes include original definitions and stored explanations, not just display names.

## Generate and verify

Install companion skills beside this skill. Pandoc renders local, sanitized MathML; the report
needs no network connection to read. Keep `report.html`, its sibling `report-pages/`, and the input inventory/census artifacts together.

```text
python3 scripts/build_report.py audited.json report.html --census ranked-interfaces.json
python3 scripts/build_report.py audited.json report.html --census ranked-interfaces.json --check
python3 scripts/test_workflow.py
```

The generator validates inputs and all highlight selectors before writing. Unknown TeX,
incomplete audits, missing annotations and unmatched selectors are errors, never silent
fallbacks. Validation checks structural/source consistency; mathematical correspondence still
requires source inspection during extraction.

For UI changes, inspect desktop/mobile examples covering a mathematical symbol, a prose term
and an assumption reference. Check source/Theorems separation, readable math, source links,
search, sidebar navigation and standalone fragments. Use automated coverage checks across the
whole dataset; a successful screenshot of one API is insufficient.

Store each API search record once; theorem requirements contain only its route and relation.
Resolve display fields from the API table. A shared API must not duplicate all its source text
into every theorem. Include a shared-API scaling fixture when changing the index format.

Publish readers into an immutable generation directory beneath `report-pages/`, then atomically
replace the main index after all readers are written. On failure the prior index and its readers
remain usable. Retain older generations so open readers and historical standalone links continue
to work; remove them only in an explicitly requested cleanup. Do not change source fragment IDs.

Change the reusable generator/templates and regenerate outputs. Never hand-patch generated
HTML or add paper/API-specific branches to implement a general presentation rule.

Desktop readers have a draggable vertical separator. Preserve its width ratio across
close/reopen and reload; keep minimum widths for both panes. Support keyboard arrows
and Home/End, double-click reset, and disable the divider for mobile full-screen reading.
Storage unavailability must not prevent using the reader.
