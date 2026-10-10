"""معلومات النظام: نوع النظام، الأقراص، مجلدات المستخدم."""

from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

IS_WINDOWS = sys.platform.startswith("win")
IS_MACOS = sys.platform == "darwin"
IS_LINUX = not IS_WINDOWS and not IS_MACOS


def _dir_size(path: Path, stop_at: int = 0) -> int:
    """حجم مجلد بالبايت، مع حماية من الروابط الرمزية والlooops."""
    total = 0
    seen: set[tuple[int, int]] = set()
    for root, dirs, files in os.walk(path, followlinks=False):
        try:
            st = os.stat(root)
            key = (st.st_dev, st.st_ino)
            if key in seen:
                dirs[:] = []
                continue
            seen.add(key)
        except OSError:
            dirs[:] = []
            continue
        for name in files:
            fp = os.path.join(root, name)
            try:
                total += os.lstat(fp).st_size
            except OSError:
                continue
            if stop_at and total > stop_at:
                return total
    return total


@dataclass
class Drive:
    """قرص أو قسم."""

    path: str
    label: str
    total: int
    used: int
    free: int
    fstype: str = ""
    removable: bool = False
    mount_point: str = ""
    size_cache: dict = field(default_factory=dict)

    @property
    def used_pct(self) -> float:
        return (self.used / self.total * 100.0) if self.total else 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["used_pct"] = round(self.used_pct, 2)
        return d


@dataclass
class UserFolders:
    """المجلدات الشخصية لكل مستخدم، مع مستوى خطورتها."""

    home: str
    downloads: str = ""
    desktop: str = ""
    videos: str = ""
    pictures: str = ""
    documents: str = ""
    music: str = ""
    temp: str = ""
    trash: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def user_folders() -> UserFolders:
    """يكتشف مجلدات المستخدم حسب النظام."""
    home = Path.home()
    f = UserFolders(home=str(home))

    def pick(*names: str) -> str:
        for n in names:
            p = home / n
            if p.exists() and p.is_dir():
                return str(p)
        return ""

    f.downloads = pick("Downloads", "التنزيلات", "التنزيلات ")
    f.desktop = pick("Desktop", "سطح المكتب")
    f.videos = pick("Videos", "مقاطع الفيديو", "الفيديوهات")
    f.pictures = pick("Pictures", "الصور")
    f.documents = pick("Documents", "المستندات", "المستندت")
    f.music = pick("Music", "الموسيقى")

    if IS_WINDOWS:
        f.temp = os.environ.get("TEMP", "") or os.environ.get("TMP", "")
        f.trash = str(Path.home() / "$Recycle.Bin")
    elif IS_MACOS:
        f.temp = os.environ.get("TMPDIR", "")
        f.trash = str(home / ".Trash")
    else:
        f.temp = os.environ.get("TMPDIR", "/tmp") or "/tmp"
        f.trash = str(home / ".local" / "share" / "Trash" / "files")

    # fallback: نقرأ إعدادات XDG على لينكس
    if not IS_WINDOWS and not IS_MACOS:
        cfg = home / ".config" / "user-dirs.dirs"
        if cfg.exists():
            try:
                for line in cfg.read_text(encoding="utf-8", errors="ignore").splitlines():
                    if not line.startswith("XDG_") or "=" not in line:
                        continue
                    key, _, val = line.partition("=")
                    val = val.strip().strip('"').replace("$HOME", str(home))
                    name = key.upper()
                    if name == "XDG_DOWNLOAD_DIR" and not f.downloads:
                        f.downloads = val
                    elif name == "XDG_DESKTOP_DIR" and not f.desktop:
                        f.desktop = val
                    elif name == "XDG_VIDEOS_DIR" and not f.videos:
                        f.videos = val
                    elif name == "XDG_PICTURES_DIR" and not f.pictures:
                        f.pictures = val
                    elif name == "XDG_DOCUMENTS_DIR" and not f.documents:
                        f.documents = val
                    elif name == "XDG_MUSIC_DIR" and not f.music:
                        f.music = val
            except OSError:
                pass
    return f


def list_drives(include_removable: bool = True) -> list[Drive]:
    """يسرد الأقراص المتاحة حسب النظام."""
    out: list[Drive] = []
    seen: set[str] = set()

    def add(path: str, fstype: str = "", removable: bool = False, label: str = "") -> None:
        try:
            key = os.path.normcase(os.path.abspath(path))
            if key in seen:
                return
            seen.add(key)
            usage = shutil.disk_usage(path)
        except (OSError, ValueError):
            return
        if usage.total <= 0:
            return
        out.append(
            Drive(
                path=path,
                label=label or os.path.basename(path.rstrip("\\/")) or path,
                total=usage.total,
                used=usage.used,
                free=usage.free,
                fstype=fstype,
                removable=removable,
                mount_point=path,
            )
        )

    if IS_WINDOWS:
        for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            root = f"{letter}:\\"
            if os.path.exists(root):
                add(root, fstype="", removable=letter in ("D", "E", "F"))
    elif IS_MACOS:
        add("/", fstype="apfs")
        add("/System/Volumes/Data", fstype="apfs")
    else:
        try:
            mounts: dict[str, str] = {}
            with open("/proc/mounts", encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    parts = line.split()
                    if len(parts) < 3:
                        continue
                    mp = parts[1].replace("\\040", " ")
                    fstype = parts[2]
                    mounts[mp] = fstype
        except OSError:
            mounts = {}

        vfs_types = {
            "ext2", "ext3", "ext4", "btrfs", "xfs", "jfs", "reiserfs",
            "fuseblk", "ntfs", "ntfs3", "fat", "fat32", "exfat", "ufs",
        }
        skip_prefixes = (
            "/proc", "/sys", "/dev", "/run", "/snap", "/var/lib/docker",
            "/var/lib/containers", "/var/cache", "/var/log", "/tmp",
            "/System/Volumes/Preboot", "/System/Volumes/VM",
        )
        for mp, fstype in sorted(mounts.items()):
            if fstype not in vfs_types:
                continue
            if any(mp == p or mp.startswith(p + "/") for p in skip_prefixes):
                continue
            if not os.path.isdir(mp):
                continue
            removable = fstype.startswith("fuse") or "/media/" in mp or "/run/media/" in mp
            if removable and not include_removable:
                continue
            add(mp, fstype=fstype, removable=removable)

        if not out:
            add("/")

    return out


def system_info() -> dict:
    """ملخّص سريع عن النظام، يعرض في الواجهة."""
    import platform

    return {
        "platform": sys.platform,
        "os_name": platform.system(),
        "os_release": platform.release(),
        "arch": platform.machine(),
        "python": platform.python_version(),
        "home": str(Path.home()),
        "is_windows": IS_WINDOWS,
        "is_linux": IS_LINUX,
        "is_macos": IS_MACOS,
    }