# Asset-Management

Minimal personal asset dashboard with automated sync from `assets.xlsx`.

## What it does

- Reads holdings and NAV history from `assets.xlsx`
- Fetches live prices with `yfinance`
- Writes synchronized frontend data to `public/data.json` (runtime) and `src/data.json` (bundled fallback)
- Generates `advisor_briefing` from holdings + latest ticker news
- Uses LLM analysis when `OPENAI_API_KEY` is available
- Falls back to deterministic rule-based briefing when key is missing

## Local run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/extract_data.py
npm ci
npm run dev
```

## Validate

```bash
python src/extract_data_test.py
python src/backfill_regression_test.py
python src/stability_test.py
npm run lint
npm run build
```

## GitHub Actions

- `Auto Data Sync`: every 6 hours, regenerates `src/data.json`, commits updates
- `Auto Data Sync`: every 6 hours, regenerates `assets.xlsx + public/data.json + src/data.json`, commits updates
- `Auto Test`: validates extraction and regression checks
- `Heartbeat 24/7 Stress Test`: 5-minute health probe
- `Deploy Pages`: builds and deploys `dist` to GitHub Pages

Optional repository secrets for LLM mode:

- `OPENAI_API_KEY`
- `OPENAI_MODEL` (optional, default `gpt-4.1-mini`)

## Minimal repository layout

```text
.github/workflows/
assets.xlsx
requirements.txt
src/
  extract_data.py
  extract_data_test.py
  backfill_regression_test.py
  stability_test.py
  data.json
  AssetDashboard.tsx
  AdvisorBriefing.tsx
```
