#!/bin/bash
# Nanobot Asset-Management: scheduled pipeline + Telegram broadcaster
# Usage: ./run_briefing.sh morning|afternoon|evening

set -euo pipefail

TIME_OF_DAY="${1:-test}"
DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="$DIR/backups/cron_$(date +%Y%m%d_%H%M).log"
AUTO_PUBLISH="${AUTO_PUBLISH:-0}"
SEND_TELEGRAM="${SEND_TELEGRAM:-1}"
TARGET_BRANCH="${TARGET_BRANCH:-main}"
REMOTE_NAME="${REMOTE_NAME:-origin}"
VENV_PATH="${VENV_PATH:-/Users/kaijimima1234/Desktop/nanobot/venv/bin/activate}"
COMMIT_PREFIX="${COMMIT_PREFIX:-chore(data): sync portfolio data}"
DATA_FILES=("assets.xlsx" "src/data.json" "public/data.json")

mkdir -p "$DIR/backups"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"
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
  echo "ERROR: .env file not found at $DIR/.env" >&2
  exit 1
fi

# Activate venv
source "$VENV_PATH"

cd "$DIR"

log "Starting $TIME_OF_DAY briefing (AUTO_PUBLISH=$AUTO_PUBLISH, SEND_TELEGRAM=$SEND_TELEGRAM)"

if [ "$AUTO_PUBLISH" = "1" ]; then
  prepare_publish_branch
fi

# Step 1: Pipeline
python3 src/extract_data.py >> "$LOG" 2>&1

# Step 2: Telegram
if [ "$SEND_TELEGRAM" = "1" ]; then
  python3 src/telegram_bot.py --time_of_day "$TIME_OF_DAY" >> "$LOG" 2>&1
else
  log "Skipping Telegram broadcast (SEND_TELEGRAM=0)"
fi

if [ "$AUTO_PUBLISH" = "1" ]; then
  publish_data
fi

log "Done."
