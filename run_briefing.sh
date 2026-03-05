#!/bin/bash
# Nanobot Asset-Management: scheduled pipeline + Telegram broadcaster
# Usage: ./run_briefing.sh morning|afternoon|evening

set -euo pipefail

TIME_OF_DAY="${1:-test}"
DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="$DIR/backups/cron_$(date +%Y%m%d_%H%M).log"
AUTO_PUBLISH="${AUTO_PUBLISH:-0}"
SEND_TELEGRAM="${SEND_TELEGRAM:-1}"
ALERT_ON_FAILURE="${ALERT_ON_FAILURE:-1}"
ALERT_LOG_LINES="${ALERT_LOG_LINES:-30}"
TARGET_BRANCH="${TARGET_BRANCH:-main}"
REMOTE_NAME="${REMOTE_NAME:-origin}"
VENV_PATH="${VENV_PATH:-/Users/kaijimima1234/Desktop/nanobot/venv/bin/activate}"
COMMIT_PREFIX="${COMMIT_PREFIX:-chore(data): sync portfolio data}"
PIPELINE_SCRIPT="${PIPELINE_SCRIPT:-scripts/extract_data.py}"
TELEGRAM_SCRIPT="${TELEGRAM_SCRIPT:-scripts/telegram_bot.py}"
DATA_FILES=("assets.xlsx" "src/data.json" "public/data.json")

mkdir -p "$DIR/backups"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"
}

send_failure_alert() {
  local exit_code="$1"
  local line="$2"
  local cmd="$3"

  if [ "${ALERT_ON_FAILURE}" != "1" ]; then
    return 0
  fi

  local token="${TELEGRAM_BOT_TOKEN:-}"
  local chat_id="${TELEGRAM_CHAT_ID:-}"
  if [ -z "$token" ] || [ -z "$chat_id" ]; then
    log "WARN: skip failure alert (missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID)"
    return 0
  fi

  local branch host
  branch="$(git branch --show-current 2>/dev/null || echo unknown)"
  host="$(hostname 2>/dev/null || echo unknown)"
  local log_tail
  log_tail="$(tail -n "${ALERT_LOG_LINES}" "$LOG" 2>/dev/null | sed 's/\r//g' | tail -c 1200)"

  local message
  message="Asset-Management pipeline FAILED
time_of_day=${TIME_OF_DAY}
host=${host}
branch=${branch}
exit_code=${exit_code}
line=${line}
command=${cmd}
log_tail:
${log_tail}"

  curl -fsS -X POST "https://api.telegram.org/bot${token}/sendMessage" \
    --data-urlencode "chat_id=${chat_id}" \
    --data-urlencode "text=${message}" \
    >/dev/null 2>&1 || log "WARN: failed to send Telegram failure alert"
}

on_error() {
  local exit_code="${1:-1}"
  local line="${2:-unknown}"
  local cmd="${3:-unknown}"
  trap - ERR
  set +e
  log "ERROR: command failed (exit=${exit_code} line=${line} cmd=${cmd})"
  send_failure_alert "${exit_code}" "${line}" "${cmd}"
  exit "${exit_code}"
}

has_non_data_changes() {
  local changes
  changes="$(git status --porcelain -- . ':(exclude)assets.xlsx' ':(exclude)src/data.json' ':(exclude)public/data.json' || true)"
  [ -n "$changes" ]
}

prepare_publish_branch() {
  if ! command -v git >/dev/null 2>&1; then
    log "ERROR: git is required when AUTO_PUBLISH=1"
    return 1
  fi

  if has_non_data_changes; then
    log "ERROR: repository has local non-data changes; refusing AUTO_PUBLISH"
    git status --short -- . ':(exclude)assets.xlsx' ':(exclude)src/data.json' ':(exclude)public/data.json' >> "$LOG" 2>&1 || true
    return 1
  fi

  local current_branch
  current_branch="$(git branch --show-current)"
  if [ "$current_branch" != "$TARGET_BRANCH" ]; then
    if [ -n "$(git status --porcelain)" ]; then
      log "ERROR: cannot switch from $current_branch to $TARGET_BRANCH with dirty working tree"
      git status --short >> "$LOG" 2>&1 || true
      return 1
    fi
    log "Switching branch: $current_branch -> $TARGET_BRANCH"
    git checkout "$TARGET_BRANCH" >> "$LOG" 2>&1
  fi

  log "Updating branch $TARGET_BRANCH from $REMOTE_NAME"
  git fetch "$REMOTE_NAME" "$TARGET_BRANCH" >> "$LOG" 2>&1
  git pull --rebase "$REMOTE_NAME" "$TARGET_BRANCH" >> "$LOG" 2>&1
}

publish_data() {
  if has_non_data_changes; then
    log "ERROR: pipeline produced non-data changes; refusing AUTO_PUBLISH"
    git status --short -- . ':(exclude)assets.xlsx' ':(exclude)src/data.json' ':(exclude)public/data.json' >> "$LOG" 2>&1 || true
    return 1
  fi

  git add "${DATA_FILES[@]}"
  if git diff --cached --quiet; then
    log "No data changes to publish."
    return 0
  fi

  local commit_msg
  commit_msg="$COMMIT_PREFIX $(date '+%Y-%m-%d %H:%M:%S %Z')"
  git commit -m "$commit_msg" >> "$LOG" 2>&1
  git push "$REMOTE_NAME" "$TARGET_BRANCH" >> "$LOG" 2>&1
  log "Published to $REMOTE_NAME/$TARGET_BRANCH"
}

# Load secrets from .env (gitignored)
if [ -f "$DIR/.env" ]; then
  set -a
  source "$DIR/.env"
  set +a
else
  on_error 1 "$LINENO" ".env file not found at $DIR/.env"
fi

trap 'on_error $? $LINENO "$BASH_COMMAND"' ERR

# Activate venv
if [ ! -f "$VENV_PATH" ]; then
  on_error 1 "$LINENO" "venv activate script not found: $VENV_PATH"
fi
source "$VENV_PATH" || on_error $? "$LINENO" "failed to source venv: $VENV_PATH"

cd "$DIR"

log "Starting $TIME_OF_DAY briefing (AUTO_PUBLISH=$AUTO_PUBLISH, SEND_TELEGRAM=$SEND_TELEGRAM, ALERT_ON_FAILURE=$ALERT_ON_FAILURE)"

if [ "$AUTO_PUBLISH" = "1" ]; then
  prepare_publish_branch
fi

# Step 1: Pipeline
python3 "$PIPELINE_SCRIPT" >> "$LOG" 2>&1

# Step 2: Telegram
if [ "$SEND_TELEGRAM" = "1" ]; then
  python3 "$TELEGRAM_SCRIPT" --time_of_day "$TIME_OF_DAY" >> "$LOG" 2>&1
else
  log "Skipping Telegram broadcast (SEND_TELEGRAM=0)"
fi

if [ "$AUTO_PUBLISH" = "1" ]; then
  publish_data
fi

log "Done."
