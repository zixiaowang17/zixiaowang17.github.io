# Census data contract

For intake only, save `statistical-theorem-inventory-v1` with `scope.theorem_scope:
main_text_only`, `papers`, and `claims`. For a completed interface census, use
`statistical-ranked-interfaces-v4` and include `interfaces` and the ranking policies below.
All `claims` are results printed as Theorem in the main text; there is no main-result selection.
An empty claim list is valid only after an explicit completed zero-theorem inspection.

Each paper has `paper_id`, `title`, `version`, `pdf_pages`, `pdf_sha256`, and the original
versioned `source_url`. HTML uses a paper-title link only. Also record:

- `main_text_last_pdf_page`: an integer between 1 and `pdf_pages`;
- `main_text_boundary`: `location` describing the inspected endpoint and the boolean
  `shared_page_with_appendix`;
- `intake_review`: `status: complete`, the source-ordered `theorem_ids`, and boolean
  `zero_theorems_confirmed` (true exactly when a completed inspection finds no theorems).

Pending or failed papers stay in a separate work queue. All evidence must fall within this
paper's main text. If an appendix starts on the last main-text page, evidence on that page
also requires `before_main_text_end: true` after inspecting its location above the endpoint.
A page-bound check cannot establish that a passage has been transcribed correctly.

A completed census includes `source_inventory: {path, sha256}`. The path resolves relative to
the census artifact; keep that inventory with the report data. The finalizer's required
`--inventory` argument pins the independently reviewed inventory. Validation checks its hash,
paper metadata, and complete claim records (excluding extraction-stage `depends_on`). Removing,
adding, renumbering or rewriting an inventoried theorem invalidates the handoff.

Each claim has:

- globally unique stable `claim_id`, `paper_id`, `claim_kind: theorem`, and printed `label`;
- `source_order`: positive per-paper order, unique and contiguous from 1;
- `statement_original`: the full original body, including hypotheses and subparts, with math
  delimited by `$...$` or `\[...\]` for rendering; retain original wording and math;
- optional `statement_normalized`, never substituted for the original;
- `evidence`: nonempty records with positive PDF `page` and a short `location`;
- in the completed census, `depends_on`: the direct paper-local interface IDs.

Do not wrap the whole statement in a Theorem TeX environment. Paragraphs and math delimiters
are sufficient. Transcription into LaTeX does not license summarizing or expanding the statement.

## Interfaces and variants

Every interface has `interface_id`, `rank_group`, `name`, `lean_role`, `type_shape`,
`semantic_boundary`, `members`, `central_claim_uses`, and `dependencies`. The shape and boundary
are internal analysis fields. Every member (paper-local variant) requires:

- `paper_id`, unique per-paper `local_id`, `local_label`, `statement_original`;
- `source_kind`: `definition`, `assumption`, `condition`, `theorem_excerpt`, or `source_passage`;
- `source_heading`: a faithful human-readable source heading, preserving printed names/numbers;
- `relation`: `exact`, `equivalent`, `specialization`, `composite_contains`, or `distinct`;
- `depends_on`: same-paper local interface IDs, plus nonempty `evidence`;
- optional `variant_note` explaining a real difference in ordinary language.

`source_kind` describes the original passage, independently of `lean_role`. Preserve an
explicit Assumption 4.1 as Assumption 4.1. A hypothesis excerpt can be headed “Theorem 5.2 —
assumption”. An unnumbered passage that actually defines an object may use Definition; a
model description or statement of constraints must not automatically receive that heading.
Do not infer this metadata in the HTML generator. Keep explanatory source captions separate
from untouched `statement_original`; do not invent original Definition numbers. Missing source
identity must be backfilled before regeneration.

Each direct use has stable `use_id`, `paper_id`, `claim_id`, `use_kind`, `reason`, and evidence.
The historical field name `central_claim_uses` now ranges over all inventoried main-text Theorems,
not a selected important subset. `use_kind` is `statement_dependency`, or `claim_target` for a
separate theorem interface. Direct uses must agree with the claim's local `depends_on` list.

The finalizer derives canonical prerequisite edges from the union of mapped same-paper local
dependencies. They retain `dependency_id`, `prerequisite_interface_id`,
`dependency_kind` (`definition_body` or `theorem_statement`), reason, and evidence. They form a DAG
inside each rank group. Each edge has source `local_edges` (`paper_id`, `from_local_id`,
`to_local_id`), with paper-tagged evidence. Validators compare the entire derived graph rather
than trusting a separately edited edge list. Dependencies between members of the same keyword
group remain local; grouping does not erase them or establish equivalence. A cycle between
canonical groups is an explicit grouping problem, not permission to drop edges. Per-paper local
dependency graphs must also be acyclic.

