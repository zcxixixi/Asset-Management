#!/bin/bash
# Nanobot Asset-Management: scheduled pipeline + Telegram broadcaster
# Usage: ./run_briefing.sh morning|afternoon|evening

set -euo pipefail

TIME_OF_DAY="${1:-test}"
DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="$DIR/backups/cron_$(date +%Y%m%d_%H%M).log"

# Activate venv
source /Users/kaijimima1234/Desktop/nanobot/venv/bin/activate

# API keys
export OPENAI_API_KEY="REDACTED_API_KEY"
export OPENAI_BASE_URL="http://127.0.0.1:8045/v1"
export OPENAI_MODEL="gemini-3-flash"
export TELEGRAM_BOT_TOKEN="REDACTED_TOKEN"
export TELEGRAM_CHAT_ID="8008838739"

cd "$DIR"

echo "[$(date)] Starting $TIME_OF_DAY briefing..." >> "$LOG"

# Step 1: Pipeline
python3 src/extract_data.py >> "$LOG" 2>&1

# Step 2: Telegram
python3 src/telegram_bot.py --time_of_day "$TIME_OF_DAY" >> "$LOG" 2>&1

echo "[$(date)] Done." >> "$LOG"
