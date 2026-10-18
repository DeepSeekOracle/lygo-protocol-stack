## v1.0.0 — 2026-10-17

First release.

- Deterministic packet audit: classify every file in a folder, extract the fields that must
  agree, and report missing, expired, and inconsistent documents with file and page citations.
- Three bundled profiles: `rental-us`, `schengen-visa`, `insurance-claim-property`.
- Finding codes `PA-E01`, `PA-X01`, `PA-X02`, `PA-C01`, `PA-C02`, `PA-C03`, `PA-F01`, `PA-R01`,
  `PA-D01`, `PA-U01` with severity-driven verdict and exit codes (0/1/2/3).
- Outputs `packet-report.md`, `packet-report.json` (`packet-audit/report/1`), and
  `packet-manifest.json` with SHA-256 per file.
- Standard-library extraction for `.txt`, `.md`, `.csv`, `.json` and `.docx`; optional `pypdf`
  for PDFs; sidecar `<name>.pdf.txt` support; images reported as unreadable instead of guessed.
- 26 fixture-driven tests (clean packet, seeded mismatches, missing documents, extraction,
  profiles, CLI) and a ten-rule self-check.
- Offline: no network imports, no subprocess, no model calls, writes only to `--out`.
