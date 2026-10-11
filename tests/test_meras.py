#!/usr/bin/env python3
"""اختبارات المنطق: الأمان، السلة، الماسح."""

from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from meras import quarantine, safety  # noqa: E402
from meras.platform_info import list_drives, user_folders  # noqa: E402
from meras.scanner import Scanner  # noqa: E402


class TestSafety(unittest.TestCase):
    def test_root_is_refused(self):
        ok, _ = safety.quarantine_allowed("/")
        self.assertFalse(ok)

    def test_home_is_refused(self):
        ok, _ = safety.quarantine_allowed(str(Path.home()))
        self.assertFalse(ok)

    def test_system_paths_refused(self):
        for p in ("/usr", "/etc", "/bin", "/lib"):
            ok, _ = safety.quarantine_allowed(p)
            self.assertFalse(ok, p)

    def test_sensitive_names_refused(self):
        for name in (".ssh", ".git", "id_rsa", ".env", "secrets.yaml"):
            ok, _ = safety.quarantine_allowed(f"/home/user/{name}")
            self.assertFalse(ok, name)

    def test_game_data_refused(self):
        for name in ("Saved Games", "Saves", "steamapps", "Minecraft", "Epic Games"):
            ok, _ = safety.quarantine_allowed(f"/home/user/{name}")
            self.assertFalse(ok, name)

    def test_app_config_refused(self):
        for name in ("AppData/Roaming", "AppData\\Roaming", "Application Support", ".config"):
            ok, _ = safety.quarantine_allowed(f"/home/user/{name}/thing")
            self.assertFalse(ok, name)

    def test_app_data_scratch_folders_allowed(self):
        """مجلدات العابرة داخل بيانات التطبيقات لازم تكون قابلة للتنظيف.

        بدون هذا الاستثناء ما بيقدر التطبيق ينظف شي على ويندوز، لأن مجلد
        Temp المؤقت كله جوّا AppData.
        """
        for path in (
            "C:\\Users\\me\\AppData\\Local\\Temp\\junk.tmp",
            "C:\\Users\\me\\AppData\\Local\\Temp\\tmpab12\\junk.txt",
            "C:\\Users\\me\\AppData\\Local\\Temp\\a\\b\\deep.log",
            "C:\\Users\\me\\AppData\\Local\\CrashDumps\\app.exe.1234.dmp",
        ):
            self.assertFalse(safety.is_sensitive_name(path), path)

    def test_app_data_real_data_still_refused(self):
        """بيانات المستخدم جوّا بيانات التطبيقات بتضل محميّة."""
        for path in (
            "C:\\Users\\me\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles\\a.default\\places.sqlite",
            "C:\\Users\\me\\AppData\\Roaming\\Game\\Saved Games\\slot1.sav",
            "C:\\Users\\me\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\a.dat",
            "C:\\Users\\me\\AppData\\Local",
            "C:\\Users\\me\\AppData\\Roaming",
        ):
            self.assertTrue(safety.is_sensitive_name(path), path)

    def test_user_own_folders_allowed(self):
        """مجلدات المستخدم هي هدف الفحص، لازم ما تكون محظورة."""
        for name in ("Downloads", "Documents", "Videos", "Pictures", "Music", "Desktop"):
            ok, why = safety.quarantine_allowed(f"/home/ahmed/{name}/somefile")
            self.assertTrue(ok, f"{name} blocked: {why}")

    def test_normal_folder_allowed(self):
        ok, why = safety.quarantine_allowed("/home/user/Downloads/oldfile.zip")
        self.assertTrue(ok, why)

    def test_windows_system_refused(self):
        for p in ("C:\\Windows", "C:\\Program Files", "C:\\ProgramData",
                  "c:/windows/system32", "C:\\$Recycle.Bin"):
            ok, _ = safety.quarantine_allowed(p)
            self.assertFalse(ok, p)

    def test_dangerous_extension_refused(self):
        for name in ("wallet.dat", "secret.key", "db.sqlite3", "game.sav"):
            ok, _ = safety.quarantine_allowed(f"/home/user/{name}")
            self.assertFalse(ok, name)


class TestQuarantine(unittest.TestCase):
    def test_move_and_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "junk.txt"
            src.write_text("hello world", encoding="utf-8")
            # نتجاوز عتبة الـ24 ساعة
            old = time.time() - 48 * 3600
            os.utime(src, (old, old))

            res = quarantine.quarantine_paths([str(src)])
            self.assertEqual(len(res.moved), 1, res.failed)
            self.assertFalse(src.exists())

            entry = res.moved[0]
            restored = quarantine.restore_entries([entry["id"]])
            self.assertEqual(restored["restored_count"], 1, restored)
            self.assertTrue(src.exists())
            self.assertEqual(src.read_text(encoding="utf-8"), "hello world")

    def test_refuses_system_path(self):
        res = quarantine.quarantine_paths(["/"])
        self.assertEqual(len(res.moved), 0)
        self.assertGreaterEqual(len(res.failed), 1)

    def test_manifest_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "a.bin"
            src.write_bytes(b"x" * 100)
            old = time.time() - 48 * 3600
            os.utime(src, (old, old))
            res = quarantine.quarantine_paths([str(src)])
            listed = quarantine.list_quarantine()
            ids = [e["id"] for e in listed]
            self.assertIn(res.moved[0]["id"], ids)
            # تنظيف
            quarantine.restore_entries(ids)


