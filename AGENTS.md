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

These rules apply to all content in this repository: the bilingual Home pages in `home/`, the Windows pages in `internals/windows/`, the Android native-library pages in `internals/android-so/`, and the bilingual Verification & reference section in `reference/`.

- **Research document, not product documentation.** Write about how the protection works internally — never how to use any tool. Do not name CrackProof unpacking/dumping tool implementations (neither the project's own tooling nor third-party ones). Generic analysis tools (IDA, Ghidra, debuggers, memory-forensics frameworks) may be named only where a technique directly involves them. Never add meta-commentary about these rules to the docs themselves — no "this document is/is not..." sections; the rules govern the writing, they are not content.
- **Product naming.** Use CrackProof® on first mention on each Home page and in legal notices; use plain "CrackProof" elsewhere. The Windows product is CrackProof for Windows® (capital P; the developer is HyperTech, capital T). CrackProof is a multi-platform family. This repository covers Windows PE files and Android native libraries; do not imply that either section describes the whole product family.
- **Component names.** Use CrackProof-internal names only (KONN, HtpecIt, HtdpStub2, Htsysm, Htsysm7679, status codes, `.kmiat`). Never name machine- or title-specific driver files (e.g. `odd.sys`, `io4.sys`, `wfshbr32.sys`/`wfshbr64.sys`) — those are per-deployment artifacts, not part of the scheme. Never name protected products, publishers, or hardware platforms; use generic build families.
- **Bilingual parity.** Every content change goes into both language variants of the affected Space, with identical file names and structure. Code blocks stay byte-identical across languages.
- **Style.** Readability takes priority. Follow `_styleguide/README.md` (Microsoft Writing Style Guide base; numbered MS-n rules are enforceable). Use established technical terms when they exist. When no stable term exists, describe the observed structure or behavior literally. Do not invent names, labels, pseudo-technical compounds, or translations merely to make the prose sound specialized. Prefer short sentences, concrete subjects, and one main idea per paragraph. Quote every YAML frontmatter `description:` value and keep descriptions short (EN ≤ ~130 chars, zh ≤ ~56 chars).
- **Correctness.** Test every code snippet before publishing. `verification/run_tests.py` must pass, and if any snippet in a page changes, re-run `snippet-tests/verify_docs.py` (in the repo's parent directory) and update the published `reference/` section to match.
- **Publishing.** Each language directory is a separate GitBook Space synced from `main`. The target directories are `home/en/`, `home/zh-cn/`, `internals/windows/en/`, `internals/windows/zh-cn/`, `internals/android-so/en/`, `internals/android-so/zh-cn/`, `reference/en/`, and `reference/zh-cn/`. The reference pages use GitBook-side file names (`detect.py.md`, `sample-debug-logs.md`, …); each language's `SUMMARY.md` is the page list. Cross-space links use GitBook's native internal-link form `https://app.gitbook.com/s/<spaceId>/<path>` (never the public hostname), always targeting the matching language. Space IDs: Home EN `FcRC5WRR58YTNOweCwNN`, Home zh `IhAaLkXqnmlpZG4wqWIz`; Windows EN `PuKTEy2soDgSB3qfWACy`, Windows zh `fEb9nKPvKsjkPAHMUbOt`; Android SO EN `fcBZibCo72OSh5jVcKoo`, Android SO zh `Aoyn9wKiHAVzBKGSUifa`; Reference EN `8S0xnfw9UP9A2yylicaA`, Reference zh `L9bXLua8yrIPEUZOHO21`.
- **Navigation parity.** A generic Overview page is a sibling of the other pages in its `SUMMARY.md` group, not their parent. GitBook derives group URL segments from localized headings, so every bilingual Space must keep reciprocal redirects for the English and Chinese group paths in `.gitbook.yaml`. Update those redirects whenever a group or page path changes.
