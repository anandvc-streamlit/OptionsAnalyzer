import numpy as np
from datetime import datetime

def calculate_annualized_roi(premium, strike_price, days_to_expiry):
    """
    Calculate annualized ROI for options
    """
    try:
        if premium <= 0 or strike_price <= 0 or days_to_expiry <= 0:
            print(f"Invalid input: premium={premium}, strike={strike_price}, days={days_to_expiry}")
            return 0

        # Calculate raw ROI
        roi = (premium / strike_price) * 100

        # Annualize the ROI
        annualized_roi = (roi * 365) / days_to_expiry

        return round(annualized_roi, 2)
    except ZeroDivisionError:
        print("Division by zero error in ROI calculation")
        return 0
    except Exception as e:
        print(f"Error calculating ROI: {str(e)}")
        return 0

def calculate_days_to_expiry(expiry_date):
    """
    Calculate days until option expiration
    """
    try:
        expiry = datetime.strptime(str(expiry_date), '%Y-%m-%d')
        days = (expiry - datetime.now()).days
        return max(days, 0)
    except Exception as e:
        print(f"Error calculating days to expiry: {str(e)}")
        return 0

def process_options_data(options_chain, option_type):
    """
    Process options chain data and calculate ROI
    """
    if options_chain is None or options_chain.empty:
        print("No options chain data to process")
        return []

    results = []

    for _, row in options_chain.iterrows():
        try:
            days_to_expiry = calculate_days_to_expiry(str(row.name))
            if days_to_expiry == 0:
                continue

            # Use last price if available, otherwise use the ask price
            premium = row['lastPrice'] if row['lastPrice'] > 0 else row['ask']

            if premium <= 0:
                continue

            roi = calculate_annualized_roi(
                premium=premium,
                strike_price=row['strike'],
                days_to_expiry=days_to_expiry
            )

            if roi > 0:  # Only include valid ROI calculations
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

        except Exception as e:
            print(f"Error processing row: {str(e)}")
            continue

    return results