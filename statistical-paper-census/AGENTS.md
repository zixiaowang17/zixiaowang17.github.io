# Repository scope

This repository contains reusable skills and a public export of an agent-assisted experiment.
Keep all artifacts in English. Preserve source statements, mathematical caveats and paper
attribution. Do not treat validation flags or work estimates as proof certificates.

Use the three sibling skills in `skills/` for census, mathlib audit and HTML generation.
Keep PDFs, credentials and private local paths out of the repository. Source PDFs must be
supplied locally by the person running a new audit and pinned by version and hash.

Regenerate HTML with the shared renderer. Do not change the archived experiment data merely
to make the demo or a test pass. Run the relevant regression suite and the release scan after
changes. Publishing the repository or posting the Zulip draft is a separate user action.
