from __future__ import annotations

import email.utils
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional
from urllib.error import URLError
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

try:
    import yfinance as yf
except Exception:  # pragma: no cover
    yf = None


MAX_PORTFOLIO_ITEMS = 8
MAX_GLOBAL_ITEMS = 6
GLOBAL_MACRO_TICKERS = ("^GSPC", "SPY", "QQQ")

CHANNEL_MARKET = "market-news"
CHANNEL_SEC = "sec-filing"
CHANNEL_COMPANY = "company-ir"
CHANNEL_MACRO = "official-macro"

RSS_TIMEOUT_SECONDS = 8
TOP_WEIGHTED_HOLDINGS_FOR_OFFICIAL_CHECK = 3
THIN_CONTEXT_HOURS = 24

SEC_CIK_REGISTRY = {
    "AAPL": "0000320193",
    "AMD": "0000002488",
    "AMZN": "0001018724",
    "GOOGL": "0001652044",
    "META": "0001326801",
    "MSFT": "0000789019",
    "NVDA": "0001045810",
    "TSLA": "0001318605",
}

COMPANY_FEED_REGISTRY = {
    "AAPL": {
        "url": "https://www.apple.com/newsroom/rss-feed.rss",
        "source": "Apple Newsroom",
    },
    "AMD": {
        "url": "https://www.amd.com/en/rss.xml",
        "source": "AMD Newsroom",
    },
    "MSFT": {
        "url": "https://news.microsoft.com/feed/",
        "source": "Microsoft News",
    },
    "NVDA": {
        "url": "https://nvidianews.nvidia.com/releases?o=rss",
        "source": "NVIDIA Newsroom",
    },
    "TSLA": {
        "url": "https://www.tesla.com/blog/rss.xml",
        "source": "Tesla Blog",
    },
}

MACRO_FEED_REGISTRY = (
    {
        "url": "https://www.federalreserve.gov/feeds/press_monetary.xml",
        "source": "Federal Reserve",
        "channel": CHANNEL_MACRO,
    },
    {
        "url": "https://www.bls.gov/feed/bls_latest.rss",
        "source": "BLS",
        "channel": CHANNEL_MACRO,
    },
    {
        "url": "https://home.treasury.gov/news/press-releases/feed",
        "source": "U.S. Treasury",
        "channel": CHANNEL_MACRO,
    },
)

TRUSTED_SOURCE_BONUS = {
    "REUTERS": 0.05,
    "BLOOMBERG": 0.05,
    "WSJ": 0.04,
    "CNBC": 0.04,
    "YAHOO FINANCE": 0.03,
    "FEDERAL RESERVE": 0.08,
    "BLS": 0.08,
    "U.S. TREASURY": 0.08,
    "SEC": 0.08,
}

CHANNEL_BONUS = {
    CHANNEL_MARKET: 0.03,
    CHANNEL_COMPANY: 0.08,
    CHANNEL_SEC: 0.1,
    CHANNEL_MACRO: 0.1,
}


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
            qty = _to_float(item.get("quantity") or item.get("qty"))
            px = _to_float(item.get("price") or item.get("price_usd"))
            value = qty * px
        totals[symbol] += max(value, 0.0)

    grand_total = sum(totals.values())
    if grand_total <= 0:
        equal_weight = 1.0 / len(symbols)
        return {symbol: equal_weight for symbol in symbols}
    return {symbol: value / grand_total for symbol, value in totals.items()}


def _top_weighted_symbols(symbol_weights: Dict[str, float], limit: int) -> List[str]:
    ranked = sorted(symbol_weights.items(), key=lambda item: item[1], reverse=True)
    return [symbol for symbol, _weight in ranked[:limit]]


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
        pass

    try:
        parsed_tuple = email.utils.parsedate_to_datetime(text)
        if parsed_tuple.tzinfo is None:
            parsed_tuple = parsed_tuple.replace(tzinfo=timezone.utc)
        return parsed_tuple.astimezone(timezone.utc)
    except (TypeError, ValueError, IndexError):
        return datetime(1970, 1, 1, tzinfo=timezone.utc)


def _iso_utc(raw_value: Any) -> str:
    dt = _parse_news_timestamp(raw_value)
    return dt.isoformat().replace("+00:00", "Z")


def _normalize_url(raw_url: Any) -> str:
    url = str(raw_url or "").strip()
    if not url:
        return ""
    parsed = urlparse(url)
    filtered_query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith("utm_")
    ]
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc.lower(),
            parsed.path.rstrip("/"),
            parsed.params,
            urlencode(filtered_query),
            "",
        )
    )


def _normalize_headline(headline: str) -> str:
    return " ".join(str(headline or "").strip().lower().split())


def _dedupe_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    deduped: List[Dict[str, Any]] = []
    seen_urls: set[str] = set()
    seen_headlines: set[str] = set()

    for item in items:
        canonical_url = _normalize_url(item.get("url"))
        headline_key = _normalize_headline(item.get("headline", ""))
        if canonical_url and canonical_url in seen_urls:
            continue
        if headline_key and headline_key in seen_headlines:
            continue
        if canonical_url:
            seen_urls.add(canonical_url)
        if headline_key:
            seen_headlines.add(headline_key)
        copied = dict(item)
        copied["url"] = canonical_url
        deduped.append(copied)

    return deduped


