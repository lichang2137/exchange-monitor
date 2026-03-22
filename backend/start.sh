#!/bin/bash
cd /root/.openclaw/workspace/memory/projects/exchange-monitor/backend
set -a
source /root/.openclaw/workspace/.env
set +a
exec ./venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
