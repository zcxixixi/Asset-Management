import json
import pandas as pd

def safe_float(v):
    if pd.isna(v) or v is None: return 0.0
    try:
        if isinstance(v, str):
            v = v.replace(',', '').replace('$', '').strip()
            if not v: return 0.0
            return float(v)
        return float(v)
    except: return 0.0

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
