#!/usr/bin/env bash
set -euo pipefail
# Skip duplicate launch when Codespaces invokes postStart more than once.
if python -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8000/api/health", timeout=2)' >/dev/null 2>&1; then
  exit 0
fi
nohup python -m uvicorn hydrofly.api:app --host 0.0.0.0 --port 8000 > /tmp/hydrofly-server.log 2>&1 < /dev/null &
