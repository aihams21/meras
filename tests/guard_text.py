#!/usr/bin/env python3
"""Text guard: blocks CJK ideographs, corrupted chars, and bidi controls.

The block ranges are written as escape sequences on purpose, so this guard
file never contains a forbidden character itself.

Usage:  python3 tests/guard_text.py [project_root]
Exit code 1 means something is wrong.
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

# Blocked ranges, expressed with escapes so this file stays clean.
_RANGES = [
    (0x1100, 0x11FF),   # Hangul Jamo
    (0x2E80, 0x2EFF),   # CJK radicals
    (0x3000, 0x303F),   # CJK symbols and punctuation
    (0x3040, 0x309F),   # Hiragana
    (0x30A0, 0x30FF),   # Katakana
    (0x3130, 0x318F),   # Hangul compatibility Jamo
    (0x3400, 0x4DBF),   # CJK extension A
    (0x4E00, 0x9FFF),   # CJK unified ideographs
    (0xA960, 0xA97F),   # Hangul Jamo extended A
    (0xAC00, 0xD7FF),   # Hangul syllables and Jamo extended B
    (0xF900, 0xFAFF),   # CJK compatibility ideographs
    (0xFE30, 0xFE4F),   # CJK compatibility forms
    (0xFF00, 0xFFEF),   # Halfwidth and fullwidth forms
    (0x20000, 0x3FFFF), # CJK extensions B and beyond
]
REPLACEMENT = "\ufffd"
BIDI_CONTROL = re.compile("[\u202a-\u202e\u2066-\u2069\u200e\u200f\ufeff]")

TEXT_EXTS = {
    ".py", ".js", ".css", ".html", ".json", ".md",
    ".txt", ".sh", ".bat", ".yml", ".cfg", ".ico", ".svg",
}
BINARY_EXTS = {".ico", ".png", ".woff", ".woff2"}
SKIP_DIRS = {
    "__pycache__", ".git", "node_modules", ".venv", "venv",
    "build", "dist", ".pytest_cache",
}
MAX_BYTES = 4 * 1024 * 1024


def blocked(ch: str) -> str:
    """Returns a description if the character is forbidden, else empty string."""
    cp = ord(ch)
    for lo, hi in _RANGES:
        if lo <= cp <= hi:
            return f"U+{cp:04X} {unicodedata.name(ch, 'unnamed')}"
    if ch == REPLACEMENT:
        return "U+FFFD REPLACEMENT CHARACTER"
    if BIDI_CONTROL.match(ch):
        return f"U+{cp:04X} bidi control"
    return ""


def scan_bytes(raw: bytes, path: Path) -> list[str]:
    """يفحص ملفا ثنائيا: يبحث عن ترميز المحارف الممنوعة داخله."""
    problems: list[str] = []
    for ch in ("\ufffd", "\u202e", "\u202a", "\u200e", "\u200f"):
        if ch.encode("utf-8") in raw:
            problems.append(f"{path}: forbidden control character inside binary file")
    for needle in ("\u4e0b\u8f7d", "\u9875"):
        if needle.encode("utf-8") in raw:
            problems.append(f"{path}: forbidden text inside binary file")
    return problems


def scan_file(path: Path) -> list[str]:
    problems: list[str] = []
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return [f"{path}: cannot read ({exc})"]
    if len(raw) > MAX_BYTES:
        return []
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        # ملفات ثنائية مثل الأيقونات: نفحص البايتات بدل فك الترميز
        if path.suffix.lower() in BINARY_EXTS:
            return scan_bytes(raw, path)
        return [f"{path}: not valid UTF-8 near byte {exc.start}"]

    for num, line in enumerate(text.splitlines(), 1):
        for ch in line:
            why = blocked(ch)
            if why:
                label = why if why.startswith("U+") else "corrupted character"
                problems.append(f"{path}:{num}: forbidden {label} in line")
                break
    return problems


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parent.parent
    problems: list[str] = []
    checked = 0
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in TEXT_EXTS:
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        checked += 1
        problems.extend(scan_file(p))

    if problems:
        print(f"GUARD FAILED: {len(problems)} problem(s) in {checked} file(s)")
        for x in problems:
            print("  -", x)
        return 1
    print(f"GUARD OK: {checked} file(s) clean. No CJK, no corrupt chars.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))