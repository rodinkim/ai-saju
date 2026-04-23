#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  echo "Usage: ./start.sh [back|front|b|f]"
  exit 1
}

if [[ "${1:-}" == "" ]]; then
  usage
fi

case "$1" in
  back|b)
    cd "$ROOT_DIR/backend"
    exec uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ;;
  front|f)
    cd "$ROOT_DIR/frontend"
    exec npm run dev -- --host 0.0.0.0 --port 80
    ;;
  *)
    usage
    ;;
esac