def _extract_from_yf_item(item: Dict[str, Any], symbol: str) -> Optional[Dict[str, Any]]:
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

    url = (
        item.get("link")
        or (content.get("clickThroughUrl") or {}).get("url")
        or (content.get("canonicalUrl") or {}).get("url")
        or ""
    )

    return {
        "symbol": symbol,
        "headline": headline,
        "source": source or "Yahoo Finance",
        "timestamp": _iso_utc(raw_ts),
        "url": url,
        "summary": str(content.get("summary") or "").strip() or None,
        "channel": CHANNEL_MARKET,
    }


def _fetch_market_news(symbols: Iterable[str]) -> List[Dict[str, Any]]:
    if yf is None:
        return []

    collected: List[Dict[str, Any]] = []
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            raw_news = ticker.news or []
        except Exception:
            continue

        for raw_item in raw_news[:6]:
            parsed = _extract_from_yf_item(raw_item, symbol)
            if parsed:
                collected.append(parsed)
    return _dedupe_items(collected)


def _build_sec_feed_url(cik: str) -> str:
    return f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=8-K&owner=exclude&count=10&output=atom"


def _extract_text(element: Optional[ET.Element]) -> str:
    if element is None:
        return ""
    return "".join(element.itertext()).strip()


def _entry_children(root: ET.Element) -> List[ET.Element]:
    items = root.findall(".//item")
    if items:
        return items
    return root.findall(".//{http://www.w3.org/2005/Atom}entry")


def _fetch_rss_items(
    url: str,
    *,
    channel: str,
    default_source: str,
    symbol: str = "",
    limit: int = 6,
) -> List[Dict[str, Any]]:
    request = Request(
        url,
        headers={
            "User-Agent": "nanobot-asset-manager/1.0 contact=local",
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9",
        },
    )
    try:
        with urlopen(request, timeout=RSS_TIMEOUT_SECONDS) as response:
            payload = response.read()
    except (URLError, TimeoutError, ValueError):
        return []

    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        return []

    items: List[Dict[str, Any]] = []
    for entry in _entry_children(root)[:limit]:
        title = (
            _extract_text(entry.find("title"))
            or _extract_text(entry.find("{http://www.w3.org/2005/Atom}title"))
        )
        if not title:
            continue

        link = ""
        atom_link = entry.find("{http://www.w3.org/2005/Atom}link")
        if atom_link is not None:
            link = atom_link.attrib.get("href", "")
        if not link:
            link = _extract_text(entry.find("link"))

        published = (
            _extract_text(entry.find("pubDate"))
            or _extract_text(entry.find("published"))
            or _extract_text(entry.find("{http://www.w3.org/2005/Atom}published"))
            or _extract_text(entry.find("updated"))
            or _extract_text(entry.find("{http://www.w3.org/2005/Atom}updated"))
        )

        source = default_source
        source_element = entry.find("source")
        if source_element is not None and _extract_text(source_element):
            source = _extract_text(source_element)

        summary = (
            _extract_text(entry.find("description"))
            or _extract_text(entry.find("{http://www.w3.org/2005/Atom}summary"))
            or _extract_text(entry.find("{http://www.w3.org/2005/Atom}content"))
            or None
        )

        items.append(
            {
                "symbol": symbol,
                "headline": title,
                "source": source or default_source,
                "timestamp": _iso_utc(published),
                "url": link,
                "summary": summary,
                "channel": channel,
            }
        )

    return _dedupe_items(items)


def _fetch_company_news(symbols: Iterable[str]) -> List[Dict[str, Any]]:
    collected: List[Dict[str, Any]] = []
    for symbol in symbols:
        registry = COMPANY_FEED_REGISTRY.get(symbol)
        if not registry:
            continue
        collected.extend(
            _fetch_rss_items(
                registry["url"],
                channel=CHANNEL_COMPANY,
                default_source=registry["source"],
                symbol=symbol,
                limit=4,
            )
        )
    return _dedupe_items(collected)


def _fetch_sec_news(symbols: Iterable[str]) -> List[Dict[str, Any]]:
    collected: List[Dict[str, Any]] = []
    for symbol in symbols:
        cik = SEC_CIK_REGISTRY.get(symbol)
        if not cik:
            continue
        collected.extend(
            _fetch_rss_items(
                _build_sec_feed_url(cik),
                channel=CHANNEL_SEC,
                default_source="SEC",
                symbol=symbol,
                limit=4,
            )
        )
    return _dedupe_items(collected)


def _fetch_macro_news() -> List[Dict[str, Any]]:
    collected: List[Dict[str, Any]] = []
    if yf is not None:
        collected.extend(_fetch_market_news(GLOBAL_MACRO_TICKERS))
    for feed in MACRO_FEED_REGISTRY:
        collected.extend(
            _fetch_rss_items(
                feed["url"],
                channel=feed["channel"],
                default_source=feed["source"],
                symbol="MACRO",
                limit=3,
            )
        )
    return _dedupe_items([{**item, "symbol": item.get("symbol") or "MACRO"} for item in collected])


