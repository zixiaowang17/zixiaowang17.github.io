# Statistical paper census

Three agent skills for reading statistical papers, mapping theorem dependencies, checking
mathlib support, and producing a searchable HTML report.

The full experiment covers **113 Annals of Statistics papers from 2024**, with **637
main-text Theorems** and **2,486 grouped interfaces**. The report and audit data are included;
PDFs are not.

**[Open the full report](experiments/aos-2024/report.html)** ·
**[Browse the audit material](experiments/aos-2024/README.md)** ·
**[What was reviewed](docs/review-summary.md)**

Download or clone the repository and open the report locally. A repository file browser may
show HTML as source; the root `index.html` also works when the repository is served as a
static site. The report works offline, except for links to external paper and mathlib sources.
Keep `report.html` beside its `report-pages/` directory.

## Reusable skills

| Skill | Purpose |
| --- | --- |
| [statistical-paper-census](skills/statistical-paper-census/SKILL.md) | Preserve every main-text Theorem and connect definitions and conditions to their uses. |
| [ranked-mathlib-audit](skills/ranked-mathlib-audit/SKILL.md) | Search a pinned mathlib revision, record inspected declarations, and describe the remaining work. |
| [statistical-census-html](skills/statistical-census-html/SKILL.md) | Build the By paper / Top APIs report with source passages, highlighted notation and linked theorems. |

These are instructions and supporting scripts for an agent. They are not an unattended PDF
parser. Source reading, mathematical grouping and library comparisons still require review.

The code uses Python 3.9+ and Pandoc. The release was exercised with Python 3.9.6 and Pandoc
3.8.2.1. The renderer and validators use Python's standard library; no API key is needed to
rebuild the report. An agent needs its own model and PDF-reading
capabilities to audit new papers.

## Install and use

Copy the three skill directories into your agent's skill directory, keeping them as siblings.
For a Codex installation using `~/.codex/skills`:

```sh
python3 scripts/install_skills.py --dest ~/.codex/skills
```

The installer refuses to replace existing skills. To inspect the package first, install into
an empty temporary directory instead.

A starting request for your agent:

> Use $statistical-paper-census to inventory the main-text Theorems and their interfaces in
> these local papers. Then use $ranked-mathlib-audit for the library comparisons and
> $statistical-census-html for the report. Preserve source statements and record unresolved
> questions. Keep PDFs private and write artifacts in English.

## Reproduce the experiment report

```sh
python3 scripts/build_experiment.py
```

This validates the saved census/audit handoff, builds every reader, then runs the generator's
full reproduction check. It takes several minutes. It does not repeat PDF source review or
perform a new mathlib search. Those activities need the pinned external sources and agent
review. [Experiment files and scope](experiments/aos-2024/README.md).

## Review status

I developed and checked the workflow in detail on two papers, then used it for the larger
113-paper experiment. The detailed trial contains 11 Theorems and 35 grouped interfaces.
The larger run is agent-assisted research output, not an independent human verification of
every entry. Source ambiguities and library comparisons are kept in the public data.

The three work labels are estimates: **Use mathlib**, **Small adaptation**, and **New
infrastructure**. A match means that the recorded interface can be supported; it does not
mean that the paper's theorems have been proved in Lean. Some corpus labels come from a
reassessment of existing evidence and need checking before using them to plan formalization.

Corrections to source transcription, interface grouping, dependency links, mathlib matches,
and the work labels are welcome. Please identify the paper/API and the relevant source or
library declaration. [Contributing](CONTRIBUTING.md).

## Checks

```sh
python3 skills/statistical-census-html/scripts/test_workflow.py
python3 scripts/check_release.py
```

The regression suite checks source preservation, dependency propagation, rendering,
navigation data and failure handling. The release check looks for PDFs, local paths, common
credential patterns and unexpected files. Neither check establishes mathematical correctness
or guarantees detection of every possible secret.

Code, skill instructions and templates retain the source project's Apache-2.0 license.
Paper quotations retain their original attribution and are not relicensed by this repository.
See [LICENSE](LICENSE) and [NOTICE](NOTICE).
