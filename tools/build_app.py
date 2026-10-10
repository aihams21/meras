"""يبني ملفا تنفيذيا مستقلا للتطبيق.

الاستخدام:
    python tools/build_app.py            # بناء حسب النظام الحالي
    python tools/build_app.py --clean    # تنظيف مخرجات سابقة ثم البناء

المخرجات:
    dist/meras-1.0.0            (لينكس)
    dist/meras-1.0.0-windows.exe  (ويندوز)

ملاحظات:
- لا يحتاج المستخدم النهائي إلى تثبيت بايثون ولا أي مكتبة
- الواجهة الويب تُحزم كبيانات داخل الملف التنفيذي
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_NAME = "meras"
ENTRY = ROOT / "run.py"
WEB = ROOT / "web"
ICON_ICO = ROOT / "tools" / "icon.ico"
DIST = ROOT / "dist"
WORK = ROOT / "build"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from meras import __version__


def binary_name() -> str:
    """اسم الملف التنفيذي، ويشمل رقم النسخة واسم النظام."""
    suffix = "-windows" if os.name == "nt" else "-linux"
    return f"{APP_NAME}-{__version__}{suffix}"


def log(msg: str) -> None:
    print(f"[build] {msg}", flush=True)


def ensure_icon() -> None:
    if not ICON_ICO.exists():
        log("generating icons")
        subprocess.run([sys.executable, str(ROOT / "tools" / "make_icons.py")], check=True)


def web_datas() -> list[tuple[str, str]]:
    """يجمع ملفات الواجهة لتُحزم بجوار الملف التنفيذي."""
    return [(str(WEB), "web")]


def build(onefile: bool = True, console: bool = False, clean: bool = False) -> int:
    ensure_icon()

    if clean:
        for d in (DIST, WORK):
            if d.exists():
                log(f"removing {d.name}/")
                shutil.rmtree(d)

    sep = ";" if os.name == "nt" else ":"
    args = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name", binary_name(),
        "--distpath", str(DIST),
        "--workpath", str(WORK),
        "--specpath", str(WORK),
        "--paths", str(ROOT),
        "--hidden-import", "webview",
        "--hidden-import", "webview.platforms.gtk",
        "--collect-submodules", "webview",
    ]
    if onefile:
        args.append("--onefile")
    else:
        args.append("--onedir")
    if console:
        args.append("--console")
    else:
        args.append("--windowed" if os.name == "nt" else "--noconsole")

    for src, dest in web_datas():
        args += ["--add-data", f"{src}{sep}{dest}"]

    if ICON_ICO.exists():
        args += ["--icon", str(ICON_ICO)]

    args.append(str(ENTRY))

    log("running PyInstaller")
    started = time.time()
    proc = subprocess.run(args, cwd=str(ROOT))
    if proc.returncode != 0:
        log("PyInstaller failed")
        return proc.returncode

    binary = DIST / (binary_name() + (".exe" if os.name == "nt" else ""))
    if not binary.exists():
        log("build finished but the binary is missing")
        return 1

    size_mb = binary.stat().st_size / (1024 * 1024)
    log(f"done in {time.time() - started:.0f}s -> {binary} ({size_mb:.1f} MB)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="build the Meras executable")
    ap.add_argument("--clean", action="store_true", help="remove previous output first")
    ap.add_argument("--onedir", action="store_true", help="folder build instead of a single file")
    ap.add_argument("--console", action="store_true", help="keep a visible console window")
    args = ap.parse_args()
    return build(onefile=not args.onedir, console=args.console, clean=args.clean)


if __name__ == "__main__":
    raise SystemExit(main())