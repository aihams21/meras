#!/usr/bin/env python3
"""نقطة تشغيل ميراس.

وضع سطح المكتب (افتراضي): يفتح نافذة تطبيق حقيقية بلا متصفح.
وضع المتصفح: --web يفتح الصفحة في المتصفح (للتطوير فقط).
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# النسخة المحمولة بتجيب pywebview و bottle جوّاها بمجلد vendor.
# لازم هالمجلد يسبق أي نسخة مثبّتة على الجهاز، وإلا البرنامج
# بيحمل pywebview من النظام وبيفشل عند المستخدم يلي ما عنده فيها.
_VENDOR = ROOT / "vendor"
if _VENDOR.is_dir():
    sys.path.insert(0, str(_VENDOR))


def main() -> int:
    args = sys.argv[1:]
    if "--web" in args:
        from meras.server import run
        run(open_browser=True)
        return 0
    from meras.desktop import main as desktop_main
    return desktop_main()


if __name__ == "__main__":
    raise SystemExit(main())