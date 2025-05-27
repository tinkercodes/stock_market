from upstox_client import UpstoxClient, InstrumentKey
from upstox_client.models import *
from upstox_client.api import market_quote_api
from upstox_client.websockets import LiveFeedType, Quote, WebSocketClient

import time

# 1. Set your API credentials and access token
api_key = 'your_api_key'
access_token = 'your_access_token'

# 2. Configure client
configuration = upstox_client.Configuration()
configuration.access_token = access_token

api_client = upstox_client.ApiClient(configuration)
market_api = market_quote_api.MarketQuoteApi(api_client)

# 3. Use WebSocket for live price
def on_quote_update(quote: Quote):
    print(f"Symbol: {quote.instrument_key}, LTP: {quote.last_traded_price}")

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, code, reason):
    print(f"WebSocket closed: {code}, {reason}")

def on_open(ws):
    print("WebSocket connection opened.")
    # 4. NSE_EQ | HDFCBANK
    instrument_key = InstrumentKey(exchange='NSE_EQ', token='1333')  # 1333 is the token for HDFCBANK
    ws.subscribe([instrument_key], LiveFeedType.LTP)

# 5. Create and connect WebSocket
ws_client = WebSocketClient(api_key=api_key, access_token=access_token)

ws_client.on_quote_update = on_quote_update
ws_client.on_error = on_error
ws_client.on_close = on_close
ws_client.on_open = on_open

# 6. Start WebSocket
ws_client.connect()

# Keep the script running
while True:
    time.sleep(1)
