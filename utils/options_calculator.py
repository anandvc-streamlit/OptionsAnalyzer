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
        # Convert expiry_date to string if it's not already
        expiry_str = str(expiry_date)
        print(f"Processing expiry date: {expiry_str}")

        # Try to parse the date
        expiry = datetime.strptime(expiry_str, '%Y-%m-%d')
        days = (expiry - datetime.now()).days
        return max(days, 0)
    except Exception as e:
        print(f"Error calculating days to expiry: {str(e)}")
        return 0

def process_options_data(options_chain, current_stock_price):
    """
    Process options chain data and calculate ROI, filtering out strategically irrelevant options
    """
    if options_chain is None or options_chain.empty:
        print("No options chain data to process")
        return []

    results = []

    for _, row in options_chain.iterrows():
        try:
            # Skip PUT options above current price and CALL options below current price
            if (row['optionType'] == 'PUT' and row['strike'] > current_stock_price) or \
               (row['optionType'] == 'CALL' and row['strike'] < current_stock_price):
                continue

            days_to_expiry = calculate_days_to_expiry(row['expirationDate'])
            if days_to_expiry == 0:
                continue

            # Get the bid and ask prices
            bid_price = row['bid']
            ask_price = row['ask']

            if bid_price <= 0 or ask_price <= 0:
                continue

            # Use the lower of Bid and Ask as the Market Premium
            premium = min(bid_price, ask_price)

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
                    'Expiry Date': row['expirationDate'],
                    'Premium': premium,
                    'Bid': bid_price,
                    'Ask': ask_price,
                    'Days to Expiry': days_to_expiry,
                    'Volume': row['volume'],
                    'Open Interest': row['openInterest'],
                    'Implied Volatility': round(row['impliedVolatility'] * 100, 2),
                    'Annualized ROI (%)': roi,
                    'Option Type': row['optionType']
                })

        except Exception as e:
            print(f"Error processing row: {str(e)}")
            continue

    print(f"Processed {len(results)} valid options")
    return results