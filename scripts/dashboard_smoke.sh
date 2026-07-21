#!/usr/bin/env bash

set -euo pipefail

backend_log="$(mktemp)"
frontend_log="$(mktemp)"
backend_pid=""
frontend_pid=""
python_bin="${PYTHON_BIN:-python}"

cleanup() {
  if [[ -n "$frontend_pid" ]]; then
    kill "$frontend_pid" 2>/dev/null || true
    wait "$frontend_pid" 2>/dev/null || true
  fi
  if [[ -n "$backend_pid" ]]; then
    kill "$backend_pid" 2>/dev/null || true
    wait "$backend_pid" 2>/dev/null || true
  fi
  npx --prefix frontend playwright-cli close 2>/dev/null || true
  rm -f "$backend_log" "$frontend_log"
}
trap cleanup EXIT

wait_for_url() {
  local url="$1"
  for _ in $(seq 1 60); do
    if curl --fail --silent "$url" >/dev/null; then return 0; fi
    sleep 1
  done
  return 1
}

PYTHONPATH=. "$python_bin" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 >"$backend_log" 2>&1 &
backend_pid=$!
BACKEND_URL=http://127.0.0.1:8000 npm --prefix frontend run dev -- --hostname 127.0.0.1 --port 3000 >"$frontend_log" 2>&1 &
frontend_pid=$!

if ! wait_for_url http://127.0.0.1:8000/health; then
  sed -n '1,160p' "$backend_log"
  exit 1
fi
if ! wait_for_url http://127.0.0.1:3000; then
  sed -n '1,160p' "$frontend_log"
  exit 1
fi

npx --prefix frontend playwright-cli open http://127.0.0.1:3000 >/dev/null
snapshot="$(npx --prefix frontend playwright-cli snapshot)"

for expected_text in "패턴별 champion 모델" "주문 의사결정 backtest" "Croston/SBA"; do
  if ! grep -Fq "$expected_text" <<<"$snapshot"; then
    echo "Dashboard text was not rendered: $expected_text"
    echo "$snapshot"
    exit 1
  fi
done

echo "Dashboard browser smoke check passed."
