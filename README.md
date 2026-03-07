# Asset Management

Personal portfolio tracker with AI-driven daily briefings, delivered via Telegram.

## Architecture

```
nanobot cron (command job) → scripts/asset_pipeline.py run-cycle
                                   ↓
                          update-data → analyze-portfolio → send-briefing → publish-data
                                   ↓
                  assets.xlsx → scripts/extract_data.py → src/public data.json → Dashboard
                                   ↓
              scripts/news_collector.py → scripts/briefing_agent.py → scripts/telegram_bot.py
```

Scheduling is deterministic; investment analysis stays agentic.

## File Map

| File | Purpose |
|------|---------|
| `scripts/asset_pipeline.py` | Canonical CLI entrypoint for update/analyze/send/publish |
| `scripts/extract_data.py` | Update stage — reads Excel, fetches prices/news, writes JSON + analysis context |
| `scripts/news_collector.py` | Collects and ranks portfolio/global news via yfinance |
| `scripts/briefing_agent.py` | Dedicated nanobot research agent for portfolio analysis |
| `scripts/telegram_bot.py` | Formats broadcasts and sends Telegram alerts/messages |
| `scripts/advisor_contract.py` | Pydantic schema + fallback for `advisor_briefing` |
| `scripts/workbook_sync.py` | Excel read/write + daily row sync |
| `assets.xlsx` | Your portfolio (single source of truth) |

## Run Manually

```bash
# 1. Refresh data only
python3 scripts/asset_pipeline.py update-data

# 2. Run nanobot-backed portfolio analysis
python3 scripts/asset_pipeline.py analyze-portfolio --time-of-day morning

# 3. Send to Telegram
python3 scripts/asset_pipeline.py send-briefing --time-of-day morning

# 4. Full scheduled cycle
python3 scripts/asset_pipeline.py run-cycle --time-of-day morning --send-telegram --publish
```

## Automation

| What | Who | When |
|------|-----|------|
| Pipeline + auto-publish + Telegram | Nanobot Cron direct command (`~/.nanobot/cron/jobs.json` → `scripts/asset_pipeline.py`) | Weekdays 8:30, 13:30, 20:00 HKT |
| CI (lint + tests) | GitHub Actions `auto_test.yml` | Every push |
| Deploy dashboard | GitHub Actions `deploy-pages.yml` | Triggered by pushes to `main` |

`run_briefing.sh` remains as a thin compatibility wrapper, but scheduled runs now call the Python CLI directly. `run-cycle` refreshes portfolio data, runs the dedicated nanobot analysis agent, sends the Telegram briefing, and when `--publish` is enabled it commits only `assets.xlsx`, `src/data.json`, and `public/data.json` to `main`.

The frontend polls `data.json` every 60 seconds while the page is visible. Open tabs automatically pick up new `last_updated` payloads after the published JSON changes on GitHub Pages.

## Dev Server

```bash
npm install && npm run dev
```

## Tests

```bash
python3 scripts/tests/extract_data_test.py
python3 scripts/tests/backfill_regression_test.py
python3 scripts/tests/stability_test.py
python3 scripts/tests/advisor_contract_test.py
python3 scripts/tests/briefing_agent_test.py
python3 scripts/tests/news_collector_test.py
python3 scripts/tests/pipeline_integration_test.py
```