The finalizer derives `related_theorems` per interface by traversing **same-paper local paths**.
Each entry has `paper_id`, `claim_id`, `relation` (`direct`, `indirect`, or `target`), and
`via_local_ids` (a path from a direct local dependency to a variant of this interface). A target
has an empty path. Multiple paths give one entry; prefer direct over indirect. Original statements
remain in `claims` and are joined by ID, not copied or paraphrased into the interface record.

## Source keywords and display names

Every published interface requires `source_keywords`: an ordered list of records with `paper_id`,
`local_id`, `source_text`, `label` and `kind` (`term` or `symbol`, default `term` for older
records). The first two identify a member; `source_text` is a literal excerpt of its original
statement. If the term occurs in adjacent main-text prose instead, the member may archive
`naming_context: [{context_id, text, evidence}]`; the keyword's `context_id` identifies that exact
passage. Do not alter `statement_original` merely to include a name. Context is for naming, not
an inferred theorem dependency. `label` preserves the quoted term wording, allowing capitalization,
whitespace and equivalent dash typography; mathematical notation belongs to symbol records.
Keyword records inherit the member's evidence. Preserve distinct paper-local definitions.

Set `name` to the distinct natural-language **term** labels joined with ` · ` in recorded order.
At least one term is required. Symbol labels belong in details, not titles. Do not invent an
umbrella concept or a synthesized definition. A keyword group indexes original passages;
it does not establish equivalence of every mathematical object in those passages. Inspect and backfill older records before publishing them; absence is an error.

## Source highlights

Every member requires at least one nonempty list among:

- `highlight_symbols`: exact LaTeX symbol/expression excerpts without math delimiters;
- `highlight_phrases`: exact prose excerpts or numbered references, such as Assumption 4.3.

Selectors must occur in that paper's original definition or theorem statements. Phrases can
also come from the member's `local_label`. Each member inherits source evidence from its own
archived definition and the corresponding theorem records. Choose actual meaning-bearing
occurrences; do not guess from an API title or a common letter. Include source-specific forms
when needed, preserving their subscripts, accents and context.

The HTML generator requires a visible match in every definition or source label and verifies
that every selector matches the definition, label, or an associated same-paper theorem after
rendering. It supports exact math structures/expression sequences and prose word boundaries.
Missing or unmatched highlights fail generation. Backfill older records; do not skip them or
mark an entire arbitrary paragraph merely to satisfy coverage. None of this changes the
archived statement, graph, ranking or mathlib audit verdict.

## Reader explanations

`theorem_explanations` is an interface-level object keyed by `claim_id`. Each entry contains:

- `paper_id` and `via_local_ids`, exactly matching the derived related-theorem record;
- `text`: a short English explanation with optional LaTeX, naming the symbol, phrase or
  referenced condition connecting the original statement to this interface;
- `evidence`: main-text page/location records supporting the statement and definition path.

It must be an object, never null, and cover exactly all related theorems, without extras
(an empty object only when there are none). Known retired boilerplate sentences, including
“This theorem directly uses the API.” and “Through another definition”, are rejected even
when prefixed to otherwise useful text. Replace them with source-specific correspondence;
do not silently discard an explanation or infer one in the renderer. Backfill legacy records
from sources before publication. The
finalizer preserves it, the validator checks coverage, path identity and evidence structure,
and the mathlib audit preserves it unchanged. Semantic correspondence still requires source
inspection; structural validation cannot establish that the explanation is mathematically true.
Never put explanations in derived `related_theorems` (which is regenerated), and never edit
`statement_original` to include commentary or keywords.

## Counts and ordering

`scope` includes `paper_count`, `theorem_scope: main_text_only`, `source_policy`,
`normalization_policy`, `semantic_ranking_policy`, and `build_order_policy`.

The finalizer derives:

- `paper_presence_count`: distinct papers represented by variants;
- `central_claim_paper_count` and `central_claim_use_count`: distinct direct theorem papers/edges;
- `semantic_rank`: descending direct paper and edge counts, then name and interface ID;
- `supported_claim_paper_count` and `supported_claim_count`: distinct papers/theorems in the
  same-paper related-theorem index, including indirect dependencies;
- `downstream_interface_count`: transitive canonical dependents;
- `build_order`: Kahn topological order, preferring supported paper/theorem counts, direct counts,
  semantic rank, name, and ID among currently buildable items.

These internal metrics never replace a theorem's statement or determine inventory inclusion.
No library verdict belongs in this artifact. Version 3 files lack the original-statement and
same-paper linkage guarantees; complete them from sources before emitting version 4.
