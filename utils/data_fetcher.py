import yfinance as yf
import pandas as pd

def get_stock_info(ticker_symbol):
    """
    Fetch basic stock information
    """
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
        return {
            'name': info.get('longName', 'N/A'),
            'current_price': info.get('regularMarketPrice', 0),
            'currency': info.get('currency', 'USD'),
            'market_cap': info.get('marketCap', 0),
        }
    except Exception:
        return None

def get_options_chain(ticker_symbol, option_type='both'):
    """
    Fetch options chain data for a given ticker
    """
    try:
        stock = yf.Ticker(ticker_symbol)
        expirations = stock.options
        
        all_options = []
        for date in expirations:
            opt = stock.option_chain(date)
            if option_type in ['call', 'both']:
                calls = opt.calls
                calls['optionType'] = 'CALL'
                all_options.append(calls)
            if option_type in ['put', 'both']:
                puts = opt.puts
                puts['optionType'] = 'PUT'
                all_options.append(puts)
                
        if not all_options:
            return None
            
        return pd.concat(all_options)
    except Exception:
        return None
