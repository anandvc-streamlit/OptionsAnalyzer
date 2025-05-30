import yfinance as yf
import pandas as pd
import streamlit as st
import re
from datetime import datetime
import time

# Initialize global variables to store error details
last_error_message = ""
last_error_details = ""

def get_stock_info(ticker_symbol, max_retries=5, initial_delay=10, status_placeholder=None):
    """
    Fetch basic stock information with improved error handling and retry logic
    """
    global last_error_message, last_error_details
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:  # Don't sleep on first attempt
                wait_time = initial_delay * (2 ** attempt)  # Exponential backoff starting from initial_delay
                print(f"Rate limited. Waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}...")
                
                # Update status message if placeholder is provided
                if status_placeholder:
                    with status_placeholder.container():
                        st.warning(f"Yahoo Finance API rate limit error. Retry {attempt + 1}/{max_retries} in {wait_time} seconds...")
                        
                        # Show actual error message if available
                        if last_error_message:
                            st.error(last_error_message)
                        
                        # Show detailed error info if available
                        if last_error_details:
                            with st.expander("Error Details"):
                                st.code(last_error_details, language="text")
                        
                        # Calculate progress as a value between 0.0 and 1.0
                        progress = min(0.99, attempt / max_retries)
                        st.progress(progress)
                
                time.sleep(wait_time)

            stock = yf.Ticker(ticker_symbol)
            info = stock.info

            # Add error checking for missing data
            if not info:
                error_msg = f"No information found for ticker {ticker_symbol}"
                print(error_msg)
                return {"error": error_msg, "details": f"The ticker '{ticker_symbol}' could not be found or returned no data."}

            # Get current price with fallbacks
            current_price = None
            price_sources = ['regularMarketPrice', 'currentPrice', 'previousClose']

            for source in price_sources:
                current_price = info.get(source)
                if current_price:
                    print(f"Found price from source: {source}")
                    break

            if not current_price:
                error_msg = f"Warning: Could not fetch price for {ticker_symbol}"
                print(error_msg)
                return {"error": error_msg, "details": "Price data is not available for this ticker symbol."}

            return {
                'name': info.get('longName', 'N/A'),
                'current_price': current_price,
                'currency': info.get('currency', 'USD'),
                'market_cap': info.get('marketCap', 0),
            }
        except Exception as e:
            error_str = str(e)
            
            # Store the error details for display during retries
            last_error_message = f"Yahoo Finance API Error: {error_str[:100]}..."
            last_error_details = error_str
            
            # Check if it's a rate limiting error
            if "Too Many Requests" in error_str or "429" in error_str:
                # Extract HTTP status code if present
                http_code = "Unknown"
                if "status" in error_str:
                    try:
                        code_match = re.search(r'status ([0-9]+)', error_str)
                        if code_match:
                            http_code = code_match.group(1)
                    except:
                        pass
                
                if attempt == max_retries - 1:  # Last attempt
                    return {
                        "error": f"We're experiencing high traffic (HTTP {http_code}). Please try again in a few minutes.",
                        "details": f"Error: {error_str}\n\nYahoo Finance is rate limiting our requests."
                    }
                continue
            print(f"Error fetching stock info: {error_str}")
            return {"error": f"Failed to retrieve stock data for {ticker_symbol}", "details": error_str}
    return {"error": "Maximum retries exceeded", "details": "Failed to fetch stock data after multiple attempts due to persistent errors."}

def get_options_chain(ticker_symbol, option_type='both', max_retries=5, initial_delay=10, status_placeholder=None):
    """
    Fetch options chain data with improved error handling and retry logic
    """
    global last_error_message, last_error_details
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:  # Don't sleep on first attempt
                wait_time = initial_delay * (2 ** attempt)  # Exponential backoff starting from initial_delay
                print(f"Rate limited. Waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}...")
                
                # Update status message if placeholder is provided
                if status_placeholder:
                    with status_placeholder.container():
                        st.warning(f"Yahoo Finance API rate limit error. Retry {attempt + 1}/{max_retries} in {wait_time} seconds...")
                        
                        # Show actual error message if available
                        if last_error_message:
                            st.error(last_error_message)
                        
                        # Show detailed error info if available
                        if last_error_details:
                            with st.expander("Error Details"):
                                st.code(last_error_details, language="text")
                        
                        # Calculate progress as a value between 0.0 and 1.0
                        progress = min(0.99, attempt / max_retries)
                        st.progress(progress)
                
                time.sleep(wait_time)

            stock = yf.Ticker(ticker_symbol)
            expirations = stock.options

            if not expirations:
                error_msg = f"No options expirations found for {ticker_symbol}"
                print(error_msg)
                return {"error": error_msg, "details": "No options data available for this ticker symbol."}

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
                error_msg = "No valid options data found"
                print(error_msg)
                return {"error": error_msg, "details": f"Could not retrieve any valid options data for {ticker_symbol}."}

            combined_options = pd.concat(all_options)
            combined_options = combined_options.dropna(subset=['strike', 'lastPrice', 'bid', 'ask'])

            if combined_options.empty:
                error_msg = "No valid options data after filtering"
                print(error_msg)
                return {"error": error_msg, "details": "Data was retrieved but contained no valid options after filtering."}

            print(f"Successfully processed {len(combined_options)} options contracts")
            return combined_options

        except Exception as e:
            error_str = str(e)
            
            # Store the error details for display during retries
            last_error_message = f"Yahoo Finance API Error: {error_str[:100]}..."
            last_error_details = error_str
            
            # Check if it's a rate limiting error
            if "Too Many Requests" in error_str or "429" in error_str:
                # Extract HTTP status code if present
                http_code = "Unknown"
                if "status" in error_str:
                    try:
                        code_match = re.search(r'status ([0-9]+)', error_str)
                        if code_match:
                            http_code = code_match.group(1)
                    except:
                        pass
                
                if attempt == max_retries - 1:  # Last attempt
                    error_msg = f"Rate limit reached for options data (HTTP {http_code})"
                    print(error_msg)
                    return {
                        "error": f"Data retrieval rate limit exceeded (HTTP {http_code})", 
                        "details": f"Error: {error_str}\n\nThe Yahoo Finance API is limiting our requests. Please try again in a few minutes."
                    }
                continue
            error_msg = f"Error in get_options_chain: {error_str}"
            print(error_msg)
            return {"error": "Failed to retrieve options data", "details": error_str}
    return {"error": "Maximum retries exceeded", "details": "Failed to fetch options data after multiple attempts."}