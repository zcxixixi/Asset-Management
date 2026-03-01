#!/usr/bin/env python3
"""
Real-Time Asset Synchronization Script
- Reads holdings from assets.xlsx
- Calculates live portfolio values via yfinance
- Synchronizes workbook tables (Holdings/Daily/Chart/Exec) with rigorous checks
- Builds JSON payload for web UI
- Generates personalized advisor briefing from latest news + optional LLM
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List

import pandas as pd
import yfinance as yf

from workbook_sync import WorkbookSyncError, normalize_date_str, sync_workbook

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None

INPUT_PATH = "assets.xlsx"
OUTPUT_PATH = "src/data.json"
REQUIRED_HOLDINGS_COLUMNS = {"symbol", "name", "quantity"}
REQUIRED_DAILY_COLUMNS = {"date", "cash_usd", "gold_usd", "stocks_usd", "total_usd", "nav", "note"}
MAX_NEWS_ITEMS = 8


def safe_float(value: Any) -> float:
    if pd.isna(value) or value is None:
        return 0.0
    try:
        if isinstance(value, str):
            value = value.replace(",", "").replace("$", "").strip()
            if not value:
                return 0.0
            return float(value)
        return float(value)
    except Exception:
        return 0.0


def to_yf_symbol(symbol: str) -> str:
    symbol = str(symbol).strip().upper()
    if symbol.endswith(".US"):
        symbol = symbol.replace(".US", "")
    if symbol in {"GOLD.CN", "GOLD"} or "GOLD" in symbol:
        return "GC=F"
    return symbol


def normalize_asset_label(name: str) -> str:
    key = str(name).strip().lower()
    if "cash" in key or key in {"usd", "cash usd"}:
        return "Cash USD"
    if "gold" in key:
        return "Gold USD"
    if "stock" in key or "equity" in key or key in {"us stocks", "us stock"}:
        return "US Stocks"
    return str(name).strip() or "Portfolio"


def format_asset_label(name: str, symbol: str) -> str:
    sym_upper = str(symbol).upper()
    if "GOLD" in sym_upper or "GC=F" in sym_upper:
        return "Gold USD"
    if ".US" in sym_upper or sym_upper in {"NVDA", "TSLA", "QQQ", "SGOV"}:
        return "US Stocks"
    if "CASH" in sym_upper or sym_upper in {"USD", "USDT"}:
        return "Cash USD"
    return normalize_asset_label(name)


def get_realtime_price(symbol: str) -> float:
    if symbol.upper() == "CASH":
        return 1.0

    yf_symbol = to_yf_symbol(symbol)
    try:
        ticker = yf.Ticker(yf_symbol)
        fast_info = ticker.fast_info
        last_price = fast_info.get("last_price") if hasattr(fast_info, "get") else fast_info["last_price"]
        if last_price and last_price > 0:
            return float(last_price)

        history = ticker.history(period="5d")
        if not history.empty:
            return float(history["Close"].dropna().iloc[-1])

        raise ValueError(f"No valid market price for {yf_symbol}")
    except Exception as exc:
        print(f"Warning: Failed to fetch {symbol} ({yf_symbol}): {exc}")
        return 0.0


def parse_published_at(raw_value: Any) -> str:
    if raw_value is None:
        return "Unknown"
    try:
        if isinstance(raw_value, (int, float)):
            dt = datetime.fromtimestamp(float(raw_value), tz=timezone.utc)
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        text = str(raw_value).strip()
        if not text:
            return "Unknown"
        dt = pd.to_datetime(text, utc=True, errors="coerce")
        if pd.isna(dt):
            return "Unknown"
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return "Unknown"


def collect_portfolio_news(symbols: List[str], max_items: int = MAX_NEWS_ITEMS) -> List[Dict[str, str]]:
    news_items: List[Dict[str, str]] = []
    seen: set[str] = set()

    for raw_symbol in symbols:
        symbol = str(raw_symbol).strip().upper()
        if not symbol or symbol in {"CASH", "USD", "USDT"}:
            continue

        yf_symbol = to_yf_symbol(symbol)
        try:
            ticker = yf.Ticker(yf_symbol)
            raw_news = ticker.news or []
        except Exception as exc:
            print(f"Warning: Failed to fetch news for {symbol}: {exc}")
            continue

        for item in raw_news:
            title = str(item.get("title", "")).strip()
            url = str(item.get("link") or item.get("url") or "").strip()
            if not title:
                continue

            unique_key = url or title
            if unique_key in seen:
                continue
            seen.add(unique_key)

            publisher = str(item.get("publisher") or item.get("source") or "Unknown").strip()
            published_at = parse_published_at(item.get("providerPublishTime") or item.get("published"))
            summary = str(item.get("summary") or "").strip()

            news_items.append(
                {
                    "symbol": symbol,
                    "title": title,
                    "publisher": publisher,
                    "published_at": published_at,
                    "url": url,
                    "summary": summary,
                }
            )

    def sort_key(entry: Dict[str, str]) -> pd.Timestamp:
        dt = pd.to_datetime(entry.get("published_at", ""), utc=True, errors="coerce")
        if pd.isna(dt):
            return pd.Timestamp(0, tz="UTC")
        return dt

    news_items.sort(key=sort_key, reverse=True)
    return news_items[:max_items]


def format_pct(value: float) -> str:
    return f"{value:+.2f}%"


def build_rule_based_briefing(
    assets: List[Dict[str, str]],
    perf_7d: float,
    news_items: List[Dict[str, str]],
) -> Dict[str, Any]:
    assets_map = {item["label"]: safe_float(item["value"]) for item in assets}
    total_value = sum(assets_map.values()) or 1.0

    cash_pct = (assets_map.get("Cash USD", 0.0) / total_value) * 100
    gold_pct = (assets_map.get("Gold USD", 0.0) / total_value) * 100
    stocks_pct = (assets_map.get("US Stocks", 0.0) / total_value) * 100

    headline = "Portfolio Pulse: Balanced but Event-Sensitive"
    if news_items:
        first = news_items[0]
        headline = f"Portfolio Pulse: {first['symbol']} drives latest market narrative"

    macro_summary = (
        f"7-day NAV move is {format_pct(perf_7d)}. Current allocation is "
        f"Cash {cash_pct:.1f}%, Gold {gold_pct:.1f}%, US Stocks {stocks_pct:.1f}%. "
        "Portfolio remains diversified, but near-term volatility can be elevated around headline-heavy sessions."
    )

    suggestions: List[Dict[str, str]] = [
        {
            "asset": "Cash USD",
            "action": "Maintain reserve" if cash_pct < 20 else "Deploy gradually",
            "rationale": "Use staged allocation to control timing risk and keep flexibility.",
        },
        {
            "asset": "US Stocks",
            "action": "Hold core exposure" if perf_7d >= -1 else "Rebalance carefully",
            "rationale": "Keep position sizing disciplined and avoid overreaction to single headlines.",
        },
    ]

    if gold_pct > 10:
        suggestions.append(
            {
                "asset": "Gold USD",
                "action": "Keep hedge",
                "rationale": "Gold weight helps absorb macro and risk-off shocks.",
            }
        )

    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "rule-based",
        "headline": headline,
        "macro_summary": macro_summary,
        "verdict": "Keep diversified core positions and adjust incrementally, not aggressively.",
        "suggestions": suggestions[:4],
        "risks": [
            "Short-term market reactions to macro headlines can exceed fundamentals.",
            "Single-name concentration risk can amplify drawdowns.",
        ],
        "news_context": news_items,
        "disclaimer": "Informational only, not financial advice.",
    }


def sanitize_briefing(raw: Any, fallback: Dict[str, Any], news_items: List[Dict[str, str]], source: str) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        raw = {}

    headline = str(raw.get("headline") or fallback["headline"]).strip()
    macro_summary = str(raw.get("macro_summary") or fallback["macro_summary"]).strip()
    verdict = str(raw.get("verdict") or fallback["verdict"]).strip()

    risks: List[str] = []
    for risk in raw.get("risks", []):
        text = str(risk).strip()
        if text:
            risks.append(text)
    if not risks:
        risks = fallback["risks"]

    suggestions: List[Dict[str, str]] = []
    for item in raw.get("suggestions", []):
        if not isinstance(item, dict):
            continue
        asset = normalize_asset_label(item.get("asset") or "Portfolio")
        action = str(item.get("action") or "Hold").strip()
        rationale = str(item.get("rationale") or "No rationale provided.").strip()
        if rationale:
            suggestions.append({"asset": asset, "action": action, "rationale": rationale})

    if not suggestions:
        suggestions = fallback["suggestions"]

    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": source,
        "headline": headline,
        "macro_summary": macro_summary,
        "verdict": verdict,
        "suggestions": suggestions[:4],
        "risks": risks[:5],
        "news_context": news_items,
        "disclaimer": "Informational only, not financial advice.",
    }


def generate_llm_briefing(
    assets: List[Dict[str, str]],
    holdings: List[Dict[str, str]],
    perf_7d: float,
    news_items: List[Dict[str, str]],
) -> Dict[str, Any]:
    fallback = build_rule_based_briefing(assets, perf_7d, news_items)

    api_key = os.getenv("GLM_API_KEY") or os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or OpenAI is None:
        return fallback

    base_url = os.getenv("GLM_BASE_URL")
    model = os.getenv("GLM_MODEL") or os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

    payload = {
        "portfolio_assets": assets,
        "holdings": holdings,
        "perf_7d_pct": round(perf_7d, 4),
        "news_items": news_items,
    }

    system_prompt = (
        "You are a cautious portfolio analyst. "
        "Use only provided data and return strict JSON with keys: "
        "headline, macro_summary, verdict, suggestions, risks. "
        "suggestions items must include: asset, action, rationale."
    )

    try:
        client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model=model,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
        )
        content = completion.choices[0].message.content or "{}"
        parsed = json.loads(content)
        return sanitize_briefing(parsed, fallback, news_items, source=f"llm:{model}")
    except Exception as exc:
        print(f"Warning: LLM briefing failed, using fallback: {exc}")
        return fallback


def suggestion_to_insight_type(action: str) -> str:
    action_lower = str(action).lower()
    if any(word in action_lower for word in ["reduce", "trim", "rebalance", "tighten", "hedge", "defensive"]):
        return "warning"
    if any(word in action_lower for word in ["add", "deploy", "accumulate", "hold", "increase", "keep", "maintain"]):
        return "opportunity"
    return "neutral"


def briefing_to_insights(briefing: Dict[str, Any]) -> List[Dict[str, str]]:
    suggestions = briefing.get("suggestions", []) if isinstance(briefing, dict) else []
    insights: List[Dict[str, str]] = []

    for item in suggestions[:3]:
        if not isinstance(item, dict):
            continue
        asset = normalize_asset_label(item.get("asset") or "Portfolio")
        action = str(item.get("action") or "").strip()
        rationale = str(item.get("rationale") or "").strip()
        if rationale:
            insights.append({"type": suggestion_to_insight_type(action), "asset": asset, "text": rationale})

    if not insights:
        insights = [
            {
                "type": "neutral",
                "asset": "Portfolio",
                "text": "No strong signal detected; maintain diversification and review positions on schedule.",
            }
        ]
    return insights


def extract_data() -> Dict[str, Any]:
    if not os.path.exists(INPUT_PATH):
        raise FileNotFoundError(f"{INPUT_PATH} not found in repository root")

    print("Reading local Excel Holdings (Broker Export Format)...")
    df_holdings = pd.read_excel(INPUT_PATH, sheet_name="Holdings")
    df_holdings = df_holdings.dropna(how="all")
    df_holdings.columns = [str(c).strip().lower() for c in df_holdings.columns]

    missing_holdings_columns = REQUIRED_HOLDINGS_COLUMNS - set(df_holdings.columns)
    if missing_holdings_columns:
        raise ValueError(f"Holdings sheet missing columns: {sorted(missing_holdings_columns)}")

    assets_grouped: Dict[str, float] = {}
    total_balance = 0.0
    tracked_symbols: List[str] = []
    holding_updates: List[Dict[str, Any]] = []
    live_holdings: List[Dict[str, str]] = []

    print("\nFetching real-time market data via yfinance...")
    for _, row in df_holdings.iterrows():
        if pd.isna(row.get("symbol")):
            continue

        symbol = str(row.get("symbol", "CASH")).strip()
        name = str(row.get("name", "Unknown")).strip()
        qty = safe_float(row.get("quantity"))

        price = get_realtime_price(symbol)
        market_value = qty * price
        total_balance += market_value

        print(f"[{symbol}] {qty} units @ ${price:,.2f} = ${market_value:,.2f}")

        category = format_asset_label(name, symbol)
        assets_grouped[category] = assets_grouped.get(category, 0.0) + market_value

        holding_updates.append(
            {
                "symbol": symbol.strip().upper(),
                "quantity": qty,
                "price_usd": price,
                "market_value_usd": market_value,
            }
        )

        if symbol.upper() not in {"CASH", "USD"} and market_value > 0:
            live_holdings.append(
                {
                    "symbol": symbol,
                    "name": name,
                    "qty": str(qty) if qty != int(qty) else str(int(qty)),
                    "value": f"{market_value:,.2f}",
                }
            )

        tracked_symbols.append(symbol)

    final_assets = [
        {"label": "Cash USD", "value": f"{assets_grouped.get('Cash USD', assets_grouped.get('USD Cash', 0.0)):,.2f}"},
        {"label": "Gold USD", "value": f"{assets_grouped.get('Gold USD', 0.0):,.2f}"},
        {"label": "US Stocks", "value": f"{assets_grouped.get('US Stocks', 0.0):,.2f}"},
    ]

    sync_now = datetime.now()
    try:
        meta = sync_workbook(
            workbook_path=INPUT_PATH,
            sync_dt=sync_now,
            holding_updates=holding_updates,
            assets_grouped=assets_grouped,
            total_balance=total_balance,
        )
        print(
            f"Workbook sync OK. last_daily_date={meta['last_daily_date']} "
            f"daily_count={meta['daily_count']} backup={meta['backup_path']}"
        )
    except WorkbookSyncError as exc:
        raise RuntimeError(f"Workbook sync failed: {exc}") from exc

    df_daily = pd.read_excel(INPUT_PATH, sheet_name="Daily")
    df_daily = df_daily.dropna(how="all", axis=1).dropna(how="all", axis=0)
    df_daily.columns = [str(c).strip().lower() for c in df_daily.columns]
    missing_daily_columns = REQUIRED_DAILY_COLUMNS - set(df_daily.columns)
    if missing_daily_columns:
        raise ValueError(f"Daily sheet missing columns: {sorted(missing_daily_columns)}")

    df_daily["date"] = df_daily["date"].apply(normalize_date_str)
    df_daily["nav"] = df_daily["nav"].apply(safe_float)
    df_daily = df_daily[df_daily["date"] != ""].copy()

    nav_series = df_daily["nav"].dropna()
    if nav_series.empty:
        raise ValueError("Daily.nav has no usable values")

    current_nav = float(nav_series.iloc[-1])
    nav_7d_ago = float(nav_series.iloc[-8]) if len(nav_series) >= 8 else float(nav_series.iloc[0])
    perf_7d = ((current_nav / nav_7d_ago) - 1) * 100 if nav_7d_ago > 0 else 0.0

    chart_data = [
        {"date": str(row.date), "value": float(row.nav)}
        for row in df_daily[["date", "nav"]].itertuples(index=False)
    ]
    if not chart_data:
        raise ValueError("chart_data generated empty from Daily sheet")

    print("\nCollecting latest portfolio-related news...")
    news_items = collect_portfolio_news(tracked_symbols, max_items=MAX_NEWS_ITEMS)
    print(f"Collected {len(news_items)} news items")

    print("Generating personalized advisor briefing...")
    advisor_briefing = generate_llm_briefing(final_assets, live_holdings, perf_7d, news_items)
    insights = briefing_to_insights(advisor_briefing)

    response = {
        "assets": final_assets,
        "holdings": live_holdings,
        "chart_data": chart_data,
        "total_balance": f"{total_balance:,.2f}",
        "last_updated": sync_now.strftime("%Y-%m-%d %H:%M:%S"),
        "insights": insights,
        "advisor_briefing": advisor_briefing,
        "performance": {"1d": "Live", "summary": "Broker Export Integration"},
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(response, file, indent=2, ensure_ascii=False)

    print(f"\n✅ Pushed synchronized data to {OUTPUT_PATH}. Total NAV: ${total_balance:,.2f}")
    return response


if __name__ == "__main__":
    try:
        extract_data()
    except Exception as exc:
        print(f"Error orchestrating pipeline: {exc}", file=sys.stderr)
        raise
