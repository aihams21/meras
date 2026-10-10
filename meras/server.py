"""خادم محلي: يقدّم الواجهة ويوفّر واجهة برمجية بسيطة.

يشتغل على 127.0.0.1 فقط، ويفتح المتصفح تلقائياً عند التشغيل.
"""

from __future__ import annotations

import json
import socket
import threading
import time
import webbrowser
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from . import quarantine, safety
from .platform_info import list_drives, system_info, user_folders
from .scanner import Scanner

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

_scan_state = {
    "running": False,
    "phase": "idle",
    "detail": "",
    "progress": 0.0,
    "updated_at": 0.0,
}
_scan_lock = threading.Lock()
_scan_result: dict = {}
_scan_thread: threading.Thread | None = None


def _set_progress(phase: str, detail: str, progress: float | None = None) -> None:
    with _scan_lock:
        _scan_state["phase"] = phase
        _scan_state["detail"] = detail
        if progress is not None:
            # التقدّم لا يرجع للخلف أبداً حتى لو تأخّرت رسالة
            try:
                value = float(progress)
            except (TypeError, ValueError):
                return
            _scan_state["progress"] = max(_scan_state["progress"], min(1.0, value))
        _scan_state["updated_at"] = time.time()


def start_scan() -> dict:
    global _scan_thread
    with _scan_lock:
        if _scan_state["running"]:
            return {"status": "already_running"}
        _scan_state["running"] = True
        _scan_state["phase"] = "start"
        _scan_state["progress"] = 0.0
        _scan_state["detail"] = ""
        _scan_state["updated_at"] = time.time()

    def worker():
        global _scan_result
        scanner = Scanner(progress=_set_progress)
        try:
            _scan_result = scanner.scan_all()
            _set_progress("done", "", 1.0)
        except Exception as exc:  # noqa: BLE001 - نعرض الخطأ للمستخدم
            _scan_result = {"error": str(exc)}
            _set_progress("error", str(exc), 1.0)
        finally:
            with _scan_lock:
                _scan_state["running"] = False

    _scan_thread = threading.Thread(target=worker, daemon=True)
    _scan_thread.start()
    return {"status": "started"}


class Handler(BaseHTTPRequestHandler):
    server_version = "Meras"

    def log_message(self, fmt, *args):  # silence console noise
        pass

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path):
        try:
            body = path.read_bytes()
        except OSError:
            self.send_error(404)
            return
        ctype = {
            ".html": "text/html; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".svg": "image/svg+xml",
            ".json": "application/json; charset=utf-8",
        }.get(path.suffix, "application/octet-stream")
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict:
        try:
            n = int(self.headers.get("Content-Length") or 0)
            if n <= 0:
                return {}
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except (ValueError, json.JSONDecodeError):
            return {}

    # ---------- routes ----------
    def do_GET(self):
        route = urlparse(self.path).path

        if route in ("/", "/index.html"):
            self._send_file(WEB_DIR / "index.html")
        elif route == "/api/system":
            self._send_json({
                "system": system_info(),
                "folders": user_folders().to_dict(),
                "drives": [d.to_dict() for d in list_drives()],
            })
        elif route == "/api/scan/status":
            with _scan_lock:
                self._send_json(dict(_scan_state))
        elif route == "/api/scan/result":
            self._send_json(_scan_result if _scan_result else {"status": "no_result"})
        elif route == "/api/quarantine":
            self._send_json({
                "entries": quarantine.list_quarantine(),
                "size": quarantine.quarantine_size(),
            })
        elif route.startswith("/static/"):
            name = route[len("/static/"):]
            if "/" in name or ".." in name:
                self.send_error(400)
                return
            self._send_file(WEB_DIR / name)
        else:
            self.send_error(404)

    def do_POST(self):
        route = urlparse(self.path).path
        body = self._body()

        if route == "/api/scan/start":
            self._send_json(start_scan())
        elif route == "/api/quarantine/add":
            paths = body.get("paths") or []
            # تحقق مزدوج من الأمان
            verified = []
            for p in paths:
                ok, _ = safety.quarantine_allowed(p)
                if ok:
                    verified.append(p)
            result = quarantine.quarantine_paths(verified)
            self._send_json(result.to_dict())
        elif route == "/api/quarantine/restore":
            ids = body.get("ids") or []
            self._send_json(quarantine.restore_entries(ids))
        elif route == "/api/scan/cancel":
            self._send_json({"status": "cancel_requested"})
        else:
            self.send_error(404)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def run(open_browser: bool = True):
    port = _free_port()
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/"
    print("=" * 56)
    print("  MERAS - space map & cleaner")
    print(f"  Open: {url}")
    print("  Press Ctrl+C to stop")
    print("=" * 56)
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")
        httpd.server_close()