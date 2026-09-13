# Assess the remaining mathematical work

Use this policy for every interface, regardless of rank. All generated artifacts, skill
instructions, status labels, reasons and documentation must be in English. Preserve original
source quotations and mathematical notation.

| Status | Decision boundary | Evidence to record |
| --- | --- | --- |
| Use mathlib (green) | An inspected declaration or direct composition expresses the required interface with matching meaning, domains and assumptions. | Name the components or primitive expression and explain why no supporting mathematical development is needed. |
| Small adaptation (yellow) | The core mathematics exists; a representation conversion or a bounded local compatibility proof remains. | Identify the existing construction and the specific conversion or connecting obligation. |
| New infrastructure (red) | An essential construction, core property or reusable theory required by the interface is missing. | Identify that missing mathematical content and the limits of the searched revision. |

## Practical boundary

A paper-specific finite sum, scalar formula or quantified condition can be green even when
mathlib has no declaration with the paper's name. Record required domains and supplied
parameters. Do not add metric laws, existence results or statistical guarantees unless they
are part of the archived interface being assessed.

A new name or simple `def` alone does not make an interface yellow. Neither `def` nor
`abbrev` determines the tier: assess the required content and properties.

Yellow requires a specific representation change or compatibility proof. Merely being
derivable from mathlib does not make a missing result an adaptation; a missing core result
is red even if its proof can use existing mathlib foundations. Explain the bridge; calling a proof
"local" is not evidence that the needed mathematics exists. Unresolved source conventions
require clarification before a confident estimate; do not conceal an unknown scope in yellow.

A required process construction, integration theory, essential existence theorem or core
algorithm without adequate support is red. Generic measure, function or matrix primitives
alone do not make a substantive missing construction a small adaptation.

There is no universal line-count, lemma-count or time threshold. A short definition can need
substantial theory to provide its required properties; a long wrapper may contain little new
mathematics. Judge the interface's actual obligations. For merged variants, green requires all
variants to be covered; name the variant that determines any higher tier.

## Record and review

Keep the original library search and comparison evidence. Record `work_status`,
`work_status_reason` and `work_status_review` with `basis`, `available`, `remaining`,
`comparison_evidence` and `scope`. Use concrete interface-specific evidence for the decision.
Do not infer the tier from the old research category, declaration name, keyword or code length.
Automated triage may suggest candidates; it does not replace reviewing ambiguous cases.

Unsearched or indeterminate items stay pending in working data, outside completed report
input. A status is a scoped planning assessment, not a promise of proof completion. State
whether it comes from a fresh search, a reassessment of pinned evidence or a compiled check.
