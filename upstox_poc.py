from __future__ import print_function
import time
import upstox_client
from upstox_client.rest import ApiException
from pprint import pprint
import os
from dotenv import load_dotenv
load_dotenv()

# Configure OAuth2 access token for authorization: OAUTH2
configuration = upstox_client.Configuration()
configuration.access_token = os.getenv("UPSTOX_ACCESS_TOKEN")
# print(f"Access Token: {configuration.access_token}")
if not configuration.access_token:
    raise ValueError("UPSTOX_ACCESS_TOKEN not found in environment variables.")
# create an instance of the API class
api_instance = upstox_client.MarketQuoteV3Api(upstox_client.ApiClient(configuration))
instrument_key = 'NSE_EQ|INE040A01034' # str | Comma separated list of instrument keys (optional)


interval = '1d' # str | Interval to get ohlc data
instrument_key = 'NSE_EQ|INE040A01034' # str | Comma separated list of instrument keys (optional)

try:
    # Market quotes and instruments - OHLC quotes
    api_response = api_instance.get_market_quote_ohlc(interval, instrument_key=instrument_key)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MarketQuoteV3Api->get_market_quote_ohlc: %s\n" % e)


# try:
#     # Market quotes and instruments - LTP quotes.
#     api_response = api_instance.get_ltp(instrument_key=instrument_key)
#     pprint(api_response)
# except ApiException as e:
#     print("Exception when calling MarketQuoteV3Api->get_ltp: %s\n" % e)