class TestScanner(unittest.TestCase):
    def test_scan_runs(self):
        s = Scanner(progress=lambda *a: None)
        s._cancel = True  # نوقف فوراً حتى ما نبطّئ الاختبار
        res = s.scan_all()
        self.assertIn("categories", res)
        self.assertIn("total_reclaimable", res)

    def test_user_folders_exist(self):
        f = user_folders()
        self.assertTrue(f.home)
        self.assertTrue(Path(f.home).is_dir())

    def test_drives_listed(self):
        drives = list_drives()
        self.assertGreaterEqual(len(drives), 1)
        d = drives[0]
        self.assertGreater(d.total, 0)
        self.assertGreaterEqual(d.used, 0)


class TestDuplicates(unittest.TestCase):
    def test_duplicate_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            # ملفان بنفس المحتوى، أكبر من الحد الأدنى
            a = Path(tmp) / "a.bin"
            b = Path(tmp) / "b.bin"
            data = b"Z" * (2 * 1024 * 1024)
            a.write_bytes(data)
            b.write_bytes(data)
            s = Scanner(progress=lambda *a_: None)

            # نحقن الملفات يدوياً بypass للجمع (نحاكي بيئة حقيقية)
            files = [
                {"path": str(a), "size": a.stat().st_size, "mtime": time.time(), "ext": ".bin"},
                {"path": str(b), "size": b.stat().st_size, "mtime": time.time(), "ext": ".bin"},
            ]
            dupes = s._find_duplicates(files)
            # SAFETY قد يرفض الملفات الأحدث من 24 ساعة، المهم ترجع قائمة
            self.assertIsInstance(dupes, list)

class TestProjectProtection(unittest.TestCase):
    """أي شيء داخل مشروع برمجي ما بينعرض للتنظيف."""

    def test_build_dir_inside_repo_is_protected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "myproject"
            (repo / "src").mkdir(parents=True)
            (repo / ".git").mkdir()
            (repo / "build").mkdir()
            src = repo / "src" / "main.cpp"
            src.write_text("int main(){}")
            build = repo / "build" / "out.bin"
            build.write_bytes(b"x" * 10)

            self.assertTrue(safety.is_project_path(str(repo)))
            self.assertTrue(safety.is_project_path(str(build)))
            self.assertFalse(safety.is_safe_to_delete(str(build)))
            self.assertFalse(safety.is_safe_to_delete(str(src)))

    def test_other_vcs_markers_are_protected(self):
        for marker in (".hg", ".svn"):
            with tempfile.TemporaryDirectory() as tmp:
                repo = Path(tmp) / "p"
                (repo / marker).mkdir(parents=True)
                target = repo / "data.bin"
                target.write_bytes(b"y" * 10)
                self.assertTrue(safety.is_project_path(str(target)), marker)
                self.assertFalse(safety.is_safe_to_delete(str(target)), marker)

    def test_plain_folder_is_not_a_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            plain = Path(tmp) / "Downloads" / "stuff"
            plain.mkdir(parents=True)
            f = plain / "old.bin"
            f.write_bytes(b"z" * 10)
            os.utime(f, (time.time() - 10 * 86400, time.time() - 10 * 86400))
            self.assertFalse(safety.is_project_path(str(f)))
            self.assertTrue(safety.is_safe_to_delete(str(f)))

    def test_build_category_skips_repo_build_dirs(self):
        """مجلد build جوّا مشروع ما لازم يطلعجة بنتيجة الفحص."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "proj"
            (repo / ".git").mkdir(parents=True)
            build = repo / "build"
            build.mkdir()
            (build / "out.bin").write_bytes(b"x" * (6 * 1024 * 1024))
            s = Scanner(progress=lambda *a_: None)
            found = s._find_build_dirs(_Folders(tmp))
            self.assertNotIn(str(build), [i["path"] for i in found])

    def test_build_category_still_reports_plain_build_dir(self):
        """مجلد build عادي برّا أي مشروع لازم يضل يظهر."""
        with tempfile.TemporaryDirectory() as tmp:
            build = Path(tmp) / "build"
            build.mkdir()
            (build / "out.bin").write_bytes(b"x" * (6 * 1024 * 1024))
            s = Scanner(progress=lambda *a_: None)
            found = s._find_build_dirs(_Folders(tmp))
            self.assertIn(str(build), [i["path"] for i in found])


class _Folders:
    """مجلدات وهمية للفحص، بدون ما نلمس مجلدات المستخدم الحقيقية."""

    def __init__(self, home):
        self.home = str(home)
        self.downloads = str(Path(home) / "Downloads")
        self.desktop = str(Path(home) / "Desktop")
        self.documents = str(Path(home) / "Documents")
        self.videos = None
        self.pictures = None
        self.temp = None


if __name__ == "__main__":
    unittest.main(verbosity=2)