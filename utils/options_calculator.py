import numpy as np
from datetime import datetime

def calculate_annualized_roi(premium, strike_price, days_to_expiry):
    """
    Calculate annualized ROI for options
    """
    try:
        # Calculate raw ROI
        roi = (premium / strike_price) * 100
        
        # Annualize the ROI
        annualized_roi = (roi * 365) / days_to_expiry
        
        return round(annualized_roi, 2)
    except ZeroDivisionError:
        return 0
    except Exception:
        return None

def calculate_days_to_expiry(expiry_date):
    """
    Calculate days until option expiration
    """
    try:
        expiry = datetime.strptime(expiry_date, '%Y-%m-%d')
        days = (expiry - datetime.now()).days
        return max(days, 0)
    except Exception:
        return 0

def process_options_data(options_chain, option_type):
    """
    Process options chain data and calculate ROI
    """
    results = []
    
    for _, row in options_chain.iterrows():
        days_to_expiry = calculate_days_to_expiry(str(row.name))
        if days_to_expiry == 0:
            continue
            
        premium = row['lastPrice'] if row['lastPrice'] > 0 else row['ask']
        
        roi = calculate_annualized_roi(
            premium=premium,
            strike_price=row['strike'],
            days_to_expiry=days_to_expiry
        )
        
        results.append({
            'Strike Price': row['strike'],
            'Expiry Date': row.name,
            'Premium': premium,
            'Days to Expiry': days_to_expiry,
            'Volume': row['volume'],
            'Open Interest': row['openInterest'],
            'Implied Volatility': round(row['impliedVolatility'] * 100, 2),
            'Annualized ROI (%)': roi
        })
    
    return results
