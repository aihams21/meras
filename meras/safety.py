"""طبقة الأمان: تمنع المساس بأي مسار حسّاس.

القاعدة الذهبية: الافتراضي الحذر. أي مسار غير آمن 100% ما بيمسّه التطبيق.
المستخدم لازم يفتح المسار يدوياً إذا بده ينظّفه.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

# مسارات نظام ما بنمسّها أبداً
SYSTEM_PREFIXES_LINUX = [
    "/", "/bin", "/boot", "/dev", "/etc", "/home", "/lib", "/lib32", "/lib64",
    "/media", "/mnt", "/opt", "/proc", "/root", "/run", "/sbin", "/srv",
    "/sys", "/usr", "/var", "/System", "/Applications", "/Library",
    "/private", "/Volumes", "/Network", "/cores", "/dev",
]

SYSTEM_PREFIXES_WINDOWS = [
    "c:\\windows", "c:\\program files", "c:\\program files (x86)",
    "c:\\programdata", "c:\\$recycle.bin", "c:\\system volume information",
    "c:\\recovery", "c:\\boot", "c:\\perfmon",
]

# أسماء مجلدات/ملفات حساسة - حتى لو كانت داخل مجلد_scanned
# ملاحظة: مجلدات المستخدم المعروفة (Downloads/Documents/Videos...) مش محفوظة
# هنا عن قصد: هيTargetsالفحص الأساسية، وحمايتها تكون kekعة من العرض الصريح
# لكل ملف على حدة (مافيش حذف نهائي).
SENSITIVE_NAMES = {
    # نظام ومشاريع
    ".git", ".hg", ".svn", "node_modules", ".venv", "venv", ".tox",
    # أسرار ومفاتيح
    ".ssh", ".gnupg", ".aws", ".azure", ".kube", ".docker",
    ".config", ".password-store", ".vault", ".keepass", ".bitwarden",
    "id_rsa", "id_ed25519", "id_ecdsa", "authorized_keys", "known_hosts",
    ".env", "credentials", "secrets",
    # بيانات الألعاب والتطبيقات
    "appdata", "roaming", "local low", "application support",
    "saved games", "save games", "saves", "sav", "game saves",
    "minecraft", "steamapps", "epic games", "battle.net", "origin",
    ".mozilla", "keychain", "library",
}

# game / project data - لا تُلمس
SENSITIVE_EXTENSIONS = {
    ".wallet", ".dat", ".sqlite", ".sqlite3", ".db", ".key", ".pem",
    ".crt", ".p12", ".pfx", ".keystore", ".kdbx", ".rdp", ".vhd", ".vhdx",
    ".iso", ".img", ".dmg", ".sav", ".save", ".es3", ".pak",
}

# ext that are safe to clean (temporary / cache / log)
SAFE_TEMP_EXTENSIONS = {
    ".tmp", ".temp", ".log", ".old", ".bak", ".cache", ".dmp", ".stackdump",
    ".part", ".crdownload", ".download", ".nib", ".swp",
}

SAFE_TEMP_DIRS = {
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "node_modules/.cache", ".gradle/caches", "target/debug",
}


def _norm(path: str) -> str:
    return os.path.normcase(os.path.abspath(os.path.expanduser(path)))


def _canon(path: str) -> str:
    """تطبيع مستقل عن النظام: فاصل واحد، بلا شرطات مكررة، بحروف صغيرة."""
    p = os.path.expanduser(str(path)).replace("\\", "/")
    while "//" in p:
        p = p.replace("//", "/")
    p = p.rstrip("/")
    return p.casefold() or "/"


def is_system_path(path: str) -> bool:
    """هل المسار جزء من نظام التشغيل؟"""
    c = _canon(path)

    # مسارات ويندوز: تُفحص حتى على لينكس (تحت Wine أو باختبارات)
    looks_windows = bool(re.match(r"^[a-z]:/", c)) or os.name == "nt"
    if looks_windows:
        for pref in SYSTEM_PREFIXES_WINDOWS:
            pc = _canon(pref)
            if c == pc or c.startswith(pc + "/"):
                return True
        if c.startswith("//?/") or c.startswith("//./"):
            return True

    # على لينكس: الجذر ومجلدات النظام محمية، أما /home و /var فليست
    root_protected = {
        "/", "/bin", "/boot", "/dev", "/etc", "/lib", "/lib32", "/lib64",
        "/proc", "/sbin", "/sys", "/usr", "/run", "/var/run",
        "/System", "/Applications", "/Library", "/private/etc", "/private/var/db",
    }
    if c in root_protected:
        return True
    return any(c.startswith(pref + "/") for pref in root_protected if pref != "/")


def is_sensitive_name(path: str) -> bool:
    """هل الاسم (أحد مكوّنات المسار) حسّاس؟"""
    # نفصل على الفاصلين حتى لو كنا على نظام ثاني: نتعامل مع مسارات ويندوز
    # على لينكس أيضاً (اختبارات، أو تشغيل تحت Wine)
    raw = str(path).replace("\\", "/")
    parts = [p for p in raw.split("/") if p]
    low_parts = [p.lower() for p in parts]
    for part in low_parts:
        if part in SENSITIVE_NAMES:
            return True
    # فحص لاحقة الملف
    base = low_parts[-1] if low_parts else ""
    for ext in SENSITIVE_EXTENSIONS:
        if base.endswith(ext):
            return True
    # كلمات dangerous within name
    for danger in ("password", "secret", "credential", "token", "wallet",
                   "keystore", "private_key", "ssh", "gnupg"):
        if danger in base:
            return True
    return False


def is_safe_to_delete(path: str) -> bool:
    """البوابة النهائية: هل ينفع التطبيق يعرض هذا المسار للتنظيف؟"""
    if not path or not os.path.exists(path):
        return False
    p = _norm(path)

    # 1) ممنوع لمس نظام التشغيل
    if is_system_path(p):
        return False

    # 2) ممنوع المسار الجذر أو الـhome مباشرة
    home = _norm(str(Path.home()))
    if p == home or p == os.sep:
        return False

    # 3) ممنوع أي اسم حسّاس (system / game / project data)
    if is_sensitive_name(p):
        return False

    # 4) ممنوع أي ملف مدّته أقل من 24 ساعة (يمكن شغّال)
    try:
        st = os.lstat(p)
        import time
        age_hours = (time.time() - st.st_mtime) / 3600.0
        if age_hours < 24 and os.path.isfile(p):
            # ملف جديد - لا نقترح على المستخدم نحذف شي بالزبط
            return False
    except OSError:
        return False

    return True


def quarantine_allowed(path: str) -> tuple[bool, str]:
    """يفحص المسار قبل أي عملية نقل. يرجع (مسموح، سبب الرفض).

    نفحص المسار الخام أولاً: abspath على لينكس يحوّل "C:\\Windows" إلى مسار
    غريب ويفقد حرف القرص، فيفلت الفحص.
    """
    if not path:
        return False, "empty path"
    if is_system_path(path):
        return False, "system path refused"
    if is_sensitive_name(path):
        return False, "sensitive name refused"
    p = _norm(path)
    if p in ("/", os.sep, _norm(str(Path.home()))):
        return False, "root/home refused"
    return True, "ok"