#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
exec uvicorn app:app --host 0.0.0.0 --port 8000
