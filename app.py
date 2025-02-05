import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_fetcher import get_stock_info, get_options_chain
from utils.options_calculator import process_options_data

# Page configuration
st.set_page_config(
    page_title="Options ROI Calculator",
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
</style>
""", unsafe_allow_html=True)

# Header
st.title("📈 Options Trading ROI Calculator")
st.markdown("""
This calculator helps you analyze the potential returns from options trading strategies.
Enter a stock ticker to get started!

_Data is sourced from Yahoo Finance and updates regularly during market hours (slight delay may occur)._
""")

# Sidebar
with st.sidebar:
    st.header("Settings")
    ticker = st.text_input("Enter Stock Ticker", value="AAPL").upper()
    option_type = st.selectbox(
        "Option Type",
        ["both", "call", "put"],
        format_func=lambda x: x.upper()
    )
    
    st.markdown("---")
    st.markdown("""
    ### How it works
    1. Enter a stock ticker
    2. Select option type
    3. View ROI calculations
    4. Compare different strikes and dates
    """)

# Main content
if ticker:
    with st.spinner('Fetching stock information...'):
        stock_info = get_stock_info(ticker)
        
    if stock_info:
        # Stock information
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Stock Price", f"${stock_info['current_price']:.2f}")
        with col2:
            st.metric("Company", stock_info['name'])
        with col3:
            st.metric("Market Cap", f"${stock_info['market_cap']:,.0f}")
            
        # Fetch options data
        with st.spinner('Calculating options ROI...'):
            options_data = get_options_chain(ticker, option_type)
            
        if options_data is not None:
            # Process options data
            results = process_options_data(options_data, option_type)
            
            if results:
                # Convert results to DataFrame
                df = pd.DataFrame(results)
                
                # Filters
                col1, col2 = st.columns(2)
                with col1:
                    min_volume = st.number_input("Minimum Volume", value=0, min_value=0)
                with col2:
                    min_open_interest = st.number_input("Minimum Open Interest", value=0, min_value=0)
                
                # Filter data
                filtered_df = df[
                    (df['Volume'] >= min_volume) &
                    (df['Open Interest'] >= min_open_interest)
                ]
                
                # Display results
                st.subheader("Options ROI Analysis")
                
                if not filtered_df.empty:
                    # ROI Chart
                    fig = px.scatter(
                        filtered_df,
                        x='Strike Price',
                        y='Annualized ROI (%)',
                        size='Open Interest',
                        color='Days to Expiry',
                        hover_data=['Expiry Date', 'Premium', 'Implied Volatility'],
                        title='ROI vs Strike Price'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Detailed data table
                    st.markdown("### Options Data Table")
                    st.markdown("Click on column headers to sort the data.")
                    
                    # Format the columns for better display
                    formatted_df = filtered_df.copy()
                    formatted_df['Strike Price'] = formatted_df['Strike Price'].map('${:,.2f}'.format)
                    formatted_df['Premium'] = formatted_df['Premium'].map('${:,.2f}'.format)
                    formatted_df['Annualized ROI (%)'] = formatted_df['Annualized ROI (%)'].map('{:,.2f}%'.format)
                    formatted_df['Implied Volatility'] = formatted_df['Implied Volatility'].map('{:,.2f}%'.format)
                    
                    # Display sortable dataframe
                    st.dataframe(
                        formatted_df.sort_values('Annualized ROI (%)', ascending=False),
                        use_container_width=True,
                        column_order=formatted_df.columns.tolist(),
                        hide_index=True
                    )
                else:
                    st.warning("No options data matching the selected filters.")
            else:
                st.error("No valid options data available for processing.")
        else:
            st.error("Failed to fetch options data. Please check the ticker symbol.")
    else:
        st.error("Failed to fetch stock information. Please check the ticker symbol.")