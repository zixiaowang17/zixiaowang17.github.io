# Zulip draft

Suggested topic: Statistical paper census and mathlib audit skills

I've been working on a set of agent skills for reading statistical papers and finding what
would be needed to formalize them in Lean.

The workflow collects main-text Theorems, links them to definitions and assumptions, checks
related mathlib declarations, and builds a searchable HTML report. I developed and reviewed
it in detail on two papers, then ran a larger experiment on 113 Annals of Statistics papers
from 2024: 637 Theorems and 2,486 grouped interfaces.

I'm sharing the three skills and the full experiment report with
its census and audit records. PDFs aren't included; the records link to the source versions.

The mathlib matches and green/yellow/red work labels need review. They aren't claims that
the paper results have been proved in Lean. I'd especially appreciate corrections to the
interface grouping, dependencies and library comparisons, or reports from people trying
the skills on other papers.

Repository: [insert the public repository URL]
Report: [insert the hosted report URL, or link to the repository's opening instructions]
