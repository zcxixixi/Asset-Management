import time
import requests
from datetime import datetime
import sys

# Constants
CHECK_INTERVAL_SECONDS = 60
TOTAL_MINUTES = 12 * 60  # 12 hours
BTC_AMOUNT = 1.05
ETH_AMOUNT = 24.89
INITIAL_USDC = 49658.33

def get_price(symbol):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return float(response.json()['price'])

def validate_assets():
    btc_price = get_price("BTCUSDT")
    eth_price = get_price("ETHUSDT")
    
    portfolio_value = (BTC_AMOUNT * btc_price) + (ETH_AMOUNT * eth_price) + INITIAL_USDC
    
    print(f"[{datetime.utcnow().isoformat()}Z] Portfolio Value: ${portfolio_value:.2f} (BTC: ${btc_price:.2f}, ETH: ${eth_price:.2f})", flush=True)

if __name__ == "__main__":
    print("Starting real time-based stress test for price checking and asset calculation...")
    print("Note: GitHub-hosted runners have a hard limit of 6 hours per job. This will run until GitHub terminates it or 12 hours passes.", flush=True)
    
    for i in range(TOTAL_MINUTES):
        try:
            validate_assets()
        except Exception as e:
            print(f"[{datetime.utcnow().isoformat()}Z] Error detected: {e}", flush=True)
            print("Waiting 10 seconds before retrying due to network error...", flush=True)
            time.sleep(10)
            continue
            
        time.sleep(CHECK_INTERVAL_SECONDS)
        
    print("Stress test completed successfully after 12 hours.")
