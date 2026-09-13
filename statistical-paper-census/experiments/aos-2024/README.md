# Annals of Statistics 2024 experiment

**[Open the HTML report](report.html)** · **[Paper index](paper-index.md)**

This is the complete saved 113-paper experiment. PDFs are external; the report and extracted
statements are included. Download the repository to read the HTML locally, or serve it as
static files. Keep the current `report-pages/` directory with the index.

| File | Contents |
| --- | --- |
| [theorem-inventory.json](theorem-inventory.json) | The 637 original main-text Theorem records and source identities. |
| [ranked-interfaces.json](ranked-interfaces.json) | Definitions, variants, source excerpts, highlights and theorem relationships. |
| [audited.json](audited.json) | The unchanged census plus inspected mathlib declarations, links, gaps and work estimates. |
| [mathlib-search-progress.json](mathlib-search-progress.json) | Search completion records and comparisons for each paper-local variant. |
| [work-status-audit.json](work-status-audit.json) | Evidence and reasons for all three-tier assignments. |
| [mathlib-evidence/links.json](mathlib-evidence/links.json) | Pinned URLs, inspected source excerpts and saved link-check evidence. |
| [mathlib-evidence/declarations.json](mathlib-evidence/declarations.json) | Recorded declaration types and descriptions. |
| [mathlib-source-manifest.json](mathlib-source-manifest.json) | Library revision, archive URL and file hashes; local checkout paths removed. |
| [source-followups.json](source-followups.json) | Recorded source questions and qualifications. |
| [source-note-triage.json](source-note-triage.json) | Their recorded disposition. |
| [paper-index.json](paper-index.json) | Source URLs, PDF hashes and links to the 113 public review summaries. |
| [export-provenance.json](export-provenance.json) | Hashes showing that the core research artifacts were exported unchanged. |

The saved audit contains historical hashes and references to earlier working artifacts.
Those older snapshots, scripts, source screenshots and private execution logs are not bundled.
The per-paper `review.json` files are public summaries, with local paths and unbundled artifact
references removed. The primary source passages and relationships remain in the aggregate
records above. A recorded `complete` status describes the saved workflow, not a formal proof.

The initial two-paper trial and the limits of the larger run are described in
[the review summary](../../docs/review-summary.md). Regenerating the HTML does not rerun the
source or library audit. The original library environment is pinned; it is not a claim about
the latest mathlib release.

Run `python3 scripts/build_experiment.py` from the repository root to rebuild and check the
report. That writes `render-verification.json` with the current report and generator hashes.
