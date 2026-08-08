import time
import os
import sys
import json
import logging
from fetch_all_216_full import fetch_all_symbols

logging.basicConfig(
    filename=r"C:\Users\Manan\.gemini\antigravity\scratch\icharts_dashboard\updater.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

INTERVAL_SECONDS = 180  # 3 minutes

def run_scheduler():
    print(f"[*] Starting 3-minute live iCharts auto-updater daemon...")
    logging.info("Starting 3-minute live iCharts auto-updater daemon...")
    
    while True:
        try:
            start_t = time.time()
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Triggering live iCharts data refresh...")
            count = fetch_all_symbols()
            elapsed = time.time() - start_t
            msg = f"Refreshed {count} symbols successfully in {elapsed:.2f} seconds."
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}")
            logging.info(msg)
        except Exception as e:
            err_msg = f"Error during data refresh: {e}"
            print(f"[!] {err_msg}")
            logging.error(err_msg)

        print(f"[*] Waiting {INTERVAL_SECONDS} seconds for next update cycle...\n")
        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    run_scheduler()
