#!/bin/bash
# Nanobot Asset-Management: scheduled pipeline + Telegram broadcaster
# Usage: ./run_briefing.sh morning|afternoon|evening

set -euo pipefail

TIME_OF_DAY="${1:-test}"
DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="$DIR/backups/cron_$(date +%Y%m%d_%H%M).log"

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
source /Users/kaijimima1234/Desktop/nanobot/venv/bin/activate

cd "$DIR"

echo "[$(date)] Starting $TIME_OF_DAY briefing..." >> "$LOG"

# Step 1: Pipeline
python3 src/extract_data.py >> "$LOG" 2>&1

# Step 2: Telegram
python3 src/telegram_bot.py --time_of_day "$TIME_OF_DAY" >> "$LOG" 2>&1

echo "[$(date)] Done." >> "$LOG"
