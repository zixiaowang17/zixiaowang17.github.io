# Theorem reading contract

Input is `ranked-mathlib-audit-v4` plus its exact `statistical-ranked-interfaces-v4` source.
The audit is an annotation of that source, not a separate opportunity to change the graph.

Join `interfaces[].related_theorems[].claim_id` to `claims[].statement_original`. Use paper titles
and printed theorem labels, not opaque IDs, as the reading labels. Group by paper: show its
original definitions first, then related theorems in `source_order`. Preserve original text. Each relation is direct, indirect,
or the theorem target itself; preserve this metadata without adding generic relationship captions.

Original definitions use `members[].statement_original` and `local_label`; show `variant_note`
only as a separate note, never as a replacement definition or a claim that all members differ.
Mathlib links use the inspected `library_audit.related_declarations[].url`; `gap` is a single
ordinary-language sentence. No shape, type dump, canonical-requirement block, or unverified flag
belongs in the visible report. Do not calculate a completion percentage from partial matches.

Each interface has a stable independently openable page. Opening it on the right must preserve
index filters and scroll; Escape/close returns focus to the activating control. URLs permit
reopening the same interface. On narrow screens the reading pane may fill the viewport. Use
keyboard-visible focus and readable mathematical line lengths.

Render original text with paragraph structure and locally produced MathML. Retain the untouched
original strings in source data. Sanitize generated HTML; treat paper text as content, never as
script, iframe markup, or navigational instructions. Preserve ordered-list numbering through
both sanitization and highlighting: allow valid `ol type`, integer `ol start`, and integer
`li value` only on their appropriate elements. Do not reset (i)/(a) labels or a numbered
continuation to 1/2. Source references to these labels must retain their meaning. No network
requests are needed to read the report, aside from deliberately following external links.

## Search and API requirements

The search entry points are By paper and Top APIs. Paper search matches paper titles, full
original theorem text, theorem labels and linked API names. The API view supports kind
filtering. Preserve search and kind filters per view and in
URLs so reload/deep links restore the same results; closing a reader preserves the current search.

Rank APIs by the census's `semantic_rank`, within `rank_group`. Never use the input array order
(which is build order) as priority rank, or renumber filtered results. Keep direct paper and theorem
use metrics in the data for ranking. Visible API rows contain rank, name, a Theorems / Papers column and a separate Status column;
add the group name only when several rank groups exist. Count distinct related theorem IDs
and distinct paper IDs from those relationships, including direct and indirect uses.
Explain once in a collapsed About ranking disclosure that ranking uses direct demand while the
displayed counts include direct and indirect relationships, deduplicated by theorem and paper. Do not
repeat statistical definitions or multiple demand metrics in every row.

Invert the already validated `related_theorems` index to find each theorem's API requirements;
exclude `target` relations from dependency lists. Deduplicate requirements by API ID within a
paper. Preserve direct/indirect relationships and all original statements. Do not traverse the
cross-paper canonical graph to manufacture new relationships.

Expose `library_audit.work_status` and its recorded reason on API rows, readers and theorem
requirements. Use green **Use mathlib**, yellow **Small adaptation** and red **New
infrastructure** text labels. Three colored toggle buttons filter Top APIs; clicking an active
button clears that filter. Preserve the selection in URLs and per-view state. Explain all
three tiers in About ranking: direct expression/composition, a local adaptation, or substantive
missing mathematical infrastructure. Judge missing mathematical content, not code length or
the existence of a same-name declaration. Assess the interface, not all related theorem proofs.

Keep count and status cells side by side under the name on narrow screens. Retain inspected
links and comparison gaps; legacy research categories remain internal. Do not infer availability
of a full theorem from its API dependencies. No recorded dependencies does not establish
complete coverage. Ignore legacy coverage URL parameters.

Paper readers include a theorem index, full original statements and expandable API requirements.
An API link navigates within the right reader; Back returns to the originating paper and scroll
position. Standalone links work without a parent page. Browser history, Escape and closing the
reader preserve useful focus and search context.

## Names and source notation

