"""محرّك الفحص: يحسب المساحة ويكشف الزبالة والملفات المكرّرة.

المبادئ:
- فحص بثلاثة مسارات (cache / big / duplicates)
- محاولات تخطّي الأخطاء بدل ما ينهار
- تقدّم (progress) اختياري عبر callback
- تصنيف كل عنصر بمستوى خطورة + سبب واضح يبان للمستخدم
"""

from __future__ import annotations

import hashlib
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path

from . import safety
from .platform_info import IS_WINDOWS, user_folders

# ---- risk levels ----
RISK_SAFE = "safe"       # تالف بوضوح / زبالة
RISK_CAUTION = "caution" # ممكن ينفع يمسح - بس لازم المستخدم يوافق
RISK_DANGER = "danger"   # ملف شخصي كبير أو قديم - حذفه طلب صريح


@dataclass
class Item:
    """عنصر في نتائج الفحص."""

    path: str
    size: int
    kind: str          # category key
    risk: str
    reason_key: str    # مفتاح سبب (يترجم بالواجهة)
    reason_params: dict = field(default_factory=dict)
    mtime: float = 0.0
    ext: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ---- categories ----
CATEGORIES = {
    "duplicates": "duplicates",
    "large": "large_files",
    "old_downloads": "old_downloads",
    "temp": "temp_files",
    "logs": "log_files",
    "empty_dirs": "empty_dirs",
    "build": "build_artifacts",
    "installers": "installers",
}

TEMP_EXT = {
    ".tmp", ".temp", ".log", ".old", ".bak", ".cache", ".dmp", ".stackdump",
    ".part", ".crdownload", ".download", ".nib", ".swp", ".orig", ".rej",
}
INSTALLER_EXT = {".iso", ".img", ".dmg", ".msi", ".pkg", ".deb", ".rpm", ".apk", ".exe", ".msix"}
LOG_EXT = {".log", ".out", ".err", ".trace"}

# build folders - safe-ish to clean (regenerated)
BUILD_DIR_NAMES = {"node_modules", "__pycache__", ".pytest_cache", ".mypy_cache",
                   ".ruff_cache", ".tox", "dist", "build", ".next", ".nuxt",
                   ".parcel-cache", ".cache", ".gradle", ".idea"}

DUPLICATE_MIN_SIZE = 1024 * 1024      # 1 MB
LARGE_FILE_THRESHOLD = 100 * 1024 * 1024   # 100 MB
OLD_DOWNLOAD_DAYS = 365               # سنة
MAX_WALK_ENTRIES = 400_000            # سقف أمان للأداء


