#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[1/2] Build: vite build"
cd "${SCRIPT_DIR}"
npm run build

echo "[2/2] Deploy: Firebase Hosting (tojung)"
firebase deploy --only hosting:tojung

echo "Deploy complete: Firebase Hosting (tojung)"
