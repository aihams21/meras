#!/usr/bin/env python3
"""نقطة تشغيل ميراس.

وضع سطح المكتب (افتراضي): يفتح نافذة تطبيق حقيقية بلا متصفح.
وضع المتصفح: --web يفتح الصفحة في المتصفح (للتطوير فقط).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


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