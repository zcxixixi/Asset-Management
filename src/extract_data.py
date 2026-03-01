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
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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


def get_realtime_price(symbol: str, mock_date: datetime = None) -> float:
    if symbol.upper() == "CASH":
        return 1.0

    yf_symbol = to_yf_symbol(symbol)
    try:
        ticker = yf.Ticker(yf_symbol)
        
        if mock_date:
            end_date = mock_date + pd.Timedelta(days=1)
            start_date = mock_date - pd.Timedelta(days=5)
            history = ticker.history(start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"))
            if not history.empty:
                return float(history["Close"].dropna().iloc[-1])
            
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


def collect_portfolio_news(symbols: List[str], max_items: int = MAX_NEWS_ITEMS, mock_date: datetime = None) -> List[Dict[str, str]]:
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
            content = item.get("content", item)
            title = str(content.get("title", "")).strip()
            
            url_obj = content.get("clickThroughUrl", {})
            url = str(url_obj.get("url") if isinstance(url_obj, dict) else content.get("link") or content.get("url") or "").strip()
            
            if not title:
                continue

            unique_key = url or title
            if unique_key in seen:
                continue
            seen.add(unique_key)

            provider_obj = content.get("provider", {})
            publisher = str(provider_obj.get("displayName") if isinstance(provider_obj, dict) else content.get("publisher") or content.get("source") or "Unknown").strip()
            
            published_at = parse_published_at(content.get("pubDate") or content.get("providerPublishTime") or content.get("published"))
            
            # For time travel simulation, rewrite the timestamp to look like the mock date
            if mock_date:
                # Force the headline to appear on the morning of the mock date
                published_at = f"{mock_date.strftime('%Y-%m-%d')} 08:30:00 UTC"
                
            summary = str(content.get("summary") or "").strip()

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


def collect_global_news(max_items: int = 10, mock_date: datetime = None) -> List[Dict[str, str]]:
    """Fetch broad market news using macro proxies (e.g. S&P 500, SPY, QQQ)."""
    print("\nFetching global market news...")
    news_items: List[Dict[str, str]] = []
    seen: set[str] = set()
    
    macro_tickers = ["^GSPC", "SPY", "QQQ"]
    
    for symbol in macro_tickers:
        if len(news_items) >= max_items:
            break
            
        try:
            ticker = yf.Ticker(symbol)
            raw_news = ticker.news or []
            for item in raw_news:
                content = item.get("content", item)
                title = str(content.get("title", "")).strip()
                
                url_obj = content.get("clickThroughUrl", {})
                url = str(url_obj.get("url") if isinstance(url_obj, dict) else content.get("link") or content.get("url") or "").strip()
                
                if not title:
                    continue

                unique_key = url or title
                if unique_key in seen:
                    continue
                seen.add(unique_key)

                provider_obj = content.get("provider", {})
                publisher = str(provider_obj.get("displayName") if isinstance(provider_obj, dict) else content.get("publisher") or content.get("source") or "Unknown").strip()
                
                published_at = parse_published_at(content.get("pubDate") or content.get("providerPublishTime") or content.get("published"))
                
                # For time travel simulation, rewrite the timestamp
                if mock_date:
                    published_at = f"{mock_date.strftime('%Y-%m-%d')} 09:15:00 UTC"
                
                summary = str(content.get("summary") or "").strip()

                news_items.append(
                    {
                        "symbol": "MACRO",
                        "title": title,
                        "publisher": publisher,
                        "published_at": published_at,
                        "url": url,
                        "summary": summary,
                    }
                )
                
                if len(news_items) >= max_items:
                    break
        except Exception as exc:
            print(f"Warning: Failed to fetch global news for {symbol}: {exc}")

    return news_items


def format_pct(value: float) -> str:
    return f"{value:+.2f}%"


def build_rule_based_briefing(
    assets: List[Dict[str, str]],
    perf_7d: float,
    news_items: Dict[str, List[Dict[str, str]]],
) -> Dict[str, Any]:
    assets_map = {item["label"]: safe_float(item["value"]) for item in assets}
    total_value = sum(assets_map.values()) or 1.0

    cash_pct = (assets_map.get("Cash USD", 0.0) / total_value) * 100
    gold_pct = (assets_map.get("Gold USD", 0.0) / total_value) * 100
    stocks_pct = (assets_map.get("US Stocks", 0.0) / total_value) * 100

    headline = "Portfolio Pulse: Balanced but Event-Sensitive"
    
    global_news = news_items.get("global", [])
    portfolio_news = news_items.get("portfolio", [])
    
    # Try to use a portfolio specific news item first, then a global one
    if portfolio_news:
        first = portfolio_news[0]
        headline = f"Portfolio Pulse: {first['symbol']} drives latest market narrative"
    elif global_news:
        headline = f"Market Pulse: Global events shape near-term outlook"

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
        "news_context": portfolio_news,
        "global_context": global_news,
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


def generate_mock_news(
    symbols: List[str], mock_date_str: str, api_key: str, base_url: str, model: str
) -> Dict[str, List[Dict[str, str]]]:
    print(f"\n[Simulation] Generating historically plausible news for {mock_date_str} via LLM...")
    if not api_key or OpenAI is None:
        print("Warning: Cannot generate dynamic mock news without API key. Using static hardcoded mock news.")
        return {
            "portfolio": [
                {
                    "symbol": symbols[0] if symbols else "PORTFOLIO",
                    "title": f"Historical Simulation Alert: Major event shakes {symbols[0] if symbols else 'markets'}.",
                    "publisher": "OpenClaw Financial",
                    "published_at": f"{mock_date_str} 08:30:00 UTC",
                    "url": "#",
                    "summary": f"This is a simulated headline reflecting a major event for {symbols[0] if symbols else 'asset'} around {mock_date_str}.",
                },
                {
                    "symbol": symbols[1] if len(symbols) > 1 else "PORTFOLIO",
                    "title": f"Analysts Upgrade Outlook Amid Sector Rallies",
                    "publisher": "Simulation Market News",
                    "published_at": f"{mock_date_str} 09:15:00 UTC",
                    "url": "#",
                    "summary": f"Analysts project continued growth for assets like {symbols[1] if len(symbols) > 1 else 'this'} following strong earnings.",
                }
            ],
            "global": [
                {
                    "symbol": "MACRO",
                    "title": f"Global Markets React to Fed Rate Decisions",
                    "publisher": "Macro Daily",
                    "published_at": f"{mock_date_str} 06:00:00 UTC",
                    "url": "#",
                    "summary": f"On {mock_date_str}, global indices showed increased volatility as central banks signaled potential policy shifts.",
                },
                {
                    "symbol": "MACRO",
                    "title": f"Geopolitical Tensions Shape Commodity Prices",
                    "publisher": "Global Tracker",
                    "published_at": f"{mock_date_str} 07:45:00 UTC",
                    "url": "#",
                    "summary": f"Commodity markets saw significant movement leading up to {mock_date_str} due to international trade developments.",
                }
            ]
        }

    prompt = (
        f"You are a mock data generator for a historical simulation. The simulated date is {mock_date_str}.\n"
        f"Generate exactly 8 realistic financial news headlines regarding the portfolio assets {symbols}, "
        f"and 15 realistic global macroeconomic headlines that would have appeared on or just before {mock_date_str}.\n"
        "Return strictly a JSON object with two keys: 'portfolio' and 'global'.\n"
        "Each is a list of objects containing: 'symbol' (use actual symbol for portfolio, or 'MACRO' for global), "
        f"'title', 'publisher', 'published_at' (format like '{mock_date_str} 08:30:00 UTC'), 'url' (make a realistic-looking url), 'summary'."
    )

    try:
        client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model=model,
            temperature=0.7,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": prompt}],
        )
        content = completion.choices[0].message.content or "{}"
        parsed = json.loads(content)
        return {
            "portfolio": parsed.get("portfolio", []),
            "global": parsed.get("global", []),
        }
    except Exception as exc:
        print(f"Warning: Mock news generation failed: {exc}")
        return {"portfolio": [], "global": []}


