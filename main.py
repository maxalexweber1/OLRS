import pandas as pd
import requests
import logging
import math

# API constants
BASE_URL_TOKEN_OHLCV = "https://openapi.taptools.io/api/v1/token/ohlcv"
BASE_URL_TOKEN = "https://openapi.taptools.io/api/v1/token/mcap"
HEADERS = {"x-api-key": "XXXXXXXXXXXXXXXXXX"}

# Mapping for Ticker to Token unit (policy + hex name)
TOKEN_ID_MAPPING = {
    "SNEK": "279c909f348e533da5808898f87f9a14bb2c3dfbbacccd631d927a3f534e454b",
    "HUNT": "95a427e384527065f2f8946f5e86320d0117839a5e98ea2c0b55fb0048554e54",
    "LENFI": "8fef2d34078659493ce161a6c7fba4b56afefa8535296a5743f6958741414441",
    "IAG": "5d16cc1a177b5d9ba9cfa9793b07e60f1fb70fea1f8aef064415d114494147",
    "BTN": "016be5325fd988fea98ad422fcfd53e5352cacfced5c106a932a35a442544e",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load CSV file
def load_csv_data(csv_file):
    df = pd.read_csv(csv_file)
    df.columns = [col.upper() for col in df.columns]  # Normalize column names to uppercase
    df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
    return df

# General API request function
def api_request(url, params=None):
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed: {url} - {e}")
        return None

# Retrieve historical token prices
def get_token_price_by_id(token_id, interval, timeframe):
    data = api_request(BASE_URL_TOKEN_OHLCV, {"unit": token_id, "interval": interval, "numIntervals": timeframe})
    if not data:
        return None
    try:
        df = pd.DataFrame(data)
        df["DATE"] = pd.to_datetime(df["time"], unit="s").dt.date
        df["volatility"] = ((df["high"] - df["low"]) / df["low"]).clip(lower=0) * 100
        return df[["DATE", "close", "volatility", "volume"]]
    except Exception as e:
        logging.error(f"Error parsing token price data: {e}")
        return None

# get circulating supply from taptools api
def get_token_circ_supply(token_id):
    token_stats = api_request(BASE_URL_TOKEN, {"unit": token_id})
    if token_stats and "circSupply" in token_stats:
        return max(round(float(token_stats["circSupply"])), 1)
    return None

# OLRS calculation
def calculate_olrs(avg_hs, volatility, volume, market_cap_ada):
    # weight factors health sore, volatility, liquidity, marketcap 
    w_hs,w_v, w_l, w_mc = 0.55, 0.15, 0.2, 0.1

    if avg_hs < 1:
        hs_component = 100 # worst-case - highest Risk
    elif avg_hs >= 4:
        hs_component = 0  #  
    else:
        hs_component = (min(100, (4 - avg_hs) * 50 + 50))  # linear decrease between 1 and 4

    # volatility -linear and exponential volatility effects.
    v_component = min(((volatility + volatility**2) / 2), 100)

    # liquidity scaling, stronger effect with low volumes (<200k ADA)
    l_component = ((1 - min(volume / 200_000, 1)) ** 2) * 100

    # market cap 
    mc_component = max(((10 - math.log10(max(market_cap_ada, 10**6))) / 4) * 100, 0)

    return round((w_hs * hs_component) + (w_v * v_component) + (w_l * l_component) + (w_mc * mc_component), 2)

# process CSV row by row and merge API data
def process_and_merge_data(csv_file, token_id, output_file):
    try:
        csv_data = load_csv_data(csv_file)
    except Exception as e:
        logging.error(f"Error loading CSV file: {e}")
        return

    token_price_data = get_token_price_by_id(token_id, "1d", 180)
    circ_supply = get_token_circ_supply(token_id)

    if token_price_data is not None:
        if circ_supply:
            token_price_data["market_cap_ada"] = token_price_data["close"] * circ_supply

        results = []
        for _, row in csv_data.iterrows():
            date = row["DATE"].date()
            token_row = token_price_data[token_price_data["DATE"] == date]

            if not token_row.empty:
                row = row.to_dict()
                row.update(token_row.iloc[0].to_dict())
                row["olrs"] = calculate_olrs(row.get("AVG_HEALTH", 1), row["volatility"], row["volume"], row["market_cap_ada"])
            results.append(row)

        result_df = pd.DataFrame(results)
        result_df.to_csv(output_file, index=False)
        logging.info(f"File saved: {output_file}")
    else:
        logging.warning("No API data available. CSV file remains unchanged.")

if __name__ == "__main__":
    # SNEK
    process_and_merge_data("data/SNEK.csv", TOKEN_ID_MAPPING["SNEK"], "data/SNEK_with_OLRS.csv")
    # IAG
    process_and_merge_data("data/IAG.csv", TOKEN_ID_MAPPING["IAG"], "data/IAG_with_OLRS.csv")
    # HUNT
    process_and_merge_data("data/HUNT.csv", TOKEN_ID_MAPPING["HUNT"], "data/HUNT_with_OLRS.csv")
    # LENFI
    process_and_merge_data("data/LENFI.csv", TOKEN_ID_MAPPING["LENFI"], "data/LENFI_with_OLRS.csv")
    # BTN
    process_and_merge_data("data/BTN.csv", TOKEN_ID_MAPPING["BTN"], "data/BTN_with_OLRS.csv")
