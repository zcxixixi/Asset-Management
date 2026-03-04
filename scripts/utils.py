import pandas as pd

def safe_float(v):
    if pd.isna(v) or v is None:
        return 0.0
    try:
        if isinstance(v, str):
            v = v.replace(',', '').replace('$', '').replace('%', '').strip()
            if not v:
                return 0.0
            return float(v)
        return float(v)
    except (ValueError, TypeError, AttributeError):
        return 0.0
