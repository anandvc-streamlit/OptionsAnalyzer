import yfinance as yf
import pandas as pd
from datetime import datetime
import time

def get_stock_info(ticker_symbol, max_retries=3):
    """
    Fetch basic stock information with improved error handling and retry logic
    """
    for attempt in range(max_retries):
        try:
            stock = yf.Ticker(ticker_symbol)
            info = stock.info

            # Add error checking for missing data
            if not info:
                print(f"No information found for ticker {ticker_symbol}")
                return None

            # Get current price with fallbacks
            current_price = None
            price_sources = ['regularMarketPrice', 'currentPrice', 'previousClose']

            for source in price_sources:
                current_price = info.get(source)
                if current_price:
                    print(f"Found price from source: {source}")
                    break

            if not current_price:
                print(f"Warning: Could not fetch price for {ticker_symbol}")
                return None

            return {
                'name': info.get('longName', 'N/A'),
                'current_price': current_price,
                'currency': info.get('currency', 'USD'),
                'market_cap': info.get('marketCap', 0),
            }
        except Exception as e:
            if "Too Many Requests" in str(e):
                if attempt < max_retries - 1:  # Don't sleep on last attempt
                    wait_time = (attempt + 1) * 2  # Exponential backoff
                    print(f"Rate limited. Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    continue
            print(f"Error fetching stock info: {str(e)}")
            if "Too Many Requests" in str(e):
                return {"error": "Rate limited by Yahoo Finance. Please try again in a few minutes."}
            return None
    return None

def get_options_chain(ticker_symbol, option_type='both', max_retries=3):
    """
    Fetch options chain data with improved error handling and retry logic
    """
    for attempt in range(max_retries):
        try:
            stock = yf.Ticker(ticker_symbol)
            expirations = stock.options

            if not expirations:
                print(f"No options expirations found for {ticker_symbol}")
                return None

            print(f"Found {len(expirations)} expiration dates for {ticker_symbol}")

            all_options = []
            for date in expirations:
                try:
                    opt = stock.option_chain(date)

                    if option_type in ['call', 'both']:
                        calls = opt.calls
                        calls['optionType'] = 'CALL'
                        calls['expirationDate'] = date
                        calls = calls[calls['lastPrice'] > 0]
                        all_options.append(calls)

                    if option_type in ['put', 'both']:
                        puts = opt.puts
                        puts['optionType'] = 'PUT'
                        puts['expirationDate'] = date
                        puts = puts[puts['lastPrice'] > 0]
                        all_options.append(puts)

                except Exception as e:
                    print(f"Error processing options for date {date}: {str(e)}")
                    continue

            if not all_options:
                print("No valid options data found")
                return None

            combined_options = pd.concat(all_options)
            combined_options = combined_options.dropna(subset=['strike', 'lastPrice', 'bid', 'ask'])

            if combined_options.empty:
                print("No valid options data after filtering")
                return None

            print(f"Successfully processed {len(combined_options)} options contracts")
            return combined_options

        except Exception as e:
            if "Too Many Requests" in str(e):
                if attempt < max_retries - 1:  # Don't sleep on last attempt
                    wait_time = (attempt + 1) * 2  # Exponential backoff
                    print(f"Rate limited. Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    continue
            print(f"Error in get_options_chain: {str(e)}")
            return None
    return None