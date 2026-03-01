from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from advisor_contract import NewsItem

try:
    import yfinance as yf
except Exception:  # pragma: no cover
    yf = None


MAX_PORTFOLIO_ITEMS = 8
MAX_GLOBAL_ITEMS = 6
GLOBAL_MACRO_TICKERS = ("^GSPC", "SPY", "QQQ")

FALLBACK_PORTFOLIO_NEWS: Dict[str, List[Dict[str, str]]] = {
    "NVDA": [
        {
            "headline": "NVIDIA extends AI datacenter roadmap after strong enterprise demand",
            "source": "MockWire",
            "timestamp": "2026-02-28T13:20:00Z",
        },
        {
            "headline": "Chip suppliers rally as NVIDIA ecosystem spending accelerates",
            "source": "MockWire",
            "timestamp": "2026-02-27T16:10:00Z",
        },
    ],
    "TSLA": [
        {
            "headline": "Tesla updates vehicle software stack with new autonomy milestones",
            "source": "MockWire",
            "timestamp": "2026-02-28T11:45:00Z",
        },
        {
            "headline": "Battery-cost trend supports margin outlook for EV leaders including Tesla",
            "source": "MockWire",
            "timestamp": "2026-02-27T08:35:00Z",
        },
    ],
    "AAPL": [
        {
            "headline": "Apple services revenue momentum offsets slower hardware cycle concerns",
            "source": "MockWire",
            "timestamp": "2026-02-28T09:15:00Z",
        },
        {
            "headline": "Analysts focus on Apple ecosystem retention and recurring subscription mix",
            "source": "MockWire",
            "timestamp": "2026-02-26T19:05:00Z",
        },
    ],
    "GC=F": [
        {
            "headline": "Gold futures gain as real-rate expectations stabilize",
            "source": "MockWire",
            "timestamp": "2026-02-28T07:50:00Z",
        },
        {
            "headline": "Commodity desks report renewed defensive allocation into gold",
            "source": "MockWire",
            "timestamp": "2026-02-26T14:30:00Z",
        },
    ],
}

FALLBACK_GLOBAL_NEWS: List[Dict[str, str]] = [
    {
        "headline": "US equities open mixed as investors digest latest inflation commentary",
        "source": "MockMacro",
        "timestamp": "2026-02-28T15:00:00Z",
    },
    {
        "headline": "Treasury yields stabilize while risk sentiment rotates into large caps",
        "source": "MockMacro",
        "timestamp": "2026-02-28T12:30:00Z",
    },
    {
        "headline": "Commodities remain supported on persistent geopolitical risk premium",
        "source": "MockMacro",
        "timestamp": "2026-02-27T21:10:00Z",
    },
]


def _to_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace(",", "").replace("$", "").strip()
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def _normalize_symbol(raw_symbol: str) -> str:
    symbol = str(raw_symbol or "").strip().upper()
    if symbol.endswith(".US"):
        symbol = symbol[: -len(".US")]
    if symbol in {"GOLD", "GOLD.CN"} or "GOLD" in symbol:
        return "GC=F"
    return symbol


def _extract_symbols(holdings: list) -> List[str]:
    symbols: List[str] = []
    seen: set[str] = set()

    for item in holdings or []:
        if isinstance(item, str):
            symbol = _normalize_symbol(item)
        elif isinstance(item, dict):
            symbol = _normalize_symbol(item.get("symbol") or item.get("ticker") or "")
        else:
            continue

        if not symbol or symbol in {"CASH", "USD", "USDT"}:
            continue
        if symbol in seen:
            continue
        seen.add(symbol)
        symbols.append(symbol)

    return symbols


