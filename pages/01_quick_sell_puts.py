import streamlit as st
import pandas as pd
import plotly.express as px
import time
from utils.data_fetcher import get_stock_info, get_options_chain
from utils.options_calculator import process_options_data

# Page configuration
st.set_page_config(
    page_title="Quick Sell Puts - Options ROI Calculator",
    page_icon="📈",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stAlert {
        padding: 0.5rem;
        margin-bottom: 1rem;
    }
    .dataframe {
        font-size: 12px;
    }
    .stProgress > div > div > div > div {
        background-color: #0031b3;
    }
    .loading-text {
        color: #0031b3;
        font-size: 1.2em;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("📉 Quick Sell Puts")
st.markdown("""
This page displays PUT options data for multiple tickers with preset filters:
- Maximum 51 days to expiry
- Maximum strike price 10% below the current price
- Sorted by Annualized ROI (high to low)

_Data is sourced from Yahoo Finance and updates regularly during market hours (slight delay may occur)._
""")

# List of tickers to analyze
tickers = ["MSTY", "PLTY", "TSLA", "SMCI", "SOFI", "NVDA", "AMZN", "MSFT", 
          "AAPL", "HIMS", "HOOD", "META", "INTC", "OKTA", "AVGO", "GOOG", 
          "T", "O", "LLY", "NFLX", "MSTR"]

# Filters - These will be applied to all tickers
st.sidebar.markdown("### Global Filters")
max_days_filter = st.sidebar.number_input("Max Days to Expiry", value=51, min_value=1, max_value=365, step=1)
below_current_price_percent = st.sidebar.slider("Max Strike Price (% below current)", value=10.0, min_value=1.0, max_value=30.0, step=0.5)
min_open_interest = st.sidebar.number_input("Min Open Interest", value=5, min_value=1, step=1)
min_volume = st.sidebar.number_input("Min Volume", value=5, min_value=1, step=1)
min_premium = st.sidebar.number_input("Min Premium ($)", value=0.05, min_value=0.01, step=0.01, format="%.2f")

# Sidebar with instructions
with st.sidebar:
    st.markdown("### How it works")
    st.markdown("""
    1. Adjust global filters in the sidebar
    2. Data is automatically filtered by:
       - PUT options only
       - Strike price below current price
       - Max days to expiry (preset: 51 days)
    3. Tables are sorted by Annualized ROI (high to low)
    
    #### Rate Limits
    To ensure stable data retrieval:
    - Data is cached for 15 minutes
    - If rate limited, tickers will retry with backoff
    """)

# Function to process a ticker and return formatted dataframe
def process_ticker(ticker):
    with st.spinner(f'Fetching data for {ticker}...'):
        # Get stock info
        stock_info = get_stock_info(ticker)
        
        if not stock_info or "error" in stock_info:
            if stock_info and "error" in stock_info:
                return ticker, None, stock_info["error"]
            else:
                return ticker, None, f"Failed to fetch stock information for {ticker}"
        
        current_price = stock_info['current_price']
        company_name = stock_info['name']
        
        # Calculate max strike price (10% below current price)
        max_strike = current_price * (1 - below_current_price_percent/100)
        
        # Fetch options data (PUT options only)
        options_data = get_options_chain(ticker, option_type='put')
        
        if options_data is None:
            return ticker, None, f"No options data available for {ticker}"
        
        # Process options data
        results = process_options_data(options_data, current_price)
        
        if not results:
            return ticker, None, f"No valid options data for {ticker}"
        
        # Convert results to DataFrame
        df = pd.DataFrame(results)
        
        # Apply filters
        filtered_df = df[
            (df['Strike Price'] <= max_strike) &
            (df['Days to Expiry'] <= max_days_filter) &
            (df['Premium'] >= min_premium) &
            (df['Volume'] >= min_volume) &
            (df['Open Interest'] >= min_open_interest)
        ]
        
        # Sort by Annualized ROI (high to low)
        filtered_df = filtered_df.sort_values(by='Annualized ROI (%)', ascending=False)
        
        # Create a copy for display with proper formatting
        if not filtered_df.empty:
            display_df = filtered_df.copy()
            
            # Format the display columns
            display_df['Strike Price'] = display_df['Strike Price'].map('${:,.2f}'.format)
            display_df['Premium'] = display_df['Premium'].map('${:,.2f}'.format)
            display_df['Bid'] = display_df['Bid'].map('${:,.2f}'.format)
            display_df['Ask'] = display_df['Ask'].map('${:,.2f}'.format)
            display_df['Implied Volatility'] = display_df['Implied Volatility'].map('{:,.2f}%'.format)
            
            return ticker, {
                'display_df': display_df,
                'filtered_df': filtered_df,
                'current_price': current_price,
                'company_name': company_name
            }, None
        else:
            return ticker, None, f"No options matching filters for {ticker}"

# Process all tickers
for ticker in tickers:
    ticker_container = st.container()
    with ticker_container:
        st.subheader(f"{ticker}")
        
        # Use caching to avoid rate limits
        @st.cache_data(ttl=900)  # Cache for 15 minutes
        def cached_process_ticker(ticker):
            return process_ticker(ticker)
        
        ticker, data, error = cached_process_ticker(ticker)
        
        if error:
            st.error(error)
            continue
        
        # Display stock info
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Stock Price", f"${data['current_price']:.2f}")
        with col2:
            st.metric("Company", data['company_name'])
        
        # Display the filtered dataframe
        st.dataframe(
            data['display_df'],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Annualized ROI (%)": st.column_config.NumberColumn(
                    "Annualized ROI (%)",
                    format="%.2f%%",
                ),
                "Strike Price": st.column_config.TextColumn(
                    "Strike Price",
                    help="Option strike price"
                ),
                "Premium": st.column_config.TextColumn(
                    "Market Premium",
                    help="Lower of Bid and Ask prices"
                ),
                "Bid": st.column_config.TextColumn(
                    "Bid",
                    help="Bid price"
                ),
                "Ask": st.column_config.TextColumn(
                    "Ask",
                    help="Ask price"
                ),
                "Implied Volatility": st.column_config.TextColumn(
                    "Implied Volatility",
                    help="Option implied volatility"
                )
            }
        )
        st.divider()
