# Asset Management

Personal portfolio tracker with AI-driven daily briefings, delivered via Telegram.

## Architecture

```
assets.xlsx → extract_data.py → data.json → Dashboard (GitHub Pages)
                    ↓
           news_collector.py  →  briefing_agent.py  →  telegram_bot.py
           (yfinance news)       (Gemini LLM)          (Telegram API)
```

**Three agents, one pipeline, zero manual steps.**

## File Map

| File | Purpose |
|------|---------|
| `src/extract_data.py` | Main orchestrator — reads Excel, fetches prices, runs agents, writes JSON |
| `src/news_collector.py` | Agent 1 — collects and ranks news per holding via yfinance |
| `src/briefing_agent.py` | Agent 2 — generates AI analysis via LLM (Gemini/GLM) |
| `src/telegram_bot.py` | Agent 3 — formats and sends Telegram broadcasts |
| `src/advisor_contract.py` | Pydantic schema + fallback (the "contract" between agents) |
| `src/workbook_sync.py` | Excel read/write + daily row sync |
| `assets.xlsx` | Your portfolio (single source of truth) |

## Run Manually

```bash
# 1. Refresh data + AI analysis
OPENAI_API_KEY="your-key" OPENAI_BASE_URL="http://127.0.0.1:8045/v1" OPENAI_MODEL="gemini-3-flash" \
  python3 src/extract_data.py

# 2. Send to Telegram
TELEGRAM_BOT_TOKEN="your-token" TELEGRAM_CHAT_ID="your-id" \
  python3 src/telegram_bot.py --time_of_day morning|afternoon|evening
```

## Automation

| What | Who | When |
|------|-----|------|
| Pipeline + Telegram | Nanobot Cron (`~/.nanobot/cron/jobs.json`) | Weekdays 8:30, 13:30, 20:00 HKT |
| CI (lint + tests) | GitHub Actions `auto_test.yml` | Every push |
| Deploy dashboard | GitHub Actions `deploy-pages.yml` | Push to main |

## Dev Server

```bash
npm install && npm run dev
```

## Tests

```bash
python3 src/extract_data_test.py
python3 src/backfill_regression_test.py
python3 src/stability_test.py
python3 src/advisor_contract_test.py
```
