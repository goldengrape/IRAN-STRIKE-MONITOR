import yfinance as yf
import json
import datetime
import os
import pandas as pd

def fetch_market_data():
    """
    Fetches real-time or latest available market data using Yahoo Finance.
    Returns a dictionary with the necessary indicators for the dashboard.
    """
    # Define tickers
    # ^VIX: CBOE Volatility Index
    # BZ=F: Brent Crude Oil Last Day Financ
    # CL=F: Crude Oil WTI (alternative if needed)
    # ^TNX: Treasury Yield 10 Years (proxy for nominal 10Y rate)
    # SPY: SPDR S&P 500 ETF Trust (for equity drop calculations)
    # HYG: iShares iBoxx $ High Yield Corporate Bond ETF (proxy for credit stress)
    # GC=F: Gold
    # DX-Y.NYB: US Dollar Index
    # TIP: iShares TIPS Bond ETF
    # ITA: iShares U.S. Aerospace & Defense ETF
    # CIBR: First Trust NASDAQ Cybersecurity ETF
    # XLP: Consumer Staples Select Sector SPDR Fund
    # QQQ: Invesco QQQ Trust
    # BTC-USD: Bitcoin
    tickers = ["^VIX", "BZ=F", "^TNX", "SPY", "HYG", "GC=F", "DX-Y.NYB", "TIP", "ITA", "CIBR", "XLP", "QQQ", "BTC-USD"]

    data = {}

    try:
        # Fetch data for the last 1 month to calculate weekly drops and trends
        hist_data = yf.download(tickers, period="1mo", progress=False)

        # Get the latest close prices
        if 'Close' in hist_data.columns:
            close_data = hist_data['Close']
            # Forward fill to handle NaNs (e.g. BTC trades on weekends while others don't)
            close_data = close_data.ffill()
            latest = close_data.iloc[-1]
            week_ago = close_data.iloc[-6] if len(close_data) >= 6 else close_data.iloc[0]
        else:
            # Fallback for single ticker or different structure
            close_data = hist_data.ffill()
            latest = close_data.iloc[-1]
            week_ago = close_data.iloc[-6] if len(close_data) >= 6 else close_data.iloc[0]

        # Extract 7-day historical trend for charts (excluding today's incomplete data if we only want full days, or just take the last 7 rows)
        last_7_days = close_data.tail(7)

        historical_trends = {
            "dates": [date.strftime("%Y-%m-%d") for date in last_7_days.index],
            "VIX": [float(val) if not pd.isna(val) else 0 for val in last_7_days.get('^VIX', [0]*7)],
            "Brent_Oil": [float(val) if not pd.isna(val) else 0 for val in last_7_days.get('BZ=F', [0]*7)],
            "US_10Y_Yield": [float(val) if not pd.isna(val) else 0 for val in last_7_days.get('^TNX', [0]*7)],
            "SPY": [float(val) if not pd.isna(val) else 0 for val in last_7_days.get('SPY', [0]*7)],
            "HYG": [float(val) if not pd.isna(val) else 0 for val in last_7_days.get('HYG', [0]*7)],
            "Gold": [float(val) if not pd.isna(val) else 0 for val in last_7_days.get('GC=F', [0]*7)],
            "USD_Index": [float(val) if not pd.isna(val) else 0 for val in last_7_days.get('DX-Y.NYB', [0]*7)],
            "TIP": [float(val) if not pd.isna(val) else 0 for val in last_7_days.get('TIP', [0]*7)],
            "ITA": [float(val) if not pd.isna(val) else 0 for val in last_7_days.get('ITA', [0]*7)],
            "CIBR": [float(val) if not pd.isna(val) else 0 for val in last_7_days.get('CIBR', [0]*7)],
            "XLP": [float(val) if not pd.isna(val) else 0 for val in last_7_days.get('XLP', [0]*7)],
            "QQQ": [float(val) if not pd.isna(val) else 0 for val in last_7_days.get('QQQ', [0]*7)],
            "BTC": [float(val) if not pd.isna(val) else 0 for val in last_7_days.get('BTC-USD', [0]*7)]
        }

        # Extract specific values safely
        vix = float(latest.get('^VIX', 0))
        brent = float(latest.get('BZ=F', 0))
        tnx = float(latest.get('^TNX', 0)) # 10Y Nominal Yield
        gold = float(latest.get('GC=F', 0))
        usd = float(latest.get('DX-Y.NYB', 0))
        tip = float(latest.get('TIP', 0))
        ita = float(latest.get('ITA', 0))
        cibr = float(latest.get('CIBR', 0))
        xlp = float(latest.get('XLP', 0))
        qqq = float(latest.get('QQQ', 0))
        btc = float(latest.get('BTC-USD', 0))

        spy_latest = float(latest.get('SPY', 0))
        spy_week_ago = float(week_ago.get('SPY', 0))
        spy_weekly_drop = ((spy_latest - spy_week_ago) / spy_week_ago) * 100 if spy_week_ago > 0 else 0

        hyg_latest = float(latest.get('HYG', 0))
        hyg_week_ago = float(week_ago.get('HYG', 0))
        # A drop in HYG indicates widening credit spreads (proxy)
        hyg_drop = ((hyg_latest - hyg_week_ago) / hyg_week_ago) * 100 if hyg_week_ago > 0 else 0

        tip_latest = float(latest.get('TIP', 0))
        tip_week_ago = float(week_ago.get('TIP', 0))
        tip_change = ((tip_latest - tip_week_ago) / tip_week_ago) * 100 if tip_week_ago > 0 else 0

        # Construct the output dictionary
        data = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "indicators": {
                "VIX": {"value": round(vix, 2), "threshold": 20, "unit": ""},
                "Brent_Oil": {"value": round(brent, 2), "threshold": 90, "unit": "$/bbl"},
                "US_10Y_Yield": {"value": round(tnx, 2), "threshold": 4.5, "unit": "%"},
                "SPY_Weekly_Change": {"value": round(spy_weekly_drop, 2), "threshold": -3.0, "unit": "%"},
                "HYG_Weekly_Change": {"value": round(hyg_drop, 2), "threshold": -1.0, "unit": "%"}, # proxy for credit spread widening
                "Gold": {"value": round(gold, 2), "threshold": 2500, "unit": "$/oz"},
                "USD_Index": {"value": round(usd, 2), "threshold": 105, "unit": ""},
                "TIP_ETF": {"value": round(tip, 2), "threshold": 110, "unit": "$"},
                "ITA_ETF": {"value": round(ita, 2), "threshold": 140, "unit": "$"},
                "CIBR_ETF": {"value": round(cibr, 2), "threshold": 65, "unit": "$"},
                "XLP_ETF": {"value": round(xlp, 2), "threshold": 80, "unit": "$"},
                "QQQ_ETF": {"value": round(qqq, 2), "threshold": 450, "unit": "$"},
                "BTC": {"value": round(btc, 2), "threshold": 80000, "unit": "$"}
            },
            "historical_trends": historical_trends
        }
    except Exception as e:
        print(f"Error fetching data: {e}")
        # Return fallback data structure on error
        data = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "error": str(e),
            "indicators": {
                "VIX": {"value": 0, "threshold": 20, "unit": ""},
                "Brent_Oil": {"value": 0, "threshold": 90, "unit": "$/bbl"},
                "US_10Y_Yield": {"value": 0, "threshold": 4.5, "unit": "%"},
                "SPY_Weekly_Change": {"value": 0, "threshold": -3.0, "unit": "%"},
                "HYG_Weekly_Change": {"value": 0, "threshold": -1.0, "unit": "%"},
                "Gold": {"value": 0, "threshold": 2500, "unit": "$/oz"},
                "USD_Index": {"value": 0, "threshold": 105, "unit": ""},
                "TIP_ETF": {"value": 0, "threshold": 110, "unit": "$"},
                "ITA_ETF": {"value": 0, "threshold": 140, "unit": "$"},
                "CIBR_ETF": {"value": 0, "threshold": 65, "unit": "$"},
                "XLP_ETF": {"value": 0, "threshold": 80, "unit": "$"},
                "QQQ_ETF": {"value": 0, "threshold": 450, "unit": "$"},
                "BTC": {"value": 0, "threshold": 80000, "unit": "$"}
            },
            "historical_trends": {"dates": [], "VIX": [], "Brent_Oil": [], "US_10Y_Yield": [], "SPY": [], "HYG": [], "Gold": [], "USD_Index": [], "TIP": [], "ITA": [], "CIBR": [], "XLP": [], "QQQ": [], "BTC": []}
        }

    return data

