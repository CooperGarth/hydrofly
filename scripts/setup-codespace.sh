#!/usr/bin/env bash
set -euo pipefail
python -m pip install -r requirements-dev-lock.txt
python -m pip install --no-deps -e .
npm ci --prefix web
npm run build --prefix web