def _symbol_weight_map(holdings: list, symbols: List[str]) -> Dict[str, float]:
    if not symbols:
        return {}

    totals: Dict[str, float] = {symbol: 0.0 for symbol in symbols}

    for item in holdings or []:
        if not isinstance(item, dict):
            continue
        symbol = _normalize_symbol(item.get("symbol") or item.get("ticker") or "")
        if symbol not in totals:
            continue

        value = _to_float(
            item.get("value")
            or item.get("market_value_usd")
            or item.get("market_value")
            or item.get("value_usd")
            or item.get("marketValue")
        )

        if value <= 0:
            # Best-effort backup if only quantity/price is present.
            qty = _to_float(item.get("quantity") or item.get("qty"))
            px = _to_float(item.get("price") or item.get("price_usd"))
            value = qty * px
        totals[symbol] += max(value, 0.0)

    grand_total = sum(totals.values())
    if grand_total <= 0:
        equal_weight = 1.0 / len(symbols)
        return {symbol: equal_weight for symbol in symbols}
    return {symbol: value / grand_total for symbol, value in totals.items()}


def _parse_news_timestamp(raw_value: Any) -> datetime:
    if raw_value is None:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)

    if isinstance(raw_value, (int, float)):
        return datetime.fromtimestamp(float(raw_value), tz=timezone.utc)

    text = str(raw_value).strip()
    if not text:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)

    if text.endswith("Z"):
        text = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)


def _iso_utc(raw_value: Any) -> str:
    dt = _parse_news_timestamp(raw_value)
    return dt.isoformat().replace("+00:00", "Z")


def _extract_from_yf_item(item: Dict[str, Any]) -> Optional[Dict[str, str]]:
    content = item.get("content", item)
    if not isinstance(content, dict):
        return None

    headline = str(content.get("title") or item.get("title") or "").strip()
    if not headline:
        return None

    provider = content.get("provider")
    if isinstance(provider, dict):
        source = str(provider.get("displayName") or provider.get("name") or "").strip()
    else:
        source = ""
    if not source:
        source = str(
            content.get("publisher")
            or content.get("source")
            or item.get("publisher")
            or "Yahoo Finance"
        ).strip()

    raw_ts = (
        content.get("pubDate")
        or content.get("providerPublishTime")
        or content.get("published")
        or item.get("providerPublishTime")
        or item.get("published")
    )
    return {
        "headline": headline,
        "source": source or "Yahoo Finance",
        "timestamp": _iso_utc(raw_ts),
    }


def _fetch_symbol_news(symbols: Iterable[str]) -> List[Dict[str, str]]:
    if yf is None:
        return []

    collected: List[Dict[str, str]] = []
    seen_headlines: set[str] = set()

    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            raw_news = ticker.news or []
        except Exception:
            continue

        for raw_item in raw_news[:6]:
            parsed = _extract_from_yf_item(raw_item)
            if not parsed:
                continue

            headline_key = parsed["headline"].strip().lower()
            if headline_key in seen_headlines:
                continue
            seen_headlines.add(headline_key)

            collected.append(
                {
                    "symbol": symbol,
                    "headline": parsed["headline"],
                    "source": parsed["source"],
                    "timestamp": parsed["timestamp"],
                }
            )

    return collected


def _fetch_global_news() -> List[Dict[str, str]]:
    if yf is None:
        return []

    collected: List[Dict[str, str]] = []
    seen_headlines: set[str] = set()

    for ticker_symbol in GLOBAL_MACRO_TICKERS:
        try:
            ticker = yf.Ticker(ticker_symbol)
            raw_news = ticker.news or []
        except Exception:
            continue

        for raw_item in raw_news[:4]:
            parsed = _extract_from_yf_item(raw_item)
            if not parsed:
                continue
            headline_key = parsed["headline"].strip().lower()
            if headline_key in seen_headlines:
                continue
            seen_headlines.add(headline_key)
            collected.append(
                {
                    "symbol": "MACRO",
                    "headline": parsed["headline"],
                    "source": parsed["source"],
                    "timestamp": parsed["timestamp"],
                }
            )

    return collected


