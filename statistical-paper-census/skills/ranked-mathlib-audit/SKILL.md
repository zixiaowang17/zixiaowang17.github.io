---
name: ranked-mathlib-audit
description: Search mathlib for interfaces in a statistical-paper-census artifact, inspect related declarations, save verified links, and assess direct reuse, small adaptation or new infrastructure from the remaining mathematical work. This is the library-search stage; statistical-census-html separately renders the report.
---

# Ranked Mathlib Audit

Write generated report content, descriptions, variant notes, mathlib explanations and
documentation in English. For conversational replies, follow the user’s latest language
preference. Preserve original source statements verbatim.

Consume a validated `statistical-ranked-interfaces-v4` census. Preserve the complete main-text
Theorem inventory, original statements, variants, related-theorem index, edges, and ordering.
Do not reinterpret PDFs or redo extraction here. `$statistical-census-html` owns HTML generation.

## Workflow

1. Validate the census, including its pinned independent inventory, with the producer's
   validator and record its exact SHA-256. Keep the referenced inventory available at handoff. Pin the mathlib
   commit/release and Lean version used for searching.
2. Search each interface using [references/search-protocol.md](references/search-protocol.md).
   Find related infrastructure even when no declaration implements the entire paper definition.
3. Inspect candidate declarations and their defining types/bodies. Save working links to the
   actual declarations in official mathlib docs or source, with an explanation of what each offers.
4. Write one concise sentence stating why those declarations still leave a gap. If they already
   suffice, say that; do not invent a gap just to fill the field. The comparison is against the
   interface's actual variants and mathematical requirements, not merely its name.
5. Add `library_audit` records under `ranked-mathlib-audit-v4` as specified in
   [references/output-schema.md](references/output-schema.md). Preserve all census data exactly.
6. Validate the completed handoff:

   ```text
   python3 scripts/validate_audit.py audited.json --census ranked-interfaces.json
   ```

## Completion rules

An `unverified*` badge is not an acceptable substitute for searching. Final report input must
contain completed searches and inspected links; unresolved or unsearched entries stay in working
data until resolved. Do not turn a failed search or an inaccessible tool into a missing verdict.
Use available local source and official documentation fallbacks.

## Three-tier work assessment

Use `work_status_policy.id: mathematical-work-v2`. Assess every archived interface and its
variants using [references/work-assessment.md](references/work-assessment.md):

- `use_mathlib` — **Use mathlib** (green): an inspected interface or direct composition of
  existing operations suffices with the same meaning, domains and assumptions; no new
  mathematical proof is needed.
- `small_adaptation` — **Small adaptation** (yellow): existing mathematics suffices, with a
  representation conversion or local compatibility proof still needed. A simple new name
  is not by itself an adaptation.
- `new_infrastructure` — **New infrastructure** (red): an essential construction, core
  property or reusable theory required by this interface still needs development.

Judge the missing mathematical content, not code length or the absence of a same-name API.
Do not require proofs of all related paper theorems just to express a definition or hypothesis.
For each decision, record the available components, the specific remaining obligation, scope
and a concise reason. Insufficient evidence remains pending in working data; it is not yellow
by default. Resolve it before including it in a completed report.

The legacy `exact_reuse`, `composable`, `partial_match` and `no_verified_match` fields remain
internal research metadata. Preserve their searches, declaration links and comparison evidence;
never mechanically map them to the three work tiers. A no-name match may still be a direct
expression. A collection of related declarations may still lack a core construction.

Reassessing completed evidence does not constitute a fresh library search or a compiled Lean
implementation. Record that method and its limits. Absence claims remain bounded by the pinned
revision and search scope. HTML layout and rendering belong to the next skill.
