import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from advisor_contract import AdvisorBriefing
from news_collector import get_portfolio_context


def _timestamp(hours_ago: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat().replace("+00:00", "Z")


class TestNewsCollector(unittest.TestCase):
    def setUp(self):
        self.holdings = [
            {"symbol": "NVDA.US", "value": "12000"},
            {"symbol": "TSLA.US", "value": "6000"},
            {"symbol": "AAPL.US", "value": "9000"},
            {"symbol": "GOLD.CN", "value": "3000"},
        ]

    def test_get_portfolio_context_merges_multi_channel_news_and_schema(self):
        market_news = [
            {
                "symbol": "NVDA",
                "headline": "NVIDIA AI demand remains strong",
                "source": "Reuters",
                "timestamp": _timestamp(6),
                "channel": "market-news",
            },
            {
                "symbol": "TSLA",
                "headline": "Tesla updates autonomy software",
                "source": "Bloomberg",
                "timestamp": _timestamp(8),
                "channel": "market-news",
            },
        ]
        company_news = [
            {
                "symbol": "NVDA",
                "headline": "NVIDIA announces next-gen inference stack",
                "source": "NVIDIA Newsroom",
                "timestamp": _timestamp(4),
                "channel": "company-ir",
            },
            {
                "symbol": "TSLA",
                "headline": "Tesla posts factory update",
                "source": "Tesla Blog",
                "timestamp": _timestamp(3),
                "channel": "company-ir",
            }
        ]
        sec_news = [
            {
                "symbol": "AAPL",
                "headline": "Apple files new 8-K",
                "source": "SEC",
                "timestamp": _timestamp(2),
                "channel": "sec-filing",
            }
        ]
        macro_news = [
            {
                "symbol": "MACRO",
                "headline": "Federal Reserve releases policy statement",
                "source": "Federal Reserve",
                "timestamp": _timestamp(5),
                "channel": "official-macro",
            }
        ]

        with (
            patch("news_collector._fetch_market_news", return_value=market_news),
            patch("news_collector._fetch_company_news", return_value=company_news),
            patch("news_collector._fetch_sec_news", return_value=sec_news),
            patch("news_collector._fetch_macro_news", return_value=macro_news),
        ):
            context = get_portfolio_context(self.holdings)

        self.assertIn("news_context", context)
        self.assertIn("global_context", context)
        self.assertIsInstance(context["news_context"], list)
        self.assertIsInstance(context["global_context"], list)
        self.assertGreater(len(context["news_context"]), 0)
        self.assertGreater(len(context["global_context"]), 0)

        required_keys = {"headline", "source", "timestamp", "channel", "relevance_score"}
        self.assertTrue(all(required_keys.issubset(item.keys()) for item in context["news_context"]))
        self.assertTrue(all(required_keys.issubset(item.keys()) for item in context["global_context"]))
        self.assertFalse(context["thin_context"])

        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "AdvisorAgent_Test",
            "headline": "Schema Validation Check",
            "macro_summary": "Testing news collector contract compliance.",
            "verdict": "NEUTRAL",
            "portfolio_overlay": {
                "stance": "BALANCED",
                "thesis": "Test overlay.",
                "rebalancing_watch": "Test watchpoint.",
            },
            "macro_themes": [{"theme": "Test theme", "implication": "Test implication"}],
            "suggestions": [
                {
                    "asset": "NVDA.US",
                    "action": "HOLD",
                    "rationale": "Test payload for schema validation.",
                    "thesis": "Test thesis",
                    "catalyst": "Test catalyst",
                    "risk": "Test risk",
                    "horizon": "MEDIUM",
                    "confidence": "HIGH",
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

    def test_get_portfolio_context_marks_thin_context_when_official_and_macro_are_missing(self):
        with (
            patch("news_collector._fetch_market_news", return_value=[]),
            patch("news_collector._fetch_company_news", return_value=[]),
            patch("news_collector._fetch_sec_news", return_value=[]),
            patch("news_collector._fetch_macro_news", return_value=[]),
        ):
            context = get_portfolio_context(self.holdings)

        self.assertEqual(context["news_context"], [])
        self.assertEqual(context["global_context"], [])
        self.assertTrue(context["thin_context"])
        self.assertGreater(len(context["thin_context_reasons"]), 0)

    def test_get_portfolio_context_dedupes_duplicate_items(self):
        duplicate = {
            "symbol": "NVDA",
            "headline": "NVIDIA AI demand remains strong",
            "source": "Reuters",
            "timestamp": _timestamp(6),
            "channel": "market-news",
            "url": "https://example.com/story?utm_source=test",
        }
        same_duplicate = {
            "symbol": "NVDA",
            "headline": "NVIDIA AI demand remains strong",
            "source": "NVIDIA Newsroom",
            "timestamp": _timestamp(3),
            "channel": "company-ir",
            "url": "https://example.com/story",
        }

        with (
            patch("news_collector._fetch_market_news", return_value=[duplicate]),
            patch("news_collector._fetch_company_news", return_value=[same_duplicate]),
            patch("news_collector._fetch_sec_news", return_value=[]),
            patch("news_collector._fetch_macro_news", return_value=[]),
        ):
            context = get_portfolio_context(self.holdings)

        self.assertEqual(len(context["news_context"]), 1)


if __name__ == "__main__":
    unittest.main()
