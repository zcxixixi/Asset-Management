import unittest
from unittest.mock import patch
import os
import sys
import json

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from extract_data import extract_data

class TestPipelineIntegration(unittest.TestCase):
    @patch('extract_data.get_portfolio_context')
    @patch('extract_data.generate_briefing')
    @patch('extract_data.sync_workbook')
    def test_pipeline_execution_mocked(self, mock_sync, mock_generate, mock_context):
        # Setup mocks
        mock_sync.return_value = {"last_daily_date": "2026-03-01", "daily_count": 10, "backup_path": "mock/path"}
        
        mock_context.return_value = {
            "news_context": [{"headline": "Test News 1"}],
            "global_context": [{"headline": "Test Macro 1"}]
        }
        
        mock_generate.return_value = {
            "verdict": "BULLISH",
            "suggestions": [{"asset": "NVDA", "action": "HOLD", "rationale": "Reason"}],
            "macro_summary": "Test Summary",
            "headline": "Test Headline"
        }
        
        # Test data extraction (time travel to avoid yfinance actual calls)
        result = extract_data(mock_date_str="2026-03-01")
        
        # Verify the pipeline called out to the sub-agents correctly
        self.assertEqual(result["advisor_briefing"]["verdict"], "BULLISH")
        self.assertEqual(len(result["insights"]), 1)
        self.assertEqual(result["insights"][0]["asset"], "NVDA")

if __name__ == '__main__':
    unittest.main()
