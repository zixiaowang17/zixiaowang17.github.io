# Audited census contract

Use `schema_version: ranked-mathlib-audit-v4`, `source_census_sha256`, `mathlib_revision`, and
`lean_version`. Copy `scope`, `papers`, `claims`, and the complete ordered `interfaces` unchanged
from the source census, adding only `library_audit` to each interface.

```json
{
  "status": "partial_match",
  "related_declarations": [
    {
      "name": "Namespace.declaration",
      "type": "Inspected full Lean type",
      "declaration_kind": "defnInfo",
      "module": "Mathlib.Module",
      "url": "https://leanprover-community.github.io/mathlib4_docs/Mathlib/Module.html#Namespace.declaration",
      "link_checked": true,
      "provides": "The mathematical component this declaration supplies"
    }
  ],
  "searches": [
    {"mechanism": "local source and official docs", "query": "actual query", "result": "observed result"}
  ],
  "gap": "One sentence comparing the interface with the linked declarations."
}
```

Final statuses: `exact_reuse`, `composable`, `partial_match`, `no_verified_match`. Every final entry
requires searches and a gap sentence, even when the sentence says no gap remains. Do not carry an
`unverified` flag or publish `unresolved` entries. Related links are required except when a completed
`no_verified_match` search found no relevant declaration; then require `no_related_reason` and an
empty related list. These are inspected related declarations, not necessarily exact matches.

The validator checks schema, original-census preservation, linkage, allowed URL shapes, and the
recorded check flag. It does not perform or certify mathematical research or network verification;
the agent must do the searches and open the destinations before creating these records.

For new audits, record root `work_status_policy` with `id: mathematical-work-v2` and the
three tier definitions, scope and assessment method. Every audit supplies:

- `work_status`: `use_mathlib`, `small_adaptation` or `new_infrastructure`.
- `work_status_reason`: a nonempty explanation of the decision.
- `work_status_review`: nonempty `basis`, `available`, `remaining`, `comparison_evidence`
  and `scope` strings. Optional provenance includes prior-review hash and variant-review count.

Follow [work-assessment.md](work-assessment.md); preserve the four-way research status and
its evidence. The validator retains support for historical binary artifacts, but new reports
use all three tiers. Validation checks completeness and consistency, not mathematical truth.
