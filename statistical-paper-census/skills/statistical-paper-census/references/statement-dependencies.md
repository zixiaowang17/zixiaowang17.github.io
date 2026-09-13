# Resolving statement dependencies

For every theorem statement and recursively every local definition, resolve each mathematical
symbol or named condition to a local interface, a stated ambient prerequisite, or an object bound
inside the statement. An inline formula or "any estimator satisfying ..." can be a local binder;
it need not become an invented reusable interface. Read relevant main-text prose, not just
numbered Definition environments. An appendix reference does not expand the reading scope.

Keep direct `theorem -> local interface` edges separate from `local interface -> prerequisite`
edges. A theorem is related to a definition if the latter lies on a same-paper path starting from
one of its direct dependencies. Proof citations, downstream applications, and background mentions
do not count. Repeated paths count once. Preserve indirect paths so the report can say why a
relation exists without pretending the definition is explicitly named in the original statement.

## Mathematical details worth preserving

- A property of independently given objects is usually a predicate, while an explicitly defined
  estimator is a function; use a structure only when the theorem consumes a meaningful bundle.
  A kernel estimator and a regularity condition on its kernel are different interfaces.
- Unpack each referenced numbered assumption separately, preserving its quantifiers. Record
  implicit section conventions in the normalized analysis without rewriting the original theorem.
- Asymptotic claims concern sequences of models. Distinguish per-model conditions from
  sequence-level conditions, and state which constants are uniform in sample size.
- Preserve the quantifier scope of "with probability tending to one": a single event supporting
  a uniform assertion differs from pointwise assertions with different events.
- If an assumption's alternative branches select different rates, keep the same branch choice
  in the assumption and conclusion. Do not invent multiple theorem records for one printed theorem.
- A nonstandard variant of a standard notion must retain its actual delta. Different properties
  in the same family are not equivalent merely because they share terminology.
- A cited result is a statement dependency only if its content is needed to state the theorem,
  not simply to prove it. Never follow it into an appendix under the current scope.

Lean shapes may help check whether the declaration is well specified. They are internal proposed
types, not checked Lean code; keep them out of the reader-facing HTML.

## Explain the correspondence

A display name uses natural-language keywords extracted from the source; keep notation in
the detail page and highlight its actual occurrences. Do not invent an
editorial umbrella name or reinterpret the definition when grouping occurrences.
For each related theorem, record the exact source notation or named reference that establishes
the connection. For example, “absolute moments” maps to $M_p$ and $\mathcal{P}_p$, even when
the word “moment” is absent from the theorem. For an indirect relation through $W_1$, explain
that the moment restriction belongs to the paper's definition of the distance; do not call it
an explicitly written theorem assumption. A proof that another hypothesis implies finite
moments does not by itself create a statement dependency.

Store explanations and source evidence in `theorem_explanations`, following the output schema.
A complete graph is not sufficient evidence that the reader can understand a connection.
