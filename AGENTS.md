<!-- gitbook-agent-instructions:start -->

## GitBook Documentation Editing

This repository contains documentation synced with GitBook via Git Sync.

Before editing GitBook-synced Markdown, YAML, or asset files, make sure the GitBook skill is available and up to date in your local agent environment. Prefer installing or updating it with:

```bash
npx skills add gitbookio/gitbook-skills
```

This command may add or update local agent skill files. Use them only as local agent instructions; do not commit those installed skill files or any tool-generated agent configuration unless the user explicitly asks for it.

If `npx` is unavailable, load the skill from:

https://gitbook.com/docs/skill.md

When making changes, preserve GitBook sync metadata such as frontmatter, `SUMMARY.md`, `docs.yaml`, `.gitbook/`, and asset links unless the requested edit explicitly requires changing them.

<!-- gitbook-agent-instructions:end -->

## Documentation requirements

These rules apply to all content in this repository — the English pages at the repo root and the Simplified Chinese mirror in `zh/`.

- **Research document, not product documentation.** Write about how the protection works internally — never how to use any tool. Do not name CrackProof unpacking/dumping tool implementations (neither the project's own tooling nor third-party ones). Generic analysis tools (IDA, Ghidra, debuggers, memory-forensics frameworks) may be named only where a technique directly involves them. Never add meta-commentary about these rules to the docs themselves — no "this document is/is not..." sections; the rules govern the writing, they are not content.
- **Product naming.** The product is CrackProof® for Windows® (capital P; the developer is HyperTech, capital T). Use the ® on first mention in the home page and in the legal notice; plain "CrackProof" elsewhere. CrackProof is a multi-platform family (Windows PE, Android DEX, Android native libraries, iOS); this document covers only the Windows PE target — never state or imply that CrackProof is Windows-only.
- **Component names.** Use CrackProof-internal names only (KONN, HtpecIt, HtdpStub2, Htsysm, Htsysm7679, status codes, `.kmiat`). Never name machine- or title-specific driver files (e.g. `odd.sys`, `io4.sys`, `wfshbr32.sys`/`wfshbr64.sys`) — those are per-deployment artifacts, not part of the scheme. Never name protected products, publishers, or hardware platforms; use generic build families.
- **Bilingual parity.** Every content change goes into both the English pages and `zh/`, with identical file names and structure. Code blocks stay byte-identical across languages.
- **Style.** Follow `_styleguide/README.md` (Microsoft Writing Style Guide base; numbered MS-n rules are enforceable). Quote every YAML frontmatter `description:` value and keep descriptions short (EN ≤ ~130 chars, zh ≤ ~56 chars).
- **Correctness.** Test every code snippet before publishing. `verification/run_tests.py` must pass, and if any snippet in a page changes, re-run `snippet-tests/verify_docs.py` (in the repo's parent directory) and update the published `reference/` section to match.
- **Publishing.** EN, zh, and the `reference/` section are all Git-Synced: pushing to `main` publishes everything (the EN space is edit-locked). The synced reference pages use GitBook-side file names (`detect.py.md`, `sample-debug-logs.md`, …) — edit those, and keep `reference/SUMMARY.md` as the page list.
