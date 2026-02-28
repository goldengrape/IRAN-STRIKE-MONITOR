import yfinance as yf
import json
import datetime
import os

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
    tickers = ["^VIX", "BZ=F", "^TNX", "SPY", "HYG"]

    data = {}

    try:
        # Fetch data for the last 1 month to calculate weekly drops and trends
        hist_data = yf.download(tickers, period="1mo", progress=False)

        # Get the latest close prices
        if 'Close' in hist_data.columns:
            latest = hist_data['Close'].iloc[-1]
            week_ago = hist_data['Close'].iloc[-6] if len(hist_data) >= 6 else hist_data['Close'].iloc[0]
        else:
            # Fallback for single ticker or different structure
            latest = hist_data.iloc[-1]
            week_ago = hist_data.iloc[-6] if len(hist_data) >= 6 else hist_data.iloc[0]

        # Extract specific values safely
        vix = float(latest.get('^VIX', 0))
        brent = float(latest.get('BZ=F', 0))
        tnx = float(latest.get('^TNX', 0)) # 10Y Nominal Yield

        spy_latest = float(latest.get('SPY', 0))
        spy_week_ago = float(week_ago.get('SPY', 0))
        spy_weekly_drop = ((spy_latest - spy_week_ago) / spy_week_ago) * 100 if spy_week_ago > 0 else 0

        hyg_latest = float(latest.get('HYG', 0))
        hyg_week_ago = float(week_ago.get('HYG', 0))
        # A drop in HYG indicates widening credit spreads (proxy)
        hyg_drop = ((hyg_latest - hyg_week_ago) / hyg_week_ago) * 100 if hyg_week_ago > 0 else 0

        # Construct the output dictionary
        data = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "indicators": {
                "VIX": {"value": round(vix, 2), "threshold": 20, "unit": ""},
                "Brent_Oil": {"value": round(brent, 2), "threshold": 90, "unit": "$/bbl"},
                "US_10Y_Yield": {"value": round(tnx, 2), "threshold": 4.5, "unit": "%"},
                "SPY_Weekly_Change": {"value": round(spy_weekly_drop, 2), "threshold": -3.0, "unit": "%"},
                "HYG_Weekly_Change": {"value": round(hyg_drop, 2), "threshold": -1.0, "unit": "%"} # proxy for credit spread widening
            }
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
                "HYG_Weekly_Change": {"value": 0, "threshold": -1.0, "unit": "%"}
            }
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
            inds = item["indicators"]
            description = (
                f"VIX: {inds['VIX']['value']} | "
                f"Brent Oil: {inds['Brent_Oil']['value']} $/bbl | "
                f"10Y Yield: {inds['US_10Y_Yield']['value']} % | "
                f"SPY Weekly Change: {inds['SPY_Weekly_Change']['value']} % | "
                f"HYG Weekly Change: {inds['HYG_Weekly_Change']['value']} %"
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
