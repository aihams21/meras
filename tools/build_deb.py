"""يبني حزمة تنصيب لينكس (deb) وحزمة محمولة (tar.gz).

الاستخدام:
    python tools/build_deb.py

المخرجات:
    dist/meras_<نسخة>_amd64.deb      حزمة تنصيب لتوزيعات دبيان وأوبونتو
    dist/meras-<نسخة>-linux.tar.gz   نسخة محمولة تفتح بنقرة مزدوجة

لماذا حزمة deb:
واجهة النافذة على لينكس تعتمد على مكتبات النظام (GTK و WebKit)، وهي
مكتبات موجودة أصلا على كل جهاز لينكس حديث. لذلك نركّب تطبيقنا في مسار
مستقل تحت opt ونطلب المكتبات في ترويسة الحزمة، فيتولى مدير الحزم تثبيتها
أو التأكد من وجودها تلقائيا. هذا أفضل من ملف واحد ضخم يحتوي نسخا من GTK.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
PKG_NAME = "meras"
APP_DIR = "opt/meras"

sys.path.insert(0, str(ROOT))
from meras import __version__  # noqa: E402

VENDOR_PKGS = ["pywebview", "bottle", "proxy_tools", "typing_extensions"]

LAUNCHER = """#!/bin/sh
# مشغّل تطبيق ميراس
APPDIR="{appdir}"
export PYTHONPATH="$APPDIR/vendor${PYTHONPATH:+:$PYTHONPATH}"
export GDK_BACKEND="${GDK_BACKEND:-x11}"
exec /usr/bin/python3 "$APPDIR/run.py" "$@"
"""

DESKTOP = """[Desktop Entry]
Type=Application
Name=Meras
Name[ar]=ميراس
Comment=Space map and safe cleaner
Comment[ar]=خريطة المساحة والتنظيف الآمن
Exec=/usr/bin/meras
Icon=meras
Terminal=false
Categories=System;Utility;Filesystem;
StartupNotify=true
StartupWMClass=Meras
Keywords=disk;cleaner;space;storage;privacy;
"""


def log(msg: str) -> None:
    print(f"[deb] {msg}", flush=True)


def arch() -> str:
    out = subprocess.run(["dpkg", "--print-architecture"], capture_output=True, text=True)
    arch = out.stdout.strip()
    return arch or "amd64"


def stage_payload(app_root: Path) -> Path:
    """ينسخ ملفات التطبيق إلى المسار المطلوب داخل جذر الحزمة."""
    app_root.mkdir(parents=True, exist_ok=True)

    shutil.copytree(ROOT / "meras", app_root / "meras",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree(ROOT / "web", app_root / "web")
    shutil.copy2(ROOT / "run.py", app_root / "run.py")

    log("installing vendored dependencies")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--target", str(app_root / "vendor"),
         "--no-compile", "--quiet", *VENDOR_PKGS],
        check=True,
    )
    return app_root


def make_deb() -> Path | None:
    if shutil.which("dpkg-deb") is None:
        log("dpkg-deb not available, skipping the deb package")
        return None

    DIST.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        log("staging application files")
        stage_payload(root / APP_DIR)

        bin_dir = root / "usr" / "bin"
        bin_dir.mkdir(parents=True)
        launcher = bin_dir / PKG_NAME
        launcher.write_text(LAUNCHER.replace("{appdir}", "/" + APP_DIR))
        launcher.chmod(0o755)

        share = root / "usr" / "share"
        (share / "applications").mkdir(parents=True)
        (share / "applications" / f"{PKG_NAME}.desktop").write_text(DESKTOP)

        icons = share / "icons" / "hicolor"
        for size in (16, 24, 32, 48, 64, 128, 256, 512):
            src = ROOT / "tools" / "icons" / f"icon-{size}.png"
            if src.exists():
                dst = icons / f"{size}x{size}" / "apps"
                dst.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst / f"{PKG_NAME}.png")
        svg_src = ROOT / "tools" / "icon.svg"
        if svg_src.exists():
            scalable = icons / "scalable" / "apps"
            scalable.mkdir(parents=True, exist_ok=True)
            shutil.copy2(svg_src, scalable / f"{PKG_NAME}.svg")

        doc = root / "usr" / "share" / "doc" / PKG_NAME
        doc.mkdir(parents=True)
        for name in ("README.md", "LICENSE"):
            src = ROOT / name
            if src.exists():
                shutil.copy2(src, doc / name)

        control = root / "DEBIAN" / "control"
        control.parent.mkdir(parents=True)
        control.write_text(f"""Package: {PKG_NAME}
Version: {__version__}
Section: utils
Priority: optional
Architecture: {arch()}
Maintainer: Meras Project <noreply@example.com>
Installed-Size: 1
Depends: python3 (>= 3.9), python3-gi, gir1.2-gtk-3.0, gir1.2-webkit2-4.0 | gir1.2-webkit2-4.1, python3-cairo
Description: Space map and safe cleaner
 Meras shows a colour coded map of every drive on the machine and finds
 space that is safe to reclaim: duplicates, large files, old downloads,
 build leftovers and temporary files. Nothing is ever deleted directly:
 selected items move to a quarantine folder that can be restored.
""")

        out = DIST / f"{PKG_NAME}_{__version__}_{arch()}.deb"
        log(f"building {out.name}")
        subprocess.run(["dpkg-deb", "--build", "--root-owner-group", str(root), str(out)],
                       check=True)
        log(f"deb ready: {out} ({out.stat().st_size / 1024:.0f} KB)")
        return out


def make_portable() -> Path:
    DIST.mkdir(parents=True, exist_ok=True)
    out = DIST / f"{PKG_NAME}-{__version__}-linux.tar.gz"
    log(f"building {out.name}")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        stage_payload(root / PKG_NAME)
        with tarfile.open(out, "w:gz") as tar:
            tar.add(root / "meras", arcname="meras")
    log(f"portable ready: {out} ({out.stat().st_size / 1024 / 1024:.1f} MB)")
    return out


def main() -> int:
    make_deb()
    make_portable()
    log("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())