def generate_llm_briefing(
    assets: List[Dict[str, str]],
    holdings: List[Dict[str, str]],
    perf_7d: float,
    news_items: Dict[str, List[Dict[str, str]]],
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
        "portfolio_news": news_items.get("portfolio", []),
        "global_news": news_items.get("global", []),
    }

    system_prompt = (
        "You are an enterprise-grade portfolio analyst. "
        "Analyze the provided `portfolio_news` and `global_news`. "
        "Crucially, tie major global events (e.g., political shifts, macro data) directly to the user's specific holdings and their relative weights. "
        "Use only provided data and return strict JSON with keys: "
        "headline, macro_summary, verdict, suggestions, risks. "
        "suggestions items must include: asset, action (Hold, Accumulate, Reduce, etc.), rationale (explaining the direct impact of global/portfolio news on this specific asset weighting)."
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
        return sanitize_briefing(parsed, fallback, news_items.get("portfolio", []), source=f"llm:{model}")
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


def extract_data(mock_date_str: str = None) -> Dict[str, Any]:
    if not os.path.exists(INPUT_PATH):
        raise FileNotFoundError(f"{INPUT_PATH} not found in repository root")
        
    sync_now = datetime.now()
    if mock_date_str:
        sync_now = datetime.strptime(mock_date_str, "%Y-%m-%d")

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

        price = get_realtime_price(symbol, mock_date=sync_now if mock_date_str else None)
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

    try:
        if mock_date_str:
            print("Skipping workbook sync for historical simulation.")
        else:
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
    
    if mock_date_str:
        df_daily = df_daily[df_daily["date"] <= mock_date_str].copy()

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

    if mock_date_str:
        api_key = os.getenv("GLM_API_KEY") or os.getenv("OPENAI_API_KEY", "").strip()
        base_url = os.getenv("GLM_BASE_URL")
        model = os.getenv("GLM_MODEL") or os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
        all_news = generate_mock_news(tracked_symbols, mock_date_str, api_key, base_url, model)
        portfolio_news = all_news.get("portfolio", [])
        global_news = all_news.get("global", [])
    else:
        print("\nCollecting latest portfolio-related news...")
        portfolio_news = collect_portfolio_news(tracked_symbols, max_items=MAX_NEWS_ITEMS, mock_date=None)
        print(f"Collected {len(portfolio_news)} portfolio news items")
        
        global_news = collect_global_news(max_items=15, mock_date=None)
        print(f"Collected {len(global_news)} global news items")
        
        all_news = {"portfolio": portfolio_news, "global": global_news}

    print("Generating personalized advisor briefing...")
    advisor_briefing = generate_llm_briefing(final_assets, live_holdings, perf_7d, all_news)
    insights = briefing_to_insights(advisor_briefing)

    response = {
        "assets": final_assets,
        "holdings": live_holdings,
        "chart_data": chart_data,
        "total_balance": f"{total_balance:,.2f}",
        "last_updated": sync_now.strftime("%Y-%m-%d %H:%M:%S"),
        "insights": insights,
        "advisor_briefing": advisor_briefing,
        "daily_news": global_news,
        "performance": {"1d": "Live", "summary": "Broker Export Integration"},
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(response, file, indent=2, ensure_ascii=False)

    print(f"\n✅ Pushed synchronized data to {OUTPUT_PATH}. Total NAV: ${total_balance:,.2f}")
    return response


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Synchronize asset data.")
    parser.add_argument("--date", type=str, help="Mock date (YYYY-MM-DD)")
    args = parser.parse_args()
    
    try:
        extract_data(mock_date_str=args.date)
    except Exception as exc:
        print(f"Error orchestrating pipeline: {exc}", file=sys.stderr)
        sys.exit(1)
