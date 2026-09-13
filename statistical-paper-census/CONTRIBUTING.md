# Contributing

Please include the paper ID, theorem label or API name when reporting a correction. Point
to the relevant source passage or a pinned mathlib declaration, and explain what differs.

Keep original statements separate from your interpretation. Changes to a census require a
new inventory/audit handoff; do not carry old validation hashes over edited source records.
Changes to a work label should name the existing support and the specific remaining task.

Run the synthetic regression suite for changes to the skills or renderer. Regenerate reports
through the shared generator rather than editing generated HTML. Preserve the current
Theorems / Papers counts, three status filters and reader navigation.

Do not commit source PDFs, credentials, personal machine paths or private execution logs.
Use public source URLs and hashes for PDF identity. Run `python3 scripts/check_release.py`
before preparing a release. Keep documentation and generated explanations in English.
