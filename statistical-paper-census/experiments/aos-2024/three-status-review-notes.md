# Three-tier work assessment

Policy: `mathematical-work-v2`. This revision reassesses the completed, pinned library
comparison evidence. It does not claim fresh searches, compiled Lean implementations or
verified estimates of proof time. The original research fields, declarations, links, variant
comparisons and source census are unchanged; `work-status-validation.json` checks this.

The report contains 542 Use mathlib, 1,790 Small adaptation and 154 New infrastructure
assessments. Every decision retains available components, remaining work, comparison evidence,
scope and the hash of its prior review in `work-status-audit.json`.

## Boundary decisions

- **Cost function**: green. The archived function is a scalar formula using norms, matrix
  multiplication and a dot product. The original comparison's transport-integrability and
  optimization arguments concern the related theorem; they do not prevent directly expressing
  this cost function.
- **Matrix / AR coefficients**: green. The archived column formulas compose existing matrix
  operations under the stated nonsingularity condition. Keep the distinct endpoint columns.
- **Average density**: green for the archived finite mixture expressions, retaining their
  denominator and nonempty-group assumptions. This does not assert statistical guarantees.
- **Amenability**: green for the archived quantified sequence-of-measures condition. This
  does not assert equivalence to every other definition of amenability.
- **KL divergence**: yellow. The comparison records an existing ordered extended divergence,
  with representation correspondence and source boundary conventions still to check.
- **Dirichlet process**: red. The inspected beta laws and product measures do not themselves
  supply the required random-measure construction and stick-breaking correspondence.

These decisions concern the archived interface and its variants. A missing same-name
statistical declaration is not a reason to mark a primitive expression red. Conversely,
generic functions, matrices or measures do not make a missing core construction a small
adaptation. Source caveats remain visible in the original comparison; estimates should be
revisited when concrete formalization reveals additional obligations.
