import json
import unittest
import os
from advisor_contract import validate_payload, generate_fallback

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures', 'advisor_contract')

class TestAdvisorContract(unittest.TestCase):

    def load_fixture(self, filename: str) -> dict:
        filepath = os.path.join(FIXTURES_DIR, filename)
        with open(filepath, 'r') as f:
            return json.load(f)

    def test_normal_fixture_is_valid(self):
        """Test that a complete, normal advisory JSON passes validation."""
        data = self.load_fixture('normal.json')
        is_valid = validate_payload(data)
        self.assertTrue(is_valid, "Normal fixture failed validation, but it should be valid.")

    def test_no_news_fixture_is_valid(self):
        """Test that a briefing without news still passes validation (empty lists allowed)."""
        data = self.load_fixture('no_news.json')
        is_valid = validate_payload(data)
        self.assertTrue(is_valid, "No-news fixture failed validation, but it should be valid.")

    def test_missing_required_field(self):
        """Test that missing a required field causes validation to fail."""
        data = self.load_fixture('normal.json')
        del data['verdict'] # Remove a required field
        is_valid = validate_payload(data)
        self.assertFalse(is_valid, "Payload missing 'verdict' should fail validation.")

    def test_invalid_enum_value(self):
        """Test that passing an invalid value for an enum field causes validation to fail."""
        data = self.load_fixture('normal.json')
        data['verdict'] = "UNCERTAIN" # Invalid enum, should be BULLISH, BEARISH, or NEUTRAL
        is_valid = validate_payload(data)
        self.assertFalse(is_valid, "Payload with invalid verdict enum should fail validation.")
        
    def test_fallback_schema_compliance(self):
        """Test that the deterministic fallback generator creates a payload that strictly adheres to the schema."""
        fallback_data = generate_fallback()
        is_valid = validate_payload(fallback_data)
        self.assertTrue(is_valid, "The generated fallback payload failed schema validation!")
        
        # Also ensure it matches our fallback fixture for sanity checking
        fallback_fixture = self.load_fixture('llm_bad_json_fallback.json')
        
        # We can't strictly compare generated_at since it's dynamic, but we can compare the rest
        self.assertEqual(fallback_data['source'], fallback_fixture['source'])
        self.assertEqual(fallback_data['verdict'], fallback_fixture['verdict'])

if __name__ == '__main__':
    unittest.main()
