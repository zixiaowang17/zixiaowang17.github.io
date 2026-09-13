---
name: statistical-paper-census
description: Collect every result labeled Theorem in the main text of statistical papers, preserve original statements, and connect definitions and variants to all related theorems. Skip appendices and main-theorem selection. Use for paper intake and cross-paper declaration censuses, before mathlib search and HTML generation.
---

# Statistical Paper Census

Write generated report content, descriptions, variant notes, mathlib explanations and
documentation in English. For conversational replies, follow the user’s latest language
preference. Preserve original source statements verbatim.

Start with the paper's main text. Store every result labeled **Theorem**, in source order,
with its printed number/title and complete original statement. Do not read appendices or select
"main" results. Lemmas, Propositions, and Corollaries are not included in this theorem inventory.

This skill owns source extraction and theorem–interface relationships. `$ranked-mathlib-audit`
adds searched library links and gaps; `$statistical-census-html` owns the report and its generator.

## Intake

1. Pin the PDF by paper ID, version, page count, SHA-256, and its original versioned
   `source_url`. HTML links the paper title to this inspected PDF; evidence locations remain
   internal. Read the main text with a PDF-capable tool; use a PDF skill when available. Matching-version TeX can aid transcription; printed PDF numbering is authoritative.
2. Save every Theorem's full original statement: hypotheses, formulas, conclusions, and all
   subparts. Do not include proofs. Preserve mathematical content and wording; normalize PDF line
   wrapping only. Keep any expanded/normalized restatement in a separate field.
3. Inspect the main-text endpoint and record `main_text_last_pdf_page`, `main_text_boundary`,
   and `intake_review`. Enumerate actual theorem environments, excluding citations and proof
   headings. Confirm a zero-theorem result explicitly; pending or failed inspection is not zero.
   Save and validate this independent inventory before interface extraction.
4. Preserve stable IDs and source order even for theorems with no extracted interface yet. A
   complete inventory can be the requested deliverable by itself; do not start the later stages
   merely because a paper was supplied.

Read [references/output-schema.md](references/output-schema.md) for the inventory and census
formats. A list selected for importance, or a normalized paraphrase, cannot stand in for the
complete original-theorem inventory. Backfill older inputs from the main text before migration.

## When interface extraction is requested

1. Inspect all stored theorem statements, including conditions defined in preceding main-text
   prose. For each definition/predicate, find **all** related stored theorems before ranking it or
   searching mathlib. Follow mathematical use, not spelling or name similarity.
2. Record per-paper direct theorem dependencies and the recursive definition dependencies.
   [references/statement-dependencies.md](references/statement-dependencies.md) gives the resolution
   rule and mathematical traps. A proof-only occurrence does not make a theorem related.
3. Keep each paper's original source statement, label, ID and dependencies separately.
   Record `source_kind` and `source_heading` from the passage: preserve numbered Definition
   and Assumption labels; identify conditions excerpted from a theorem by that theorem's
   number. Unlabelled prose can define an object, impose a condition, or describe a model;
   inspect which it does. Use a neutral source-passage heading when it does not define an
   object. Do not infer source type from a proposed Lean role, invent a numbered Definition,
   or turn an assumption into a new predicate definition during extraction. A shared layout
   does not imply that all source statements are definitions or mathematical variants.
   For every member, select source-backed `highlight_symbols` and/or `highlight_phrases`.
   At least one selector must identify the original definition or its source label, and every
   selector must occur there or in a related same-paper theorem. Include actual assumption
   references and instantiated notation where needed. Prefer distinctive expressions over
   ambiguous letters; inspect the correspondence, not just string matches. Apply this to all
   interfaces, not only the top-ranked example. An indirect theorem need not contain the symbol.
   Read [references/declaration-semantics.md](references/declaration-semantics.md) when choosing an
   internal Lean role. Type shapes and semantic boundaries are internal aids, not report content;
   use the Lean skill only when that analysis is needed.
4. Extract the author's natural-language keywords and notation before grouping across papers.
   Use readable natural-language terms for titles; do not put a list of symbols in a title.
   Source terms may be capitalized for display. Keep symbols in the detail page, where their
   occurrences can be highlighted in the original definitions and theorem statements. Never
   invent an umbrella name, reinterpret a definition, or write a synthesized definition for a
   group. Group equivalent occurrences while preserving each paper's full original definition
   and source identity. Shared vocabulary alone does not establish equivalence. Stronger
   assumptions, specializations and different quantifiers remain distinguishable; grouping
   related keywords does not make the underlying definitions identical.
   Record mandatory `source_keywords` with exact source excerpts and paper-local references,
   distinguishing natural-language terms from symbols. If the author names an object in adjacent
   prose, archive that passage separately as `naming_context` with its own main-text evidence. Preserve their meaning
   and original definitions; capitalization or typesetting does not license reinterpretation.
5. Construct the related-theorem index from each paper's own dependency paths, then map local
   definitions to canonical interfaces. Do not import another paper's variant dependencies into
   that paper's theorem. Mark direct and indirect relations separately; deduplicate by theorem ID.
6. Supply source-backed `theorem_explanations` for every interface before publication: identify the
   actual symbol, phrase or numbered assumption in each related theorem and connect it to the
   paper-local definition. For indirect use, name the intervening definition or assumption.
   A title or “directly uses the API” is not an explanation. An English API name need not occur
   verbatim in the theorem, but its mathematical correspondence must be explicit and traceable.
   Keep these explanations separate from `statement_original`; never insert search keywords
   into source quotations. `theorem_explanations` must be an object, never null, and cover
   every related theorem. Known retired relationship captions are rejected at publication;
   backfill their source correspondence instead of deleting the explanation or adding filler.
7. Keep direct demand, paper presence, and dependency-propagated reach distinct. Preserve the
   existing dependency-safe build ordering; no ranking decision may remove a stored theorem.
8. Emit unfinalized `statistical-ranked-interfaces-v4` JSON, then derive counts and links:

   ```text
   python3 scripts/finalize_census.py unfinalized.json ranked-interfaces.json --inventory theorem-inventory.json
   python3 scripts/validate_census.py ranked-interfaces.json
   ```

## Batch completion and recovery

Keep a work queue keyed by stable paper ID and pinned PDF version, recording the current stage,
artifact paths and any failure. Resume from the last validated artifact. A failed or pending paper
must not enter completed counts or be treated as having zero theorems or zero API requirements.
Finalize only inspected inventories; pin their hashes at the census handoff and preserve original
claim records. For an aggregate report, reconcile the included per-paper inventories before
combining them. Do not silently drop a failed paper from a requested corpus; report its status.

Names, same-paper connection explanations, source identities and highlights are required for all
published APIs. Older artifacts require source-backed migration, not a compatibility bypass or
filler explanations. Preserve the previous successful artifact on failure. The finalizer derives
canonical edges from local dependencies, validates a temporary file, then replaces the destination.
If grouping introduces a canonical cycle, inspect and revise the grouping; never remove actual
local edges to force an order.

## Boundaries

Do not decide library availability here or exclude an interface because mathlib is believed to
have it. Obvious ambient notation can remain local/external, but its library availability belongs
to the search stage. Preserve enough source context for the formalizer without turning the HTML
into an evidence or pseudo-signature dump. Intake and extraction remain main-text-only even when
a theorem refers to an appendix; keep the reference and record any unresolved meaning.