def _score_news(
    *,
    symbol: str,
    headline: str,
    source: str,
    timestamp: str,
    channel: str,
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

    score += CHANNEL_BONUS.get(channel, 0.0)
    score += TRUSTED_SOURCE_BONUS.get(source.upper(), 0.0)

    published_at = _parse_news_timestamp(timestamp)
    age_hours = max((datetime.now(timezone.utc) - published_at).total_seconds() / 3600.0, 0.0)
    freshness_bonus = max(0.0, 1.0 - min(age_hours / 168.0, 1.0)) * 0.3
    score += freshness_bonus

    return round(min(score, 0.999), 4)


def _rank_and_cast(
    items: List[Dict[str, Any]],
    *,
    symbol_weights: Dict[str, float],
    max_items: int,
    include_symbol_prefix: bool,
) -> List[Dict[str, Any]]:
    scored: List[Dict[str, Any]] = []
    for item in items:
        symbol = str(item.get("symbol", "")).strip().upper()
        headline = str(item.get("headline", "")).strip()
        if not headline:
            continue
        source = str(item.get("source", "Unknown")).strip() or "Unknown"
        timestamp = _iso_utc(item.get("timestamp"))
        channel = str(item.get("channel") or CHANNEL_MARKET).strip() or CHANNEL_MARKET
        relevance = _score_news(
            symbol=symbol,
            headline=headline,
            source=source,
            timestamp=timestamp,
            channel=channel,
            symbol_weights=symbol_weights,
        )
        label = f"[{symbol}] " if include_symbol_prefix and symbol and symbol != "MACRO" else ""
        scored.append(
            {
                "symbol": symbol if symbol else None,
                "headline": f"{label}{headline}",
                "source": source,
                "timestamp": timestamp,
                "url": _normalize_url(item.get("url")),
                "summary": item.get("summary"),
                "channel": channel,
                "relevance_score": relevance,
            }
        )

    scored.sort(
        key=lambda n: (
            n.get("relevance_score") if n.get("relevance_score") is not None else -1.0,
            _parse_news_timestamp(n.get("timestamp")),
        ),
        reverse=True,
    )
    return scored[:max_items]


def _top_holding_has_official_context(news_context: List[Dict[str, Any]], top_symbols: List[str]) -> bool:
    official_channels = {CHANNEL_SEC, CHANNEL_COMPANY}
    if not top_symbols:
        return False
    return all(
        any(item.get("symbol") == symbol and item.get("channel") in official_channels for item in news_context)
        for symbol in top_symbols
    )


def _has_recent_macro(global_context: List[Dict[str, Any]]) -> bool:
    now = datetime.now(timezone.utc)
    for item in global_context:
        age_hours = max((now - _parse_news_timestamp(item.get("timestamp"))).total_seconds() / 3600.0, 0.0)
        if age_hours <= THIN_CONTEXT_HOURS:
            return True
    return False


def get_portfolio_context(holdings: list) -> dict:
    try:
        symbols = _extract_symbols(holdings)
        symbol_weights = _symbol_weight_map(holdings, symbols)

        portfolio_candidates = []
        portfolio_candidates.extend(_fetch_market_news(symbols))
        portfolio_candidates.extend(_fetch_company_news(symbols))
        portfolio_candidates.extend(_fetch_sec_news(symbols))
        portfolio_candidates = _dedupe_items(portfolio_candidates)

        global_candidates = _fetch_macro_news()

        news_context = (
            _rank_and_cast(
                portfolio_candidates,
                symbol_weights=symbol_weights,
                max_items=MAX_PORTFOLIO_ITEMS,
                include_symbol_prefix=True,
            )
            if portfolio_candidates
            else []
        )
        global_context = (
            _rank_and_cast(
                global_candidates,
                symbol_weights=symbol_weights,
                max_items=MAX_GLOBAL_ITEMS,
                include_symbol_prefix=False,
            )
            if global_candidates
            else []
        )

        top_symbols = _top_weighted_symbols(symbol_weights, TOP_WEIGHTED_HOLDINGS_FOR_OFFICIAL_CHECK)
        thin_context = not _top_holding_has_official_context(news_context, top_symbols) or not _has_recent_macro(global_context)
        thin_context_reasons: List[str] = []
        if not _top_holding_has_official_context(news_context, top_symbols):
            thin_context_reasons.append("top holdings lack official/company source coverage")
        if not _has_recent_macro(global_context):
            thin_context_reasons.append("macro context has no official item within 24 hours")

        return {
            "news_context": news_context,
            "global_context": global_context,
            "thin_context": thin_context,
            "thin_context_reasons": thin_context_reasons,
        }
    except Exception:
        return {
            "news_context": [],
            "global_context": [],
            "thin_context": True,
            "thin_context_reasons": ["news collection failed"],
        }
