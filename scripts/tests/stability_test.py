import json
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import safe_float

def test_robustness():
    print("Testing 'Safe Float' logic with corrupt inputs...")
    corrupt_inputs = ["$1,234.56", "None", "  ", "#N/A", "1.23.45", None]
    expected = [1234.56, 0.0, 0.0, 0.0, 0.0, 0.0]
    
    for i, val in enumerate(corrupt_inputs):
        result = safe_float(val)
        assert result == expected[i], f"Failed on {val}: expected {expected[i]}, got {result}"
    
    print("✅ Logic Robustness: PASSED (Handles malformed spreadsheet data).")

if __name__ == "__main__":
    test_robustness()
