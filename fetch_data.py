import json
import os
import sys
from curl_cffi import requests
from bs4 import BeautifulSoup

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

def fetch_all_symbols_totals(username="Jaymesh", password="JAY23mesh"):
    print("[*] Connecting & Logging in to iCharts...")
    session = requests.Session(impersonate="chrome120")
    base_url = "https://www.icharts.in/opt"
    
    # 1. Login
    session.get(f"{base_url}/login.php")
    res_login = session.post(f"{base_url}/login.php", data={"username": username, "password": password, "submit": "submit"})
    
    soup_login = BeautifulSoup(res_login.text, "html.parser")
    if soup_login.find("div", class_="incorrect"):
        raise PermissionError("Login failed: Invalid iCharts credentials.")
        
    session.get(f"{base_url}/OptionChain_Beta_MinuteWise.php")
    print("[+] Successfully logged in to iCharts!")

    symbols = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"]
    dashboard_data = []

    headers = {
        "Origin": "https://www.icharts.in",
        "Referer": f"{base_url}/OptionChain_Beta_MinuteWise.php",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    for sym in symbols:
        print(f"[*] Fetching totals for {sym}...")
        # Get Expiry
        r_exp = session.post(f"{base_url}/hcharts/stx8req/php/getExpiryDatesforSymbol.php", data={"sym": sym})
        try:
            exp_list = [item["id"] for item in r_exp.json()]
            exp = exp_list[0] if exp_list else ""
        except Exception:
            exp = ""

        # Fetch Table Data with buttontype = Value_btn
        data_payload = {
            "optSymbol": sym,
            "buttontype": "Value_btn",
            "optExpDate": exp,
            "optExpDate_hist": exp,
            "striketype": "allstrikes",
            "txtDate": "2026-08-07",
            "defaultDate": "2026-08-07"
        }

        res = session.post(f"{base_url}/OptionChainTable_Beta_Min_Wise_v15.php", data=data_payload, headers=headers)
        j = res.json()

        c_oi = j.get("Total_Call_OI_stats", 0) or 0
        p_oi = j.get("Total_Put_OI_stats", 0) or 0
        net_oi_num = p_oi - c_oi

        c_oi_chg = j.get("Total_Call_OI_Chg_stats", 0) or 0
        p_oi_chg = j.get("Total_Put_OI_Chg_stats", 0) or 0
        net_oi_chg_num = p_oi_chg - c_oi_chg

        c_vol = j.get("Total_Call_Volume_stats", 0) or 0
        p_vol = j.get("Total_Put_Volume_stats", 0) or 0
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

        # Sentiment estimation
        pcr_oi = j.get("PCR_OI_stats", "N.A.")
        pcr_val = j.get("pcr_val", "1.0")

        sym_entry = {
            "symbol": sym,
            "expiry": exp,
            "pcr_oi": pcr_oi,
            "pcr_val": pcr_val,
            "strike_atm": j.get("strikePriceATM", "N/A"),
            "totals": {
                "total_oi": {
                    "stat": "Total OI",
                    "calls": c_oi_str,
                    "puts": p_oi_str,
                    "net": net_oi_str,
                    "net_num": net_oi_num
                },
                "total_oi_chg": {
                    "stat": "Total OI Chg",
                    "calls": c_oi_chg_str,
                    "puts": p_oi_chg_str,
                    "net": net_oi_chg_str,
                    "net_num": net_oi_chg_num
                },
                "total_vol": {
                    "stat": "Total Volume",
                    "calls": c_vol_str,
                    "puts": p_vol_str,
                    "net": net_vol_str,
                    "net_num": net_vol_num
                }
            }
        }
        dashboard_data.append(sym_entry)

    # Save to data.json
    out_dir = os.path.dirname(os.path.abspath(__file__))
    data_json_path = os.path.join(out_dir, "data.json")
    with open(data_json_path, "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, indent=2)

    print(f"[+] Dashboard data successfully updated at {data_json_path}")
    return dashboard_data

if __name__ == "__main__":
    fetch_all_symbols_totals()
