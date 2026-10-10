"""يولّد أيقونة التطبيق بكل الأحجام من ملف SVG واحد.

الاستخدام:
    python build/make_icons.py

الناتج:
    build/icon.ico                 لويندوز
    build/icons/icon-*.png         للينكس وللمستودع
"""

from __future__ import annotations

import shutil
import struct
import subprocess
import sys
import zlib
from pathlib import Path

BUILD = Path(__file__).resolve().parent
SVG = BUILD / "icon.svg"
PNG_DIR = BUILD / "icons"
ICO = BUILD / "icon.ico"

SIZES = [16, 24, 32, 48, 64, 128, 256, 512]


def have(tool: str) -> bool:
    return shutil.which(tool) is not None


def render_png(size: int) -> bytes:
    """يحوّل SVG إلى PNG. يفضّل rsvg ثم inkscape ثم imagemagick."""
    out = BUILD / f".icon-{size}.png"
    if have("rsvg-convert"):
        subprocess.run(
            ["rsvg-convert", "-w", str(size), "-h", str(size), "-o", str(out), str(SVG)],
            check=True,
        )
    elif have("inkscape"):
        subprocess.run(
            ["inkscape", str(SVG), "-o", str(out), "-w", str(size), "-h", str(size)],
            check=True,
        )
    elif have("convert"):
        subprocess.run(
            ["convert", "-background", "none", "-density", "600", str(SVG),
             "-resize", f"{size}x{size}", str(out)],
            check=True,
        )
    else:
        raise SystemExit("no SVG rasterizer found (rsvg-convert / inkscape / convert)")
    data = out.read_bytes()
    out.unlink()
    return data


def png_size(data: bytes) -> tuple[int, int]:
    """يقرأ العرض والارتفاع من ترويسة PNG."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a png")
    w, h = struct.unpack(">II", data[16:24])
    return w, h


def write_ico(images: dict[int, bytes]) -> None:
    """يكتب ملف أيقونة ويندوز متعدد الأحجام من صور PNG."""
    count = len(images)
    offset = 6 + 16 * count
    entries = bytearray()
    blobs = bytearray()
    for size in sorted(images):
        data = images[size]
        w = 0 if size >= 256 else size
        entries += struct.pack("<BBBBHHII", w, w, 0, 0, 1, 32, len(data), offset)
        blobs += data
        offset += len(data)
    header = struct.pack("<HHH", 0, 1, count)
    ICO.write_bytes(bytes(header + entries + blobs))


def main() -> int:
    if not SVG.exists():
        raise SystemExit(f"missing source icon: {SVG}")

    PNG_DIR.mkdir(parents=True, exist_ok=True)
    images: dict[int, bytes] = {}

    for size in SIZES:
        data = render_png(size)
        w, h = png_size(data)
        if (w, h) != (size, size):
            raise SystemExit(f"size mismatch at {size}: got {w}x{h}")
        images[size] = data
        (PNG_DIR / f"icon-{size}.png").write_bytes(data)
        print(f"  icon-{size}.png")

    write_ico(images)
    print(f"  icon.ico ({ICO.stat().st_size} bytes)")
    print("icons are ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())