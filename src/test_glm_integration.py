import unittest
from unittest.mock import MagicMock, patch
import json
import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from extract_data import generate_llm_briefing

class TestGLMIntegration(unittest.TestCase):
    @patch('extract_data.OpenAI')
    @patch('extract_data.os.getenv')
    def test_generate_llm_briefing_glm(self, mock_getenv, mock_openai_class):
        # Setup mocks
        mock_getenv.side_effect = lambda k, default=None: {
            'GLM_API_KEY': 'test-key',
            'GLM_BASE_URL': 'https://api.glm.ai/v1',
            'GLM_MODEL': 'glm-5'
        }.get(k, default)

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=json.dumps({
            "headline": "GLM-5 Analysis",
            "macro_summary": "Summary",
            "verdict": "Verdict",
            "suggestions": [{"asset": "NVDA.US", "action": "Hold", "rationale": "Reason"}],
            "risks": ["Risk"]
        })))]
        mock_client.chat.completions.create.return_value = mock_response

        # Test data
        assets = [{"label": "US Stocks", "value": "1000"}]
        holdings = [{"symbol": "NVDA.US", "name": "Nvidia", "qty": "1", "value": "100"}]
        perf_7d = 0.05
        news_items = [{"symbol": "NVDA.US", "title": "Big News"}]

        # Call function
        result = generate_llm_briefing(assets, holdings, perf_7d, news_items)

        # Assertions
        mock_openai_class.assert_called_with(api_key='test-key', base_url='https://api.glm.ai/v1')
        self.assertEqual(result['headline'], "GLM-5 Analysis")
        self.assertEqual(result['source'], "llm:glm-5")

if __name__ == '__main__':
    unittest.main()