def _fallback_portfolio_news(symbols: List[str]) -> List[Dict[str, str]]:
    target_symbols = symbols or ["NVDA", "TSLA", "AAPL", "GC=F"]
    fallback_items: List[Dict[str, str]] = []

    for symbol in target_symbols:
        symbol_items = FALLBACK_PORTFOLIO_NEWS.get(symbol)
        if symbol_items:
            for entry in symbol_items:
                fallback_items.append(
                    {
                        "symbol": symbol,
                        "headline": entry["headline"],
                        "source": entry["source"],
                        "timestamp": entry["timestamp"],
                    }
                )
        else:
            fallback_items.append(
                {
                    "symbol": symbol,
                    "headline": f"{symbol} faces mixed short-term sentiment in thin news cycle",
                    "source": "MockWire",
                    "timestamp": "2026-02-26T08:00:00Z",
                }
            )

    return fallback_items


def _fallback_global_news() -> List[Dict[str, str]]:
    return [
        {
            "symbol": "MACRO",
            "headline": item["headline"],
            "source": item["source"],
            "timestamp": item["timestamp"],
        }
        for item in FALLBACK_GLOBAL_NEWS
    ]


def _score_news(
    *,
    symbol: str,
    headline: str,
    source: str,
    timestamp: str,
    symbol_weights: Dict[str, float],
) -> float:
    score = 0.0
    if symbol in symbol_weights:
        score += 0.55 + min(symbol_weights[symbol], 1.0) * 0.4
    elif symbol == "MACRO":
        score += 0.35

    upper_headline = headline.upper()
    for tracked_symbol, weight in symbol_weights.items():
        if tracked_symbol in upper_headline:
            score += 0.15 + (weight * 0.1)

    trusted_sources = {"REUTERS", "BLOOMBERG", "WSJ", "CNBC", "YAHOO FINANCE"}
    if source.upper() in trusted_sources:
        score += 0.05

    published_at = _parse_news_timestamp(timestamp)
    age_hours = max((datetime.now(timezone.utc) - published_at).total_seconds() / 3600.0, 0.0)
    freshness_bonus = max(0.0, 1.0 - min(age_hours / 168.0, 1.0)) * 0.3
    score += freshness_bonus

    return round(min(score, 0.999), 4)


def _rank_and_cast(
    items: List[Dict[str, str]],
    *,
    symbol_weights: Dict[str, float],
    max_items: int,
    include_symbol_prefix: bool,
) -> List[NewsItem]:
    scored: List[NewsItem] = []
    for item in items:
        symbol = str(item.get("symbol", "")).strip().upper()
        headline = str(item.get("headline", "")).strip()
        if not headline:
            continue
        source = str(item.get("source", "Unknown")).strip() or "Unknown"
        timestamp = _iso_utc(item.get("timestamp"))
        relevance = _score_news(
            symbol=symbol,
            headline=headline,
            source=source,
            timestamp=timestamp,
            symbol_weights=symbol_weights,
        )

        label = f"[{symbol}] " if include_symbol_prefix and symbol else ""
        scored.append(
            NewsItem(
                headline=f"{label}{headline}",
                source=source,
                timestamp=timestamp,
                relevance_score=relevance,
            )
        )

    scored.sort(
        key=lambda n: (
            n.relevance_score if n.relevance_score is not None else -1.0,
            _parse_news_timestamp(n.timestamp),
        ),
        reverse=True,
    )
    return scored[:max_items]


def get_portfolio_context(holdings: list) -> dict:
    """Collect and rank portfolio/global news as NewsItem objects.

    Returns:
        {"news_context": List[NewsItem], "global_context": List[NewsItem]}
    """

    symbols = _extract_symbols(holdings)
    symbol_weights = _symbol_weight_map(holdings, symbols)

    portfolio_candidates = _fetch_symbol_news(symbols)
    if not portfolio_candidates:
        portfolio_candidates = _fallback_portfolio_news(symbols)

    global_candidates = _fetch_global_news()
    if not global_candidates:
        global_candidates = _fallback_global_news()

    news_context = _rank_and_cast(
        portfolio_candidates,
        symbol_weights=symbol_weights,
        max_items=MAX_PORTFOLIO_ITEMS,
        include_symbol_prefix=True,
    )
    global_context = _rank_and_cast(
        global_candidates,
        symbol_weights=symbol_weights,
        max_items=MAX_GLOBAL_ITEMS,
        include_symbol_prefix=False,
    )

    return {
        "news_context": news_context,
        "global_context": global_context,
    }
