# crackproof-research

Source repository for the CrackProof binary-protection research site, covering
Windows PE files and Android native libraries.

## Layout

- `home/en/`, `home/zh-cn/` — single-page site home
- `internals/windows/en/`, `internals/windows/zh-cn/` — Windows PE internals
- `internals/android-so/en/`, `internals/android-so/zh-cn/` — Android native-library internals
- `reference/en/`, `reference/zh-cn/` — Verification & reference section: the
  runnable snippet suite, one file per page, plus desensitized reference
  captures
- `verification/` — the runnable Python snippet suite and test vectors behind
  the reference section (`python run_tests.py`)
- `_styleguide/` — the writing style guide enforced on all content

Each content directory is published through GitBook Git Sync. Editing rules
for contributors and agents: see `AGENTS.md`.

The legacy `internals/en/` and `internals/zh-cn/` directories remain temporarily
so the existing Windows Spaces keep publishing while Git Sync is moved to the
new project directories. Remove them only after both Windows Spaces have been
rewired and a successful sync has been confirmed.
