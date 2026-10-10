#!/usr/bin/env bash
# تشغيل ميراس على لينكس
set -e
cd "$(dirname "$0")"
PY=python3
command -v $PY >/dev/null 2>&1 || { echo "نحتاج python3 لتشغيل التطبيق"; exit 1; }
exec $PY run.py "$@"