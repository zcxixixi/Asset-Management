#!/bin/bash
# Thin compatibility wrapper around the canonical Python pipeline CLI.

set -euo pipefail

TIME_OF_DAY="${1:-test}"
DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PATH="${VENV_PATH:-/Users/kaijimima1234/Desktop/nanobot/venv/bin/activate}"
SEND_TELEGRAM="${SEND_TELEGRAM:-1}"
AUTO_PUBLISH="${AUTO_PUBLISH:-0}"
ALERT_ON_FAILURE="${ALERT_ON_FAILURE:-1}"

if [ -f "$DIR/.env" ]; then
  set -a
  source "$DIR/.env"
  set +a
fi

if [ -f "$VENV_PATH" ]; then
  source "$VENV_PATH"
fi

cd "$DIR"

ARGS=("scripts/asset_pipeline.py" "run-cycle" "--time-of-day" "$TIME_OF_DAY")
if [ "$SEND_TELEGRAM" = "1" ]; then
  ARGS+=("--send-telegram")
else
  ARGS+=("--no-send-telegram")
fi
if [ "$AUTO_PUBLISH" = "1" ]; then
  ARGS+=("--publish")
else
  ARGS+=("--no-publish")
fi
if [ "$ALERT_ON_FAILURE" = "1" ]; then
  ARGS+=("--alert-on-failure")
else
  ARGS+=("--no-alert-on-failure")
fi

python3 "${ARGS[@]}"
