"""السلة: نقل الملفات إلى منطقة عزل قابلة للاسترجاع.

الفلسفة: التطبيق ما بيحذف نهائي أبداً. كل شي بينقل لـQuarantine، ومعه manifest
يسجّل المسار الأصلي حتى لو حذفت الملفات بعد أسبوع، تقدر ترجّعها بضغطة.
"""

from __future__ import annotations

import json
import os
import shutil
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path

from . import safety

QUARANTINE_DIR_NAME = ".meras_quarantine"


def quarantine_root() -> Path:
    base = Path.home() / QUARANTINE_DIR_NAME
    base.mkdir(parents=True, exist_ok=True)
    (base / "files").mkdir(exist_ok=True)
    return base


def manifest_path() -> Path:
    return quarantine_root() / "manifest.json"


def _load_manifest() -> list[dict]:
    mp = manifest_path()
    if not mp.exists():
        return []
    try:
        data = json.loads(mp.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_manifest(entries: list[dict]) -> None:
    mp = manifest_path()
    tmp = mp.with_suffix(".tmp")
    tmp.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(mp)


@dataclass
class QuarantineResult:
    moved: list[dict]
    failed: list[dict]
    bytes_freed: int

    def to_dict(self) -> dict:
        return {
            "moved_count": len(self.moved),
            "failed_count": len(self.failed),
            "bytes_freed": self.bytes_freed,
            "moved": self.moved,
            "failed": self.failed,
        }


def quarantine_paths(paths: list[str]) -> QuarantineResult:
    """ينقل الملفات/المجلدات إلى العزل. آمن 100%.

    - ما بيحذف نهائي
    - بيسجّل كل عملية بالـmanifest للاسترجاع
    - بيفحص كل مسار عبر طبقة الأمان قبل النقل
    """
    root = quarantine_root()
    files_dir = root / "files"
    entries = _load_manifest()
    moved, failed = [], []
    freed = 0

    for src in paths:
        ok, why = safety.quarantine_allowed(src)
        if not ok:
            failed.append({"path": src, "error": f"refused: {why}"})
            continue
        if not os.path.exists(src):
            failed.append({"path": src, "error": "not found"})
            continue

        entry_id = uuid.uuid4().hex[:12]
        dest = files_dir / entry_id
        try:
            size = _size_of(src)
            if os.path.isdir(src):
                shutil.move(src, dest)
            else:
                shutil.move(src, dest)
            freed += size
            entry = {
                "id": entry_id,
                "original_path": os.path.abspath(src),
                "stored_as": str(dest.relative_to(root)),
                "size": size,
                "is_dir": os.path.isdir(dest),
                "quarantined_at": time.time(),
            }
            entries.append(entry)
            moved.append(entry)
        except (OSError, shutil.Error) as exc:
            failed.append({"path": src, "error": str(exc)})

    _save_manifest(entries)
    return QuarantineResult(moved, failed, freed)


def restore_entries(entry_ids: list[str]) -> dict:
    """يرجّع ملفات من العزل لأماكنها الأصلية."""
    entries = _load_manifest()
    root = quarantine_root()
    restored, failed = [], []

    remaining = []
    for entry in entries:
        if entry["id"] not in entry_ids:
            remaining.append(entry)
            continue
        stored = root / entry["stored_as"]
        original = Path(entry["original_path"])
        if not stored.exists():
            failed.append({"path": entry["original_path"], "error": "gone from quarantine"})
            continue
        try:
            original.parent.mkdir(parents=True, exist_ok=True)
            if original.exists():
                # تعارض: ننقل الأصلي الجديد لعنعصر مؤقت
                backup = original.with_name(original.name + ".restored_backup")
                shutil.move(str(original), str(backup))
                shutil.move(str(stored), str(original))
            else:
                shutil.move(str(stored), str(original))
            restored.append(entry["original_path"])
        except (OSError, shutil.Error) as exc:
            failed.append({"path": entry["original_path"], "error": str(exc)})

    _save_manifest(remaining)
    return {"restored_count": len(restored), "restored": restored, "failed": failed}


def list_quarantine() -> list[dict]:
    """يسرد كل اللي بالعزل حالياً."""
    entries = _load_manifest()
    root = quarantine_root()
    out = []
    for entry in entries:
        stored = root / entry["stored_as"]
        entry["present"] = stored.exists()
        out.append(entry)
    return out


def quarantine_size() -> int:
    root = quarantine_root()
    total = 0
    files_dir = root / "files"
    if not files_dir.exists():
        return 0
    for dirpath, _, filenames in os.walk(files_dir):
        for name in filenames:
            try:
                total += os.lstat(os.path.join(dirpath, name)).st_size
            except OSError:
                continue
    return total


def _size_of(path: str) -> int:
    if os.path.isfile(path):
        try:
            return os.lstat(path).st_size
        except OSError:
            return 0
    total = 0
    for dirpath, _, filenames in os.walk(path, followlinks=False):
        for name in filenames:
            try:
                total += os.lstat(os.path.join(dirpath, name)).st_size
            except OSError:
                continue
    return total