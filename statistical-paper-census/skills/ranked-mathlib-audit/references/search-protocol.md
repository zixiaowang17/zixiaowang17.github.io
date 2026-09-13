# Search and link verification

For each interface, search its mathematical name, aliases, semantics, and relevant type shapes.
Use Lean local/semantic/type-pattern search when available; otherwise inspect pinned mathlib source
with `rg` and official documentation. No particular unavailable MCP tool is mandatory.

Inspect each plausible candidate's full type, declaration kind, module, and defining body where
needed. Compare domains, quantifiers, assumptions, constants, and conventions. Look for useful
building blocks as well as a complete match; the reader needs to see what mathlib already provides.
Generated recursors, constructors, or projection names are not independent mathematical matches.

Open each saved declaration URL and verify that it points to the declaration actually inspected,
including the fragment or source lines. Use official mathlib docs or the mathlib repository.
A search-results page or a guessed namespace URL is not a declaration link. For moving docs,
compare against the recorded mathlib revision; prefer commit-pinned source when versions differ.

Persist decisive `mechanism`, `query`, and `result` records and each related declaration's name,
type, kind, module, URL, and the short phrase describing what it provides. `link_checked` records
that the destination was actually opened and checked; setting the field alone is not verification.

The one-sentence gap identifies the mathematical content still needed beyond those declarations.
"Not found" after an exact-name query is insufficient. A completed search with no related result
may report that bounded outcome with `no_related_reason`; never manufacture a weak unrelated
link or an unverified missing verdict to fill the UI.
