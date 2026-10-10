"""غلاف سطح المكتب: يفتح نافذة تطبيق حقيقية بدون متصفح.

ما يفعله هذا الملف:
- يشغّل الخادم المحلي في خيط مستقل على منفذ حر
- يفتح نافذة بلا إطار نظام مع شريط عنوان خاص وأزرار تحكم
- يوفّر جسرا بين الواجهة ولغة بايثون للتحكم بالنافذة
- يحترم الإعداد --native-frame لاستخدام إطار النظام
"""

from __future__ import annotations

import argparse
import socket
import sys
import threading
import time
from pathlib import Path

# نضيف جذر المشروع للاستيراد قبل أي شيء آخر
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from meras import __version__          # noqa: E402
from meras.server import Handler       # noqa: E402
from http.server import ThreadingHTTPServer  # noqa: E402

BG_DARK = "#070816"
BG_LIGHT = "#eef1fb"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for(port: int, timeout: float = 8.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.4):
                return True
        except OSError:
            time.sleep(0.08)
    return False


class Bridge:
    """دوال تستدعيها الواجهة من داخل النافذة."""

    def __init__(self, window_holder: dict):
        self._holder = window_holder

    def app_info(self) -> dict:
        return {"version": __version__, "mode": "desktop"}

    def close_window(self) -> None:
        w = self._holder.get("window")
        if w is not None:
            try:
                w.destroy()
            except Exception:  # noqa: BLE001
                pass

    def minimize_window(self) -> None:
        w = self._holder.get("window")
        if w is not None:
            try:
                w.minimize()
            except Exception:  # noqa: BLE001
                pass

    def toggle_maximize(self) -> bool:
        w = self._holder.get("window")
        if w is not None:
            try:
                if w.is_fullscreen:
                    w.restore()
                else:
                    w.maximize()
                return bool(w.is_fullscreen)
            except Exception:  # noqa: BLE001
                return False
        return False


def build_url() -> tuple[str, ThreadingHTTPServer]:
    port = _free_port()
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    _wait_for(port)
    return f"http://127.0.0.1:{port}/", httpd


def main() -> int:
    ap = argparse.ArgumentParser(prog="meras", description="Meras desktop app")
    ap.add_argument("--native-frame", action="store_true",
                    help="use the system window frame instead of the custom one")
    ap.add_argument("--debug", action="store_true", help="print the internal URL")
    args = ap.parse_args()

    try:
        import webview  # noqa: PLC0415
    except ImportError:
        print("pywebview is required for desktop mode: pip install pywebview")
        return 2

    url, httpd = build_url()
    if args.debug:
        print("internal url:", url)
        print("open this in a browser only for debugging.")

    holder: dict = {}
    bridge = Bridge(holder)

    # شاشة الإقلاع تظهر داخل النافذة نفسها ثم تختفي، بلا أي إعادة تحميل
    screen = f"{url}?boot=1"

    window = webview.create_window(
        "Meras",
        screen,
        js_api=bridge,
        width=1180,
        height=820,
        min_size=(940, 660),
        frameless=not args.native_frame,
        easy_drag=False,
        background_color=BG_DARK,
        on_top=False,
    )
    holder["window"] = window

    try:
        webview.start()
    finally:
        try:
            httpd.shutdown()
        except Exception:  # noqa: BLE001
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())