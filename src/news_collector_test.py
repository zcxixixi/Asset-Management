import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from advisor_contract import AdvisorBriefing
from news_collector import get_portfolio_context


def _yf_item(headline: str, source: str, timestamp: str) -> dict:
    return {
        "content": {
            "title": headline,
            "provider": {"displayName": source},
            "pubDate": timestamp,
        }
    }


class _FakeTicker:
    def __init__(self, news_items):
        self.news = news_items


class _FakeYFinance:
    def __init__(self, data_map):
        self._data_map = data_map

    def Ticker(self, symbol):
        return _FakeTicker(self._data_map.get(symbol, []))


class TestNewsCollector(unittest.TestCase):
    def setUp(self):
        self.holdings = [
            {"symbol": "NVDA.US", "value": "12000"},
            {"symbol": "TSLA.US", "value": "6000"},
            {"symbol": "AAPL.US", "value": "9000"},
            {"symbol": "GOLD.CN", "value": "3000"},
        ]

    def test_get_portfolio_context_uses_yfinance_data_and_schema(self):
        fake_yf = _FakeYFinance(
            {
                "NVDA": [
                    _yf_item("NVIDIA AI demand remains strong", "Reuters", "2026-02-28T13:20:00Z"),
                    _yf_item("NVIDIA supply chain improves", "CNBC", "2026-02-27T10:20:00Z"),
                ],
                "TSLA": [
                    _yf_item("Tesla updates autonomy software", "Bloomberg", "2026-02-28T11:45:00Z"),
                ],
                "^GSPC": [
                    _yf_item("S&P 500 opens mixed on macro data", "Reuters", "2026-02-28T15:00:00Z"),
                ],
                "SPY": [
                    _yf_item("Large caps stabilize after volatile week", "Yahoo Finance", "2026-02-28T12:30:00Z"),
                ],
                "QQQ": [
                    _yf_item("Tech sentiment improves into month-end", "CNBC", "2026-02-27T21:10:00Z"),
                ],
            }
        )

        with patch("news_collector.yf", fake_yf):
            context = get_portfolio_context(self.holdings)

        self.assertIn("news_context", context)
        self.assertIn("global_context", context)
        self.assertIsInstance(context["news_context"], list)
        self.assertIsInstance(context["global_context"], list)
        self.assertGreater(len(context["news_context"]), 0)
        self.assertGreater(len(context["global_context"]), 0)

        required_keys = {"headline", "source", "timestamp", "relevance_score"}
        self.assertTrue(all(isinstance(item, dict) and required_keys.issubset(item.keys()) for item in context["news_context"]))
        self.assertTrue(all(isinstance(item, dict) and required_keys.issubset(item.keys()) for item in context["global_context"]))

        news_scores = [item["relevance_score"] for item in context["news_context"] if item.get("relevance_score") is not None]
        self.assertEqual(news_scores, sorted(news_scores, reverse=True))

        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "AdvisorAgent_Test",
            "headline": "Schema Validation Check",
            "macro_summary": "Testing news collector contract compliance.",
            "verdict": "NEUTRAL",
            "suggestions": [
                {
                    "asset": "NVDA.US",
                    "action": "HOLD",
                    "rationale": "Test payload for schema validation.",
                }
            ],
            "risks": ["Test-only validation risk placeholder."],
            "news_context": context["news_context"],
            "global_context": context["global_context"],
            "disclaimer": "Test disclaimer.",
        }

        validated = AdvisorBriefing.model_validate(payload)
        self.assertIsInstance(validated.news_context, list)
        self.assertIsInstance(validated.global_context, list)

    def test_get_portfolio_context_returns_empty_lists_when_no_news(self):
        with patch("news_collector.yf", None):
            context = get_portfolio_context(self.holdings)

        self.assertEqual(context["news_context"], [])
        self.assertEqual(context["global_context"], [])

    def test_get_portfolio_context_returns_empty_lists_on_exception(self):
        with patch("news_collector._fetch_symbol_news", side_effect=RuntimeError("boom")):
            context = get_portfolio_context(self.holdings)

        self.assertEqual(context["news_context"], [])
        self.assertEqual(context["global_context"], [])


if __name__ == "__main__":
    unittest.main()
