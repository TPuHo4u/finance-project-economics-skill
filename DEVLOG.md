# Development Log

## 2026-10-23 — Standalone package prepared

- Copied the ten canonical skill files into `skills/finance-project-economics/` and recorded their SHA-256 values in `dev/source-files.json`. No course PDFs, raw source documents, private trial notes, or credentials are included.
- The copied documents contain 22 package-relative links; all resolve within the skill directory. The source manifest retains four course-source SHA-256 entries as provenance metadata; the referenced originals are not bundled.
- Earlier usage validation covered eight trials, including standalone use and a UX/other-course handoff. Those trials were not rerun for this packaging task, and their private notes are not included.
- `python3 -B dev/check.py` passed: 10 copied-file hashes, required `SKILL.md` frontmatter, 22 relative links, and four source hashes. A separate comparison confirmed all ten copied files are byte-identical to the canonical source.
- ZIP byte correspondence was skipped because no ZIP bundle is included.
- Primary reviewed the package and authorized publication was prepared; the public Git repository is the distribution mirror of the canonical authoring skill. Update the package and its manifest together when changing the canonical source.

- Published the repository publicly. GitHub rejected the initial private-email author address; the unpublished commit was replaced using the account noreply address, then pushed successfully. Anonymous raw reads matched all ten skill files. Added portable existence/symlink guards to installation commands so repeating them cannot create a nested link in an existing skill directory.