class Scanner:
    """ماسح المساحة. كل الدوال ترجع نتائج نظيفة جاهزة للعرض."""

    def __init__(self, progress=None):
        self.progress = progress or (lambda *_: None)
        self._cancel = False

    def cancel(self):
        self._cancel = True

    # ---------- helpers ----------
    def _walk(self, root: str, follow=False):
        if not root or not os.path.isdir(root):
            return
        count = 0
        for dirpath, dirnames, filenames in os.walk(root, followlinks=follow):
            if self._cancel:
                return
            count += len(dirnames) + len(filenames)
            if count > MAX_WALK_ENTRIES:
                self.progress("limit", root)
                return
            # تخطّي المجلدات الحساسة entirely
            dirnames[:] = [d for d in dirnames if not safety.is_sensitive_name(os.path.join(dirpath, d))]
            yield dirpath, dirnames, filenames
            self.progress("walk", dirpath)

    @staticmethod
    def _sha256(path: str, chunk=1024 * 1024) -> str | None:
        try:
            h = hashlib.sha256()
            with open(path, "rb") as fh:
                while True:
                    b = fh.read(chunk)
                    if not b:
                        break
                    h.update(b)
            return h.hexdigest()
        except OSError:
            return None

    # ---------- main scan ----------
    def scan_all(self) -> dict:
        """يفحص كل المجلدات الشخصية + Zakalate."""
        folders = user_folders()
        self.progress("start", "")

        result = {
            "categories": {},
            "total_reclaimable": 0,
            "scanned_roots": [],
            "duration_ms": 0,
        }
        t0 = time.time()

        # نجمع الملفات مرة وحدة
        files = self._collect_files(folders)

        # ---- duplicates ----
        result["categories"]["duplicates"] = self._find_duplicates(files)
        # ---- large files ----
        result["categories"]["large"] = self._find_large(files)
        # ---- old downloads ----
        result["categories"]["old_downloads"] = self._find_old_downloads(files, folders)
        # ---- temp + logs ----
        temp, logs, installers, build = [], [], [], []
        for f in files:
            ext = f["ext"]
            if ext in INSTALLER_EXT:
                installers.append(f)
            elif ext in LOG_EXT:
                logs.append(f)
            elif ext in TEMP_EXT:
                temp.append(f)
        result["categories"]["installers"] = self._mk_items(installers, "installers", RISK_CAUTION, "installer")
        result["categories"]["logs"] = self._mk_items(logs, "logs", RISK_SAFE, "log")
        result["categories"]["temp"] = self._mk_items(temp, "temp", RISK_SAFE, "temp")
        result["categories"]["build"] = self._find_build_dirs(folders)
        result["categories"]["empty_dirs"] = self._find_empty_dirs(folders)

        # ---- totals ----
        total = 0
        for key, items in result["categories"].items():
            total += sum(i["size"] for i in items)
        result["total_reclaimable"] = total
        result["duration_ms"] = int((time.time() - t0) * 1000)
        result["scanned_roots"] = [p for p in [
            folders.downloads, folders.desktop, folders.videos,
            folders.pictures, folders.documents, folders.temp,
        ] if p and os.path.isdir(p)]
        return result

    def _collect_files(self, folders) -> list[dict]:
        roots = [p for p in [
            folders.downloads, folders.desktop, folders.videos,
            folders.pictures, folders.documents, folders.temp,
        ] if p and os.path.isdir(p)]
        out: list[dict] = []
        seen_paths: set[str] = set()
        for root in roots:
            for dirpath, dirnames, filenames in self._walk(root):
                for name in filenames:
                    fp = os.path.join(dirpath, name)
                    if fp in seen_paths:
                        continue
                    seen_paths.add(fp)
                    try:
                        st = os.lstat(fp)
                    except OSError:
                        continue
                    if os.path.islink(fp):
                        continue
                    out.append({
                        "path": fp,
                        "size": st.st_size,
                        "mtime": st.st_mtime,
                        "ext": Path(name).suffix.lower(),
                    })
            self.progress("root_done", root)
        return out

    def _mk_items(self, files: list[dict], kind: str, risk: str, reason: str) -> list[dict]:
        items = []
        for f in files:
            if not safety.is_safe_to_delete(f["path"]):
                continue
            items.append(Item(
                path=f["path"], size=f["size"], kind=kind, risk=risk,
                reason_key=reason, mtime=f["mtime"], ext=f["ext"],
            ).to_dict())
        items.sort(key=lambda x: x["size"], reverse=True)
        return items

    def _find_duplicates(self, files: list[dict]) -> list[dict]:
        # group by size first (fast), then hash only same-size groups
        by_size: dict[int, list[dict]] = defaultdict(list)
        for f in files:
            if f["size"] >= DUPLICATE_MIN_SIZE:
                by_size[f["size"]].append(f)

        items: list[dict] = []
        for size, group in by_size.items():
            if len(group) < 2:
                continue
            by_hash: dict[str, list[dict]] = defaultdict(list)
            for f in group:
                h = self._sha256(f["path"])
                if h:
                    by_hash[h].append(f)
            for h, same in by_hash.items():
                if len(same) < 2:
                    continue
                # نحتفظ بأحدث واحد ونضع الباقي كمرشّح
                same_sorted = sorted(same, key=lambda x: x["mtime"], reverse=True)
                keeper = same_sorted[0]
                for dup in same_sorted[1:]:
                    if not safety.is_safe_to_delete(dup["path"]):
                        continue
                    items.append(Item(
                        path=dup["path"], size=dup["size"], kind="duplicates",
                        risk=RISK_CAUTION, reason_key="duplicate",
                        reason_params={"keep": os.path.basename(keeper["path"]),
                                       "hash": h[:12]},
                        mtime=dup["mtime"], ext=dup["ext"],
                    ).to_dict())
            self.progress("dup", "")
        items.sort(key=lambda x: x["size"], reverse=True)
        return items

    def _find_large(self, files: list[dict]) -> list[dict]:
        big = [f for f in files if f["size"] >= LARGE_FILE_THRESHOLD]
        return self._mk_items(big, "large", RISK_DANGER, "large_file")

    def _find_old_downloads(self, files: list[dict], folders) -> list[dict]:
        cutoff = time.time() - OLD_DOWNLOAD_DAYS * 86400
        if folders.downloads and os.path.isdir(folders.downloads):
            old = [f for f in files
                   if f["mtime"] < cutoff
                   and os.path.abspath(f["path"]).startswith(os.path.abspath(folders.downloads))]
            return self._mk_items(old, "old_downloads", RISK_DANGER, "old_download")
        return []

    def _find_build_dirs(self, folders) -> list[dict]:
        items: list[dict] = []
        roots = [folders.home] if folders.home else []
        # نفحص الجذور الشخصية بس depth محدود
        for root in roots:
            for dirpath, dirnames, filenames in self._walk(root):
                depth = os.path.relpath(dirpath, root).count(os.sep)
                if depth > 6:
                    dirnames[:] = []
                    continue
                base = os.path.basename(dirpath)
                if base in BUILD_DIR_NAMES and not safety.is_sensitive_name(dirpath):
                    size = self._dirsize_quick(dirpath)
                    if size > 5 * 1024 * 1024:
                        items.append(Item(
                            path=dirpath, size=size, kind="build",
                            risk=RISK_CAUTION, reason_key="build_dir",
                        ).to_dict())
                    # ما ننزل جواها - خلصنا منها
                    dirnames[:] = []
        items.sort(key=lambda x: x["size"], reverse=True)
        return items

    def _dirsize_quick(self, path: str) -> int:
        total = 0
        for dirpath, dirnames, filenames in os.walk(path, followlinks=False):
            dirnames[:] = [d for d in dirnames
                           if not os.path.islink(os.path.join(dirpath, d))]
            for name in filenames:
                try:
                    total += os.lstat(os.path.join(dirpath, name)).st_size
                except OSError:
                    continue
        return total

    def _find_empty_dirs(self, folders) -> list[dict]:
        items: list[dict] = []
        for root in [folders.downloads, folders.desktop, folders.documents]:
            if not root or not os.path.isdir(root):
                continue
            for dirpath, dirnames, filenames in self._walk(root):
                if not dirnames and not filenames and dirpath != root:
                    if not safety.is_sensitive_name(dirpath):
                        items.append(Item(
                            path=dirpath, size=4096, kind="empty_dirs",
                            risk=RISK_SAFE, reason_key="empty_dir",
                        ).to_dict())
        return items[:500]  # سقف معقول


def default_large_threshold() -> int:
    return LARGE_FILE_THRESHOLD