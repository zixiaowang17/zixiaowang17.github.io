# Preparing a public release

The release package is a selected export, not a copy of the research workspace or its Git
history. It includes reusable skills, the synthetic demo, the full experiment HTML, core
research data, library-link evidence and public per-paper review summaries.

Excluded material includes PDFs, PDF screenshots, local PDF registries, private execution
logs, machine-specific paths, cached environments and obsolete HTML generations. Source
URLs and PDF hashes remain so readers can identify the versions used.

Before publishing:

1. Read the README and review summary, and check the public data and Zulip draft.
2. Run `python3 scripts/check_release.py` and inspect its findings. The file manifest records
   the exact package contents; the scan is not a guarantee of perfect secret detection.
3. Use a fresh repository and a commit identity you are comfortable making public. Do not
   import the working repository's history. Create the first commit and attach the intended
   new remote after reviewing the package.
4. Publish the repository. The root `index.html` and `.nojekyll` are ready for a static host;
   point the host at the repository root to make the HTML readable in a browser.
5. Fill in the repository/report links in `docs/zulip-post.md` and review it before posting.

The core experiment JSON is preserved byte-for-byte. `export-provenance.json` records its
source and export hashes. Local paths were removed from the library source manifest and
per-paper review summaries. Core data was not rewritten to satisfy the release scan.