Render an interface's stored `theorem_explanations[claim_id].text` beside the associated theorem,
separately from the untouched original statement. Typeset its math using the same sanitized
renderer. Replace the generic relation sentence rather than adding another metadata block.
Link to the final paper-local definition on the recorded path. It is visible above that paper's
theorems; clicking scrolls to it. Preserve existing fragment IDs for old standalone links.
All published interfaces require a non-null explanation object with complete coverage; known
retired boilerplate captions fail census validation instead of becoming reader text. Legacy
input must be backfilled; the renderer must not fabricate source correspondence or substitute
a generic use sentence. API search includes original definition text and these explanations.

Use natural-language `name` labels in titles and results. Symbol-only source keywords are detail
metadata.

## Highlight contract for every API

Each member has `highlight_symbols` (exact LaTeX expressions, without delimiters) and/or
`highlight_phrases` (exact source prose or a numbered source reference). At least one list
must be nonempty. The census validator checks literal provenance against that member's
original definition, local source label (phrases only), or same-paper theorem statements.
The renderer additionally limits theorem matches to this interface's related theorems.

Prefer distinctive named expressions or numbered assumptions over ambiguous single letters.
For example, packing-number D(ε, B, d) should not highlight every scalar D. The source reviewer
must inspect this correspondence; a literal occurrence alone does not establish meaning.

Render and validate every definition separately: it or its source label must contain a visible
highlight. Every selector must also produce an actual rendered match in its source context.
Fail before writing output when selectors are absent, invalid or unmatched. Older artifacts
must be annotated before regeneration; optional-highlight fallback is not supported.

Mathematical matches use complete MathML subtrees or exact consecutive expression nodes.
Only presentation classes/grouping may change; preserve the mathematical token order and TeX
annotation. Prose matching skips MathML and uses word boundaries, preserving original text and
HTML escaping. Same-paper selectors may highlight related theorem statements and recorded
explanations. An indirect theorem without a matching symbol remains unhighlighted.

On API pages, source blocks have a light background and blue border; Theorems occupy a
separate white section with a heading and divider. Keep stable source fragments and original
statements. Verify all API pages, not one named example, and retain negative tests for missing
selectors, source mismatches, unrelated same-letter symbols and cross-paper leakage.

## Preserve source statement types

Every member supplies `source_kind` and `source_heading`. The renderer displays the heading
without inferring it from the API's Lean role. Keep a printed Assumption number as the main
heading, not as metadata beneath a generic Definition heading. Omit a duplicate local-label
line when it is identical to the heading. Backlinks use the same source heading. Unnumbered
object definitions may use Definition; constraints, model descriptions and theorem hypotheses
retain their own source identity. Do not fabricate a predicate definition to justify a label.


## Original-paper links

`papers[].source_url` identifies the inspected PDF version. Link the paper title to it in
each paper reader and each paper group of an API reader. Keep links at this paper level;
omit per-statement and per-theorem PDF links or page labels. Retain evidence locations in
the underlying data for verification. Paper links open separately with `rel=noopener`,
preserving the census reader. Escape URLs and allow only HTTP(S) sources without credentials. Fail when
a source URL is absent or unsafe; never manufacture a citation URL or an unverified version.

## Scalable index and safe publication

Store each API record once. Theorem `requirements` entries contain only `route` and `relation`;
resolve name, rank, URL and gap through the API table when rendering. Keep text search behavior
and counts unchanged while avoiding repeated cross-paper source text in each requirement.

Readers live in `report-pages/<generation>/`, identified by a content fingerprint of data,
generator and assets. Write the entire new generation before atomically replacing the main
HTML index. Prior generations remain readable after an interrupted build or a successful update.
`--check` verifies the currently expected index and generation without changing files. Existing
legacy standalone files remain available. Do not prune historical generations during publication.

Desktop readers have a draggable vertical separator. Preserve its width ratio across
close/reopen and reload; keep minimum widths for both panes. Support keyboard arrows
and Home/End, double-click reset, and disable the divider for mobile full-screen reading.
Storage unavailability must not prevent using the reader.
