# crackproof-research

Source repository for the CrackProof binary-protection research site, covering
Windows PE files and Android native libraries.

## Layout

- `home/en/`, `home/zh-cn/`, `home/zh-tw/` — single-page site home
- `internals/windows/en/`, `internals/windows/zh-cn/`, `internals/windows/zh-tw/` — Windows PE internals
- `internals/android-so/en/`, `internals/android-so/zh-cn/`, `internals/android-so/zh-tw/` — Android native-library internals
- `reference/en/`, `reference/zh-cn/`, `reference/zh-tw/` — Verification & reference section: the
  runnable snippet suite, one file per page, plus desensitized reference
  captures
- `scripts/s2tw.py` — regenerate Traditional Chinese from Simplified after any
  `zh-cn` edit (`pip install opencc-python-reimplemented && python scripts/s2tw.py`)
- `verification/` — the runnable Python snippet suite and test vectors behind
  the reference section (`python run_tests.py`)
- `_styleguide/` — the writing style guide enforced on all content

Each content directory is published through GitBook Git Sync. Editing rules
for contributors and agents: see `AGENTS.md`.
