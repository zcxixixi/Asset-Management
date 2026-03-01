# Asset-Management

Minimal asset dashboard with automated workbook sync, market/news enrichment, and GitHub Pages delivery.

## Core Features

- Reads holdings and NAV history from `assets.xlsx`.
- Updates portfolio values using `yfinance`.
- Syncs workbook tables (`Holdings`, `Daily`, `Chart`, `Exec`) with integrity checks.
- Writes web payload to:
  - `public/data.json` (runtime source, preferred by UI)
  - `src/data.json` (bundled fallback)
- Generates AI advisor briefing from portfolio + macro news context.
- Supports historical simulation mode via `--date YYYY-MM-DD`.

## Data Flow

1. Run `python src/extract_data.py`.
2. Script updates workbook and JSON payloads.
3. React UI loads live payload from `public/data.json` (cache-busted request), then falls back to bundled data when needed.

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm ci
```

## Local Usage

```bash
# Normal sync (today / live)
python src/extract_data.py

# Historical simulation
python src/extract_data.py --date 2026-02-27

# Frontend
npm run dev
```

## Validation

```bash
python src/extract_data_test.py
python src/backfill_regression_test.py
python src/stability_test.py
python src/test_glm_integration.py
python script_real_stress_test.py
npm run lint
npm run build
```

Latest robustness results are tracked in [TEST_LOG.md](/Users/kaijimima1234/Desktop/openclaw/Asset-Management-codex-sync/TEST_LOG.md).

## Automation (GitHub Actions)

- `Auto Data Sync`: every 6 hours; regenerates `assets.xlsx + public/data.json + src/data.json`, commits to `main`.
- `Auto Test`: runs frontend validation + Python schema/regression/LLM/heartbeat checks on push/PR.
- `Deploy Pages`: builds and deploys `dist` to GitHub Pages.

## Optional Secrets

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `GLM_API_KEY`
- `GLM_BASE_URL`
- `GLM_MODEL`

## Minimal Layout

```text
.github/workflows/
assets.xlsx
public/data.json
src/
  extract_data.py
  workbook_sync.py
  extract_data_test.py
  backfill_regression_test.py
  stability_test.py
  test_glm_integration.py
  data.json
  live_data.ts
```
