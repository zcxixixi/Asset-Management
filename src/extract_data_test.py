import gspread
import traceback

SHEET_ID = '1_J8C9rKSRR0SbmOHO1N2ixeerdQ8GM-aKG4jJkWFniE'

try:
    gc = gspread.service_account()
    sh = gc.open_by_key(SHEET_ID)
    print("SUCCESS: Access granted.")
except Exception:
    traceback.print_exc()
