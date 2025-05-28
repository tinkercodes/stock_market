from __future__ import print_function
import time
import upstox_client
from upstox_client.rest import ApiException
from pprint import pprint
import os
import json
from dotenv import load_dotenv
import pandas as pd
load_dotenv()

def get_instrument_key(stocks_dict) -> str:
    """
    Generate the instrument key for Upstox API.
    
    Args:
        symbol (str): The stock symbol.
        exchange (str): The exchange code (e.g., 'NSE_EQ').
    
    Returns:
        str: The formatted instrument key.
    """
    try:
        instrument_df = pd.read_csv('instrument.csv')
        symbols = []
        for key, stock in stocks_dict.items():
            if symbol := stock.get("symbol", ""):
                symbols.append(symbol.strip().upper())
        filtered_df = instrument_df[instrument_df['trading_symbol'].isin(symbols)]
        
        for i in range(0, len(filtered_df), 100):
            chunk = filtered_df.iloc[i:i+100]
            if not chunk.empty:
                combined = chunk.apply(lambda row: f"{row['exchange']}_{row['instrument_type']}|{row['exchange_token']}", axis=1)
                yield ','.join(combined)
            else:
                print("No valid symbols found in the provided stocks.")
                yield ""
    except Exception as e:
        print(f"Error generating instrument key: {e}")
        return ""

def get_stock_change(instrument_key: str) -> None:

    configuration = upstox_client.Configuration()
    configuration.access_token = os.getenv("UPSTOX_ACCESS_TOKEN")

    if not configuration.access_token:
        raise ValueError("UPSTOX_ACCESS_TOKEN not found in environment variables.")

    api_instance = upstox_client.MarketQuoteV3Api(upstox_client.ApiClient(configuration))

    interval = '1d' # str | Interval to get ohlc data

    try:
        # Market quotes and instruments - OHLC quotes
        api_response = api_instance.get_market_quote_ohlc(interval, instrument_key=instrument_key)
        print(api_response.to_dict())
    except ApiException as e:
        print("Exception when calling MarketQuoteV3Api->get_market_quote_ohlc: %s\n" % e)
    

    # try:
    #     # Market quotes and instruments - LTP quotes.
    #     api_response = api_instance.get_ltp(instrument_key=instrument_key)
    #     print(api_response.to_dict())
    # except ApiException as e:
    #     print("Exception when calling MarketQuoteV3Api->get_ltp: %s\n" % e)

def main(stocks: list[dict]) -> None:
    """
    Main function to process stocks and fetch their changes using Upstox API.
    
    Args:
        stocks (list[dict]): List of stock dictionaries containing 'Symbol' and other details.
    """
    if not stocks:
        print("No stocks provided.")
        return

    for instrument_key in get_instrument_key(stocks):
        if instrument_key:
            # print(f"Processing instrument key: {instrument_key}")
            get_stock_change(instrument_key)
    else:
        print("No valid instrument key generated from the provided stocks.")

if __name__ == "__main__":
    with open('mf_stocks.json', 'r') as f:  
        stocks = json.load(f)
    main(stocks)
