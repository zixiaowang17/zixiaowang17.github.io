# What was reviewed

## Two-paper trial

The workflow and reader were developed through a detailed trial on:

1. **Gromov–Wasserstein distances: Entropic regularization, duality and sample complexity**
   ([source version](https://arxiv.org/pdf/2212.12848v3)).
2. **Wasserstein convergence in Bayesian and frequentist deconvolution models**
   ([source version](https://arxiv.org/pdf/2309.15300v1)).

The saved trial records contain 11 main-text Theorems, 35 grouped interfaces and 39
paper-local source passages. The recorded review compared theorem labels and statements
with the pinned PDFs, traced definition/theorem connections, inspected related mathlib
declarations and tested the HTML reader. This is the basis for describing the workflow as
reviewed on two papers. It is not a proof of those papers or a general accuracy benchmark.
The historical trial predates the present three-color status policy.

## Larger experiment

The subsequent Annals of Statistics volume 52 (2024) experiment contains:

| Inventory | Count |
| --- | ---: |
| Papers | 113 |
| Main-text Theorems | 637 |
| Grouped interfaces | 2,486 |
| Paper-local source passages | 2,655 |

The theorem inventory excludes appendices and results labeled Lemma, Proposition or
Corollary. An interface's displayed counts include both direct and indirect theorem
relationships. Ranking uses direct demand and is preserved under filtering.

The exported corpus preserves the saved census and library-audit JSON byte-for-byte.
The HTML is rebuilt from those records using the release templates. Its content, IDs,
relationships, ordering and status assignments are preserved; About ranking uses the shorter
release wording. The 113 public paper-review summaries omit local execution details.

The library inspection is pinned to mathlib commit
`4edb0dbaa3b3cf729d86d1e2f035474d5ae2ac09`, with recorded Lean toolchain
`leanprover/lean4:v4.34.0-rc2`. The audit retains 472 distinct inspected declaration links,
search records, source excerpts and comparisons for the paper-local variants.

## Limits

The larger run is agent-assisted. Saved completion flags and schema checks should not be
read as independent human verification of every mathematical comparison. The software
checks inventory consistency, source preservation and rendering; it cannot establish that
all source interpretations or mathlib matches are correct.

The 542 green, 1,790 yellow and 154 red work labels are planning estimates from the archived
evidence. The release skill now states the boundary more explicitly: a simple name or `def`
is not itself an adaptation; a missing core result remains infrastructure work even when
it can be proved from mathlib. This export does not claim to have reassessed every older
label under that clarification.

No paper theorem is claimed to be formally proved by this project. Source issues remain
visible in the [follow-up records](../experiments/aos-2024/source-followups.json) and
[triage decisions](../experiments/aos-2024/source-note-triage.json).
