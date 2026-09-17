#!/usr/bin/env python3
"""Regenerate Traditional Chinese (zh-tw) trees from Simplified (zh-cn).

Do not hand-author zh-tw pages. After any zh-cn content change, run this
from the repository root:

    python scripts/s2tw.py

Requires: pip install opencc-python-reimplemented

The script:

1. Repairs GitBook Markdown damage in every zh-cn source file:
   - numeric-entity corruption (CJK next to symbols exported as
     ``&#x8D56;``) is decoded back to the character;
   - underscore emphasis next to CJK (``依赖_原始_的``) is rewritten to
     asterisk emphasis (``依赖*原始*的``), because CommonMark treats CJK
     as word characters and will not render ``_…_`` there.
2. Rebuilds each zh-tw directory from the matching zh-cn tree.
3. Converts prose with OpenCC ``s2tw`` (Taiwan character standard, not
   ``s2twp`` phrase localization) so terminology stays aligned with zh-cn.
4. Leaves fenced and inline code byte-identical.
5. Remaps zh-cn GitBook space IDs to the zh-tw counterparts.
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

try:
    from opencc import OpenCC
except ImportError:
    sys.stderr.write(
        "opencc is required. Install with:\n"
        "  pip install opencc-python-reimplemented\n"
    )
    raise SystemExit(2)

REPO_ROOT = Path(__file__).resolve().parents[1]

PAIRS: tuple[tuple[str, str], ...] = (
    ("home/zh-cn", "home/zh-tw"),
    ("internals/windows/zh-cn", "internals/windows/zh-tw"),
    ("internals/android-so/zh-cn", "internals/android-so/zh-tw"),
    ("reference/zh-cn", "reference/zh-tw"),
    ("senbei/zh-cn", "senbei/zh-tw"),
    ("arare/zh-cn", "arare/zh-tw"),
)

# zh-cn space ID -> zh-tw space ID. Keep in sync with AGENTS.md.
SPACE_ID_MAP: dict[str, str] = {
    "IhAaLkXqnmlpZG4wqWIz": "oGjHDoJ7g4TMY3X80PzH",  # Home
    "fEb9nKPvKsjkPAHMUbOt": "sFi4W2Zr1UBoxZd5YI3A",  # Windows
    "Aoyn9wKiHAVzBKGSUifa": "HezwIJwx0lhm5CUG7g8R",  # Android SO
    "L9bXLua8yrIPEUZOHO21": "2p7kzW649ZlKfmpYdJ87",  # Reference
    "tMIkyJzuS8q10cZToDDD": "v6LkixcUwwnaXW5PFCVE",  # Senbei
}

CONVERT_SUFFIXES = {".md"}
COPY_AS_IS_SUFFIXES = {".yaml", ".yml"}

ENTITY_RE = re.compile(r"&#x([0-9A-Fa-f]+);|&#(\d+);")
FENCE_RE = re.compile(
    r"(^```[^\n]*\n.*?^```[ \t]*(?:\n|$))",
    re.MULTILINE | re.DOTALL,
)
INLINE_RE = re.compile(r"`[^`\n]+`")
# Single-underscore emphasis only. Do not touch __bold__ or snake_case.
UNDERSCORE_EMPHASIS_RE = re.compile(r"(?<!_)_([^_\n]+?)_(?!_)")

# OpenCC s2tw sometimes reads 干 as 幹 (work) instead of 乾 (dry).
# 幹淨 is not a valid word; 干净 must become 乾淨.
OPENCC_FIXES: tuple[tuple[str, str], ...] = (("幹淨", "乾淨"),)


def is_cjk(cp: int) -> bool:
    return (
        0x3400 <= cp <= 0x4DBF
        or 0x4E00 <= cp <= 0x9FFF
        or 0xF900 <= cp <= 0xFAFF
        or 0x20000 <= cp <= 0x2A6DF
        or 0x2A700 <= cp <= 0x2B73F
        or 0x2B740 <= cp <= 0x2B81F
        or 0x2B820 <= cp <= 0x2CEAF
        or 0x30000 <= cp <= 0x3134F
    )


def is_cjk_char(ch: str) -> bool:
    return bool(ch) and is_cjk(ord(ch))


def decode_cjk_entities(text: str) -> tuple[str, list[str]]:
    found: list[str] = []

    def repl(match: re.Match[str]) -> str:
        raw = match.group(1)
        cp = int(raw, 16) if raw is not None else int(match.group(2), 10)
        if not is_cjk(cp):
            return match.group(0)
        ch = chr(cp)
        found.append(f"{match.group(0)} -> {ch} (U+{cp:04X})")
        return ch

    return ENTITY_RE.sub(repl, text), found


def rewrite_cjk_underscore_emphasis(text: str) -> tuple[str, list[str]]:
    """Turn `_…_` into `*…*` when the span is next to or contains CJK.

    CommonMark treats CJK as word characters, so `_原始_` between hanzi
    is intra-word and does not become <em>. Asterisks do.
    """
    found: list[str] = []

    def repl(match: re.Match[str]) -> str:
        inner = match.group(1)
        start, end = match.span()
        prev = match.string[start - 1] if start > 0 else ""
        nxt = match.string[end] if end < len(match.string) else ""
        if not (
            is_cjk_char(prev)
            or is_cjk_char(nxt)
            or any(is_cjk_char(ch) for ch in inner)
        ):
            return match.group(0)
        found.append(f"_{inner}_ -> *{inner}*")
        return f"*{inner}*"

    return UNDERSCORE_EMPHASIS_RE.sub(repl, text), found


def map_noncode(text: str, transform) -> tuple[str, list[str]]:
    """Apply *transform* to Markdown outside fenced and inline code."""
    notes: list[str] = []
    fence_parts: list[str] = []
    last = 0
    for match in FENCE_RE.finditer(text):
        chunk, extra = map_inline(text[last:match.start()], transform)
        fence_parts.append(chunk)
        notes.extend(extra)
        fence_parts.append(match.group(0))
        last = match.end()
    chunk, extra = map_inline(text[last:], transform)
    fence_parts.append(chunk)
    notes.extend(extra)
    return "".join(fence_parts), notes


def map_inline(text: str, transform) -> tuple[str, list[str]]:
    notes: list[str] = []
    parts: list[str] = []
    last = 0
    for match in INLINE_RE.finditer(text):
        chunk, extra = transform(text[last:match.start()])
        parts.append(chunk)
        notes.extend(extra)
        parts.append(match.group(0))
        last = match.end()
    chunk, extra = transform(text[last:])
    parts.append(chunk)
    notes.extend(extra)
    return "".join(parts), notes


def repair_markdown(text: str) -> tuple[str, list[str]]:
    decoded, notes = decode_cjk_entities(text)
    rewritten, extra = map_noncode(decoded, rewrite_cjk_underscore_emphasis)
    notes.extend(extra)
    return rewritten, notes


def convert_prose(text: str, cc: OpenCC) -> str:
    parts: list[str] = []
    last = 0
    for match in INLINE_RE.finditer(text):
        parts.append(cc.convert(text[last:match.start()]))
        parts.append(match.group(0))
        last = match.end()
    parts.append(cc.convert(text[last:]))
    out = "".join(parts)
    for src, dst in OPENCC_FIXES:
        out = out.replace(src, dst)
    return out


def convert_markdown(text: str, cc: OpenCC) -> str:
    parts: list[str] = []
    last = 0
    for match in FENCE_RE.finditer(text):
        parts.append(convert_prose(text[last:match.start()], cc))
        parts.append(match.group(0))
        last = match.end()
    parts.append(convert_prose(text[last:], cc))
    out = "".join(parts)
    for src_id, dst_id in SPACE_ID_MAP.items():
        out = out.replace(src_id, dst_id)
    return out


def extract_fences(text: str) -> list[str]:
    return [match.group(0) for match in FENCE_RE.finditer(text)]


def read_text(path: Path) -> tuple[str, str]:
    data = path.read_bytes()
    newline = "\r\n" if b"\r\n" in data else "\n"
    return data.decode("utf-8").replace("\r\n", "\n"), newline


def write_text(path: Path, text: str, newline: str) -> None:
    path.write_bytes(text.replace("\n", newline).encode("utf-8"))


def repair_zh_cn() -> int:
    repaired = 0
    for src_rel, _ in PAIRS:
        src_root = REPO_ROOT / src_rel
        for path in sorted(src_root.rglob("*.md")):
            original, newline = read_text(path)
            fixed, found = repair_markdown(original)
            if not found:
                continue
            write_text(path, fixed, newline)
            repaired += 1
            rel = path.relative_to(REPO_ROOT).as_posix()
            print(f"repaired {rel}")
            for item in found:
                print(f"  {item}")
    return repaired


def rebuild_zh_tw(cc: OpenCC) -> None:
    for src_rel, dst_rel in PAIRS:
        src_root = REPO_ROOT / src_rel
        dst_root = REPO_ROOT / dst_rel
        if not src_root.is_dir():
            raise SystemExit(f"missing source tree: {src_rel}")
        if dst_root.exists():
            shutil.rmtree(dst_root)
        copied = 0
        converted = 0
        for src in src_root.rglob("*"):
            if not src.is_file():
                continue
            if src.name.startswith(".") and src.suffix not in CONVERT_SUFFIXES | COPY_AS_IS_SUFFIXES:
                continue
            rel = src.relative_to(src_root)
            dst = dst_root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.suffix in CONVERT_SUFFIXES:
                source_text, newline = read_text(src)
                dest_text = convert_markdown(source_text, cc)
                write_text(dst, dest_text, newline)
                src_fences = extract_fences(source_text)
                dst_fences = extract_fences(dest_text)
                if src_fences != dst_fences:
                    raise SystemExit(
                        f"code fence mismatch after conversion: "
                        f"{src.relative_to(REPO_ROOT).as_posix()}"
                    )
                converted += 1
            else:
                shutil.copy2(src, dst)
                copied += 1
        print(f"{src_rel} -> {dst_rel}: converted {converted} md, copied {copied} other")


def main() -> int:
    repaired = repair_zh_cn()
    print(f"zh-cn repair: {repaired} file(s)")
    rebuild_zh_tw(OpenCC("s2tw"))
    print("zh-tw regeneration complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
