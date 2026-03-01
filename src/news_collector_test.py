import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from advisor_contract import AdvisorBriefing, NewsItem
from news_collector import get_portfolio_context


class TestNewsCollector(unittest.TestCase):
    def test_get_portfolio_context_returns_schema_valid_lists(self):
        holdings = [
            {"symbol": "NVDA.US", "value": "12000"},
            {"symbol": "TSLA.US", "value": "6000"},
            {"symbol": "AAPL.US", "value": "9000"},
            {"symbol": "GOLD.CN", "value": "3000"},
        ]

        # Force deterministic fallback path so the test never depends on live APIs.
        with patch("news_collector.yf", None):
            context = get_portfolio_context(holdings)

        self.assertIn("news_context", context)
        self.assertIn("global_context", context)
        self.assertIsInstance(context["news_context"], list)
        self.assertIsInstance(context["global_context"], list)
        self.assertGreater(len(context["news_context"]), 0)
        self.assertGreater(len(context["global_context"]), 0)

        self.assertTrue(all(isinstance(item, NewsItem) for item in context["news_context"]))
        self.assertTrue(all(isinstance(item, NewsItem) for item in context["global_context"]))

        news_scores = [item.relevance_score for item in context["news_context"] if item.relevance_score is not None]
        self.assertEqual(news_scores, sorted(news_scores, reverse=True))

        # Prove the returned lists can be embedded into the strict AdvisorBriefing schema.
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
            "news_context": [item.model_dump() for item in context["news_context"]],
            "global_context": [item.model_dump() for item in context["global_context"]],
            "disclaimer": "Test disclaimer.",
        }

        validated = AdvisorBriefing.model_validate(payload)
        self.assertIsInstance(validated.news_context, list)
        self.assertIsInstance(validated.global_context, list)


if __name__ == "__main__":
    unittest.main()
