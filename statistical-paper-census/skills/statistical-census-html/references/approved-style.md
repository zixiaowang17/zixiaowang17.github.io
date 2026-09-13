# Approved census report style

Approved by the user on 2026-09-08 after the By paper / Top APIs redesign. This is the default
for subsequent reports and datasets. The canonical implementation is `assets/report.css`,
`assets/report.html`, `assets/reading-page.html` and `assets/report.js`.

## Preserve

- A white reading surface, dark blue text, restrained blue links and subtle grey rules.
- The existing CSS tokens: ink `#22314c`, muted `#607088`, line `#dce3ed`, paper `#fff`,
  wash `#f5f7fa`, accent `#2056b5`.
- System sans-serif for navigation and metadata; Georgia/Times serif for theorem statements.
- A left-aligned report heading followed by underlined view tabs. The default is
  “Search the census”; use `--title` for a user-specified report title.
- Omit the introductory sentence beneath the title and the explanatory sentence beneath the
  search controls. The user removed both; do not restore them in future reports.
- By paper and Top APIs as peers in the main search area, with contextual filters.
- Simple result rows: paper titles and audited API needs; API rows show rank, name and one
  compact **Theorems / Papers** column and a separate **Status** column. Keep ranking/count definitions in a collapsed About ranking disclosure,
  rather than repeating direct/indirect statistics under every API name.
  Keep the existing minimum rank-column widths, but allow the column to grow to
  fit longer ranks so four-digit corpus ranks never overlap API names.
- Use the approved three-tier work assessment: **Use mathlib** (green),
  **Small adaptation** (yellow), **New infrastructure** (red). Keep compact text badges in
  rows and readers. Show three colored status toggle buttons in Top APIs; retain text and
  pressed-state accessibility. Explain each tier in About ranking. On narrow screens, keep
  counts and status side by side below the API name. Hide legacy research categories.
- A right-side reading pane that preserves the search context, with Back, Close and
  Open separately controls; on narrow screens, the reader fills the viewport.
- Natural-language API names in the list and page title; notation is highlighted in the details.
- Each paper's original definitions shown before its related theorem statements. Do not label
  all source definitions Variants or put them in a trailing disclosure.
- Distinguish source passages with a light background and blue left border. Their headings
  preserve source identity (Definition, Assumption 4.1, a theorem excerpt, etc.); the shared
  styling must not relabel all passages Definition. Put related theorem statements on white
  under a separate Theorems heading and divider.
- Only paper-level original PDF links; no per-theorem or per-passage PDF page controls.
- No generic direct/indirect relationship captions. Retain source-specific explanations.
- Full original text and MathML, with expandable API requirements, followed by inspected
  mathlib links and concise gap explanations.
- Comfortable reading widths and the existing spacing scale; long formulas scroll within
  their own area rather than widening the page.

## Changes within this style

New data, additional results, bug fixes and accessibility improvements should reuse the existing
components. Do not change the palette, font pairing, page structure or visual identity merely
because a new report is generated. An explicit user request is required for a redesign.

Update the generator and maintained assets together, regenerate the report, and verify the
changed interactions and representative desktop/mobile pages. Do not hand-edit generated HTML.

Desktop readers have a draggable vertical separator. Preserve its width ratio across
close/reopen and reload; keep minimum widths for both panes. Support keyboard arrows
and Home/End, double-click reset, and disable the divider for mobile full-screen reading.
Storage unavailability must not prevent using the reader.