if __name__ == "__main__":
    market_data = fetch_market_data()

    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    # Write to current JSON
    with open("data/data.json", "w", encoding="utf-8") as f:
        json.dump(market_data, f, indent=4)

    # Maintain historical data
    history_file = "data/history.json"
    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        except json.JSONDecodeError:
            print(f"Error reading {history_file}, starting fresh.")
            history = []

    # Append new data point
    history.append(market_data)

    # Save history back
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)

    # Generate RSS Feed
    rss_file = "data/rss.xml"
    rss_items = ""
    # Sort history to have newest items first in RSS
    sorted_history = sorted(history, key=lambda x: x["timestamp"], reverse=True)

    # Cap RSS at last 30 items to keep feed size manageable
    for item in sorted_history[:30]:
        pub_date = datetime.datetime.fromisoformat(item["timestamp"]).strftime("%a, %d %b %Y %H:%M:%S +0000")

        if "error" in item:
            description = f"Error fetching data: {item['error']}"
        else:
            inds = item.get("indicators", {})
            description = (
                f"VIX: {inds.get('VIX', {}).get('value', 0)} | "
                f"Brent Oil: {inds.get('Brent_Oil', {}).get('value', 0)} $/bbl | "
                f"10Y Yield: {inds.get('US_10Y_Yield', {}).get('value', 0)} % | "
                f"SPY: {inds.get('SPY_Weekly_Change', {}).get('value', 0)} % | "
                f"HYG: {inds.get('HYG_Weekly_Change', {}).get('value', 0)} % | "
                f"Gold: {inds.get('Gold', {}).get('value', 0)} | "
                f"USD: {inds.get('USD_Index', {}).get('value', 0)} | "
                f"BTC: {inds.get('BTC', {}).get('value', 0)}"
            )

        rss_items += f"""
        <item>
            <title>Market Data Update: {pub_date}</title>
            <description>{description}</description>
            <pubDate>{pub_date}</pubDate>
            <guid isPermaLink="false">{item["timestamp"]}</guid>
        </item>"""

    rss_content = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
    <channel>
        <title>Geopolitical Market Dashboard RSS Feed</title>
        <description>Daily updates on key macroeconomic indicators (VIX, Brent, US10Y, SPY, HYG) tracking geopolitical risks.</description>
        <link>https://github.com/jules-11467788464661651638/geopolitical-dashboard</link>
        <lastBuildDate>{datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")}</lastBuildDate>
        {rss_items}
    </channel>
</rss>"""

    with open(rss_file, "w", encoding="utf-8") as f:
        f.write(rss_content)

    print("Market data, history, and RSS feed updated successfully.")
