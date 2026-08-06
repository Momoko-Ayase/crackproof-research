# crackproof-research

Source repository for the CrackProof for Windows internals research document,
published at <https://launchcore.gitbook.io/crackproof-research/>.

## Layout

- `internals/en/` — main document (English)
- `internals/zh-cn/` — main document (简体中文)
- `reference/en/`, `reference/zh-cn/` — Verification & reference section: the
  runnable snippet suite, one file per page, plus desensitized reference
  captures
- `verification/` — the runnable Python snippet suite and test vectors behind
  the reference section (`python run_tests.py`)
- `_styleguide/` — the writing style guide enforced on all content

Each content directory is published through GitBook Git Sync. Editing rules
for contributors and agents: see `AGENTS.md`.
