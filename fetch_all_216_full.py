import json
import time
import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

STORE_FILE = os.path.join(os.path.dirname(__file__), "backend_store.json")
DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")

def load_persistent_store():
    if os.path.exists(STORE_FILE):
        try:
            with open(STORE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data_list = json.load(f)
                return {item["symbol"]: item for item in data_list if "symbol" in item}
        except Exception:
            pass
    return {}

def save_persistent_store(store_dict):
    try:
        with open(STORE_FILE, "w", encoding="utf-8") as f:
            json.dump(store_dict, f, indent=2)
    except Exception as e:
        print("Error saving backend_store.json:", e)

def format_val(val):
    if val is None or val == "N.A.":
        return "N/A", 0
    try:
        num_val = float(val)
        abs_val = abs(num_val)
        if abs_val >= 10000000:
            formatted = f"{num_val / 10000000:.2f} Cr"
        elif abs_val >= 100000:
            formatted = f"{num_val / 100000:.2f} L"
        else:
            formatted = f"{num_val:,.2f}"
        return formatted, num_val
    except Exception:
        return str(val), 0

def safe_json(res):
    if res and res.status_code == 200:
        try:
            return res.json()
        except Exception:
            pass
    return {}

def fetch_complete_symbol_data(sym_item, cookies, existing_cached_item):
    sym, exp = sym_item
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Origin": "https://www.icharts.in",
        "Referer": "https://www.icharts.in/opt/OptionChain_Beta_MinuteWise.php"
    })
    session.cookies.update(cookies)

    base_url = "https://www.icharts.in/opt"
    headers = {
        "Origin": "https://www.icharts.in",
        "Referer": f"{base_url}/OptionChain_Beta_MinuteWise.php",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    time.sleep(0.1)  # Throttle per worker to avoid Nginx 429 Too Many Requests

    try:
        # 1. Fetch OptionChain in VALUE mode
        payload_val = {
            "optSymbol": sym,
            "buttontype": "Value_btn",
            "optExpDate": exp,
            "optExpDate_hist": exp,
            "striketype": "allstrikes",
            "txtDate": "2026-08-07",
            "defaultDate": "2026-08-07"
        }
        res_val = session.post(f"{base_url}/OptionChainTable_Beta_Min_Wise_v15.php", data=payload_val, headers=headers, timeout=10)

        # 2. Fetch OptionChain in QTY mode (Quantity_btn)
        payload_qty = {
            "optSymbol": sym,
            "buttontype": "Quantity_btn",
            "optExpDate": exp,
            "optExpDate_hist": exp,
            "striketype": "allstrikes",
            "txtDate": "2026-08-07",
            "defaultDate": "2026-08-07"
        }
        res_qty = session.post(f"{base_url}/OptionChainTable_Beta_Min_Wise_v15.php", data=payload_qty, headers=headers, timeout=10)

        # 3. Fetch Future OI from SymbolDashboard.php
        payload_dash = {
            "optSymbol": sym,
            "rdDataType": "latest",
            "txtDate": "2026-08-07"
        }
        res_dash = session.post(f"{base_url}/api/dashboard/php/getDataForSymbolDashboard.php", data=payload_dash, headers=headers, timeout=10)

        # Handle Nginx HTTP 429 Rate Limiting / Connection Errors
        if res_val.status_code == 429 or res_qty.status_code == 429 or res_dash.status_code == 429:
            if existing_cached_item:
                return existing_cached_item

        j_val = safe_json(res_val)
        j_qty = safe_json(res_qty)
        j_dash = safe_json(res_dash)

        sym_dash = j_dash.get("symbolDashboard", {}) if isinstance(j_dash, dict) else {}
        
        try:
            fresh_fut_oi = float(sym_dash.get("Current_Month_OI", 0) or 0) if isinstance(sym_dash, dict) else 0
            fresh_fut_oi_chg = float(sym_dash.get("Current_Month_OIChg", 0) or 0) if isinstance(sym_dash, dict) else 0
        except Exception:
            fresh_fut_oi = 0
            fresh_fut_oi_chg = 0

        # Persistent Fallback for Future OI if iCharts session disconnected / returned 0
        if (not fresh_fut_oi or fresh_fut_oi == 0) and existing_cached_item and existing_cached_item.get("future_oi", 0) > 0:
            future_oi = existing_cached_item["future_oi"]
            future_oi_chg = existing_cached_item.get("future_oi_chg", 0)
        else:
            future_oi = fresh_fut_oi or (existing_cached_item.get("future_oi", 0) if existing_cached_item else 0)
            future_oi_chg = fresh_fut_oi_chg or (existing_cached_item.get("future_oi_chg", 0) if existing_cached_item else 0)

        # Extract Value mode Totals
        c_oi = j_val.get("Total_Call_OI_stats") or j_val.get("total_call_oi_val") or j_val.get("total_call_oi") or 0
        p_oi = j_val.get("Total_Put_OI_stats") or j_val.get("total_put_oi_val") or j_val.get("total_put_oi") or 0
        c_oi_chg = j_val.get("Total_Call_OI_Chg_stats") or j_val.get("total_call_oi_chg_val") or j_val.get("total_call_oi_change") or 0
        p_oi_chg = j_val.get("Total_Put_OI_Chg_stats") or j_val.get("total_put_oi_chg_val") or j_val.get("total_put_oi_change") or 0
        c_vol = j_val.get("Total_Call_Volume_stats") or j_val.get("total_call_volume") or 0
        p_vol = j_val.get("Total_Put_Volume_stats") or j_val.get("total_put_volume") or 0

        # Fallback to cached totals if fresh fetch is empty/zero
        if c_oi == 0 and p_oi == 0 and c_oi_chg == 0 and p_oi_chg == 0 and existing_cached_item and "totals" in existing_cached_item:
            c_oi = existing_cached_item["totals"]["total_oi"]["calls_num"]
            p_oi = existing_cached_item["totals"]["total_oi"]["puts_num"]
            c_oi_chg = existing_cached_item["totals"]["total_oi_chg"]["calls_num"]
            p_oi_chg = existing_cached_item["totals"]["total_oi_chg"]["puts_num"]
            c_vol = existing_cached_item["totals"]["total_vol"]["calls_num"]
            p_vol = existing_cached_item["totals"]["total_vol"]["puts_num"]

        net_oi_num = p_oi - c_oi
        net_oi_chg_num = p_oi_chg - c_oi_chg
        net_vol_num = p_vol - c_vol

        c_oi_str, _ = format_val(c_oi)
        p_oi_str, _ = format_val(p_oi)
        net_oi_str, _ = format_val(net_oi_num)

        c_oi_chg_str, _ = format_val(c_oi_chg)
        p_oi_chg_str, _ = format_val(p_oi_chg)
        net_oi_chg_str, _ = format_val(net_oi_chg_num)

        c_vol_str, _ = format_val(c_vol)
        p_vol_str, _ = format_val(p_vol)
        net_vol_str, _ = format_val(net_vol_num)

        # Extract QTY mode OTM Totals (Screenshot 1: OTM table)
        otm_c_oi_qty = j_qty.get("Total_Call_OTM_OI_stats") or 0
        otm_p_oi_qty = j_qty.get("Total_Put_OTM_OI_stats") or 0
        otm_c_chg_qty = j_qty.get("Total_Call_OTM_OI_Chg_stats") or 0
        otm_p_chg_qty = j_qty.get("Total_Put_OTM_OI_Chg_stats") or 0

        # Persistent Fallback for QTY OTM metrics if iCharts session disconnected / returned 0
        if otm_c_oi_qty == 0 and otm_p_oi_qty == 0 and otm_c_chg_qty == 0 and otm_p_chg_qty == 0 and existing_cached_item and "otm_qty" in existing_cached_item:
            otm_c_oi_qty = existing_cached_item["otm_qty"].get("total_otm_oi_calls_num", 0)
            otm_p_oi_qty = existing_cached_item["otm_qty"].get("total_otm_oi_puts_num", 0)
            otm_c_chg_qty = existing_cached_item["otm_qty"].get("total_otm_oi_chg_calls_num", 0)
            otm_p_chg_qty = existing_cached_item["otm_qty"].get("total_otm_oi_chg_puts_num", 0)

        otm_net_chg_qty = otm_p_chg_qty - otm_c_chg_qty

        otm_c_vol_qty = j_qty.get("Total_Call_OTM_Volume_stats") or 0
        otm_p_vol_qty = j_qty.get("Total_Put_OTM_Volume_stats") or 0

        # Extract QTY mode ITM Totals
        itm_c_oi_qty = j_qty.get("Total_Call_ITM_OI_stats") or 0
        itm_p_oi_qty = j_qty.get("Total_Put_ITM_OI_stats") or 0
        itm_c_chg_qty = j_qty.get("Total_Call_ITM_OI_Chg_stats") or 0
        itm_p_chg_qty = j_qty.get("Total_Put_ITM_OI_Chg_stats") or 0

        pcr_oi = j_val.get("PCR_OI_stats") or j_val.get("pcr_val") or (existing_cached_item.get("pcr_oi") if existing_cached_item else "N.A.")
        pcr_val = j_val.get("pcr_val") or (existing_cached_item.get("pcr_val") if existing_cached_item else "1.0")
        future_oi_str, _ = format_val(future_oi)

        # Strategy 2 Rule Evaluation:
        # Future OI * 15% < Total OTM OI Chg (Calls) OR Total OTM OI Chg (Puts)
        threshold_15pct = future_oi * 0.15
        strat2_calls_pass = otm_c_chg_qty > threshold_15pct if threshold_15pct > 0 else False
        strat2_puts_pass = otm_p_chg_qty > threshold_15pct if threshold_15pct > 0 else False
        strat2_match = strat2_calls_pass or strat2_puts_pass

        # Strategy 1 Rule Evaluation:
        # Rule 1: Total OI Chg Net > Total OI Calls AND Total OI Puts
        # Rule 2: Calls OI Chg < 0 OR Puts OI Chg < 0
        strat1_rule1 = (net_oi_chg_num > c_oi) and (net_oi_chg_num > p_oi)
        strat1_rule1_abs = (abs(net_oi_chg_num) > c_oi) and (abs(net_oi_chg_num) > p_oi)
        strat1_rule2 = (c_oi_chg < 0) or (p_oi_chg < 0)
        strat1_match = (strat1_rule1 or strat1_rule1_abs) and strat1_rule2

        return {
            "symbol": sym,
            "expiry": exp,
            "pcr_oi": str(pcr_oi),
            "pcr_val": str(pcr_val),
            "strike_atm": j_val.get("strikePriceATM") or (existing_cached_item.get("strike_atm") if existing_cached_item else "N/A"),
            "future_oi": future_oi,
            "future_oi_str": future_oi_str,
            "future_oi_chg": future_oi_chg,
            "threshold_15pct": threshold_15pct,
            "threshold_15pct_str": format_val(threshold_15pct)[0],
            "strategy2_match": strat2_match,
            "strategy2_calls_pass": strat2_calls_pass,
            "strategy2_puts_pass": strat2_puts_pass,
            "strategy1_match": strat1_match,
            "otm_qty": {
                "total_otm_oi_calls": format_val(otm_c_oi_qty)[0],
                "total_otm_oi_puts": format_val(otm_p_oi_qty)[0],
                "total_otm_oi_chg_calls": format_val(otm_c_chg_qty)[0],
                "total_otm_oi_chg_puts": format_val(otm_p_chg_qty)[0],
                "total_otm_oi_chg_net": format_val(otm_net_chg_qty)[0],
                "total_otm_oi_calls_num": otm_c_oi_qty,
                "total_otm_oi_puts_num": otm_p_oi_qty,
                "total_otm_oi_chg_calls_num": otm_c_chg_qty,
                "total_otm_oi_chg_puts_num": otm_p_chg_qty,
                "total_otm_oi_chg_net_num": otm_net_chg_qty,
                "total_otm_vol_calls": format_val(otm_c_vol_qty)[0],
                "total_otm_vol_puts": format_val(otm_p_vol_qty)[0],
                "pcr_otm_oi": j_qty.get("PCR_OTM_OI_stats", "N.A."),
                "pcr_otm_oi_chg": j_qty.get("PCR_OTM_OI_Chg_stats", "N.A.")
            },
            "itm_qty": {
                "total_itm_oi_calls": format_val(itm_c_oi_qty)[0],
                "total_itm_oi_puts": format_val(itm_p_oi_qty)[0],
                "total_itm_oi_chg_calls": format_val(itm_c_chg_qty)[0],
                "total_itm_oi_chg_puts": format_val(itm_p_chg_qty)[0],
                "pcr_itm_oi": j_qty.get("PCR_ITM_OI_stats", "N.A."),
                "pcr_itm_oi_chg": j_qty.get("PCR_ITM_OI_Chg_stats", "N.A.")
            },
            "totals": {
                "total_oi": {
                    "stat": "Total OI",
                    "calls": c_oi_str,
                    "puts": p_oi_str,
                    "net": net_oi_str,
                    "calls_num": c_oi,
                    "puts_num": p_oi,
                    "net_num": net_oi_num
                },
                "total_oi_chg": {
                    "stat": "Total OI Chg",
                    "calls": c_oi_chg_str,
                    "puts": p_oi_chg_str,
                    "net": net_oi_chg_str,
                    "calls_num": c_oi_chg,
                    "puts_num": p_oi_chg,
                    "net_num": net_oi_chg_num
                },
                "total_vol": {
                    "stat": "Total Volume",
                    "calls": c_vol_str,
                    "puts": p_vol_str,
                    "net": net_vol_str,
                    "calls_num": c_vol,
                    "puts_num": p_vol,
                    "net_num": net_vol_num
                }
            }
        }
    except Exception as e:
        # Return existing cached item if exception occurred
        if existing_cached_item:
            return existing_cached_item
        return None

def fetch_all_symbols_complete():
    map_file = os.path.join(os.path.dirname(__file__), "symbol_expiry_map.json")
    if not os.path.exists(map_file):
        map_file = r"C:\Users\Manan\.gemini\antigravity\scratch\symbol_expiry_map.json"
    with open(map_file, "r", encoding="utf-8") as f:
        expiry_map = json.load(f)

    store_dict = load_persistent_store()

    print(f"[{time.strftime('%H:%M:%S')}] Logging into iCharts for Complete Multi-Strategy Scan...")
    login_session = requests.Session()
    login_session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    
    try:
        login_session.get("https://www.icharts.in/opt/login.php", timeout=6)
        login_session.post("https://www.icharts.in/opt/login.php", data={"username": "Jaymesh", "password": "JAY23mesh", "submit": "submit"}, timeout=6)
    except Exception as e:
        print("[!] Login notice:", e)

    cookies = login_session.cookies.get_dict()

    print(f"[{time.strftime('%H:%M:%S')}] Extracting Value + QTY + Future OI with Persistent Cache for ALL {len(expiry_map)} symbols...")
    start_time = time.time()

    results = []
    items = list(expiry_map.items())
    
    # Reduced workers to 4 to avoid triggering HTTP 429 Rate Limiting
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(fetch_complete_symbol_data, item, cookies, store_dict.get(item[0])): item[0] for item in items}
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)
                store_dict[res["symbol"]] = res

    elapsed = time.time() - start_time
    print(f"[{time.strftime('%H:%M:%S')}] [SUCCESS] Extracted dataset for {len(results)} / {len(expiry_map)} symbols in {elapsed:.2f} seconds!")

    # Save persistent store
    save_persistent_store(store_dict)

    # Always write ALL cached symbols to data.json so no symbols are ever dropped or missing
    full_dataset = list(store_dict.values())
    full_dataset.sort(key=lambda x: x["symbol"])

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(full_dataset, f, indent=2)

    print(f"[+] Saved persistent dataset ({len(full_dataset)} symbols) to {DATA_FILE} and {STORE_FILE}")
    return len(full_dataset)

# Alias for backwards compatibility
fetch_all_symbols = fetch_all_symbols_complete

if __name__ == "__main__":
    fetch_all_symbols_complete()

