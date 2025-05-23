print("Streamlit app is starting up...")

try:
    import streamlit as st
    import pandas as pd
    import plotly.express as px
    from utils.data_fetcher import get_stock_info, get_options_chain
    from utils.options_calculator import process_options_data
except Exception as e:
    print("Import error:", e)
    raise

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
    .loading-text {
        color: #0031b3;
        font-size: 1.2em;
        margin-bottom: 1rem;
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

# Main input controls
col1, col2 = st.columns([2, 2])
with col1:
    ticker = st.text_input("Enter Stock Ticker", value="AAPL").upper()
with col2:
    option_type = st.selectbox(
        "Option Type",
        ["both", "call", "put"],
        format_func=lambda x: x.upper()
    )

# Sidebar with instructions
with st.sidebar:
    st.markdown("### How it works")
    st.markdown("""
    1. Enter a stock ticker
    2. Select option type
    3. View ROI calculations
    4. Compare different strikes and dates

    #### Rate Limits
    To ensure stable data retrieval:
    - Wait a few seconds between searches
    - Try different tickers if one is rate limited
    - Refresh the page if needed
    """)

# Main content
if ticker:
    # Create placeholder for status messages
    status_placeholder = st.empty()

    # Display initial loading message
    with status_placeholder.container():
        st.write('Fetching market data... This may take a few moments.')
        progress_bar = st.progress(0)

    # Pass the status placeholder to the function
    stock_info = get_stock_info(ticker, status_placeholder=status_placeholder)

    # Clear the placeholder after data fetching is complete
    status_placeholder.empty()

    if stock_info:
        if isinstance(stock_info, dict) and "error" in stock_info:
            st.error(stock_info["error"])

            # Display technical details in an expandable section if available
            if "details" in stock_info:
                with st.expander("Show Technical Details"):
                    st.code(stock_info["details"], language="text")

            st.info("While waiting, you can try searching for a different stock symbol or review the tips in the sidebar.")
        else:
            # Stock information
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Stock Price", f"${stock_info['current_price']:.2f}")
            with col2:
                st.metric("Company", stock_info['name'])
            with col3:
                st.metric("Market Cap", f"${stock_info['market_cap']:,.0f}")

            # Fetch options data
            # Create placeholder for options status messages
            options_status_placeholder = st.empty()

            # Display initial loading message
            with options_status_placeholder.container():
                st.write('Calculating options ROI... Please wait.')
                options_progress_bar = st.progress(0)

            # Pass the status placeholder to the function
            options_data = get_options_chain(ticker, option_type, status_placeholder=options_status_placeholder)

            # Clear the placeholder after data fetching is complete
            options_status_placeholder.empty()

            if isinstance(options_data, dict) and "error" in options_data:
                # Display main error message
                st.error(options_data["error"])

                # Display technical details in an expandable section
                if "details" in options_data:
                    with st.expander("Show Technical Details"):
                        st.code(options_data["details"], language="text")

                st.info("💡 Tip: While waiting, you can try searching for a different stock symbol or review the tips in the sidebar.")
            elif options_data is not None:
                # Process options data
                results = process_options_data(options_data, stock_info['current_price'])

                if results:
                    # Convert results to DataFrame
                    df = pd.DataFrame(results)

                    # Filters section
                    st.subheader("Filter Options")

                    # Create columns for filters
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        min_strike = st.number_input("Min Strike Price",
                                                   value=float(df['Strike Price'].min()),
                                                   step=1.0)
                        max_strike = st.number_input("Max Strike Price",
                                                   value=float(df['Strike Price'].max()),
                                                   step=1.0)
                        min_volume = st.number_input("Min Volume",
                                                   value=5,
                                                   step=1)

                    with col2:
                        min_days = st.number_input("Min Days to Expiry",
                                                 value=0,
                                                 step=1)
                        max_days = st.number_input("Max Days to Expiry",
                                                 value=int(df['Days to Expiry'].max()),
                                                 step=1)
                        min_open_interest = st.number_input("Min Open Interest",
                                                          value=5,
                                                          step=1)

                    with col3:
                        min_premium = st.number_input("Min Premium",
                                                    value=float(df['Premium'].min()),
                                                    step=0.01)
                        min_roi = st.number_input("Min Annualized ROI (%)",
                                                value=float(df['Annualized ROI (%)'].min()),
                                                step=1.0)
                        min_iv = st.number_input("Min Implied Volatility (%)",
                                               value=float(df['Implied Volatility'].min()),
                                               step=1.0)

                    # Apply filters
                    filtered_df = df[
                        (df['Strike Price'] >= min_strike) &
                        (df['Strike Price'] <= max_strike) &
                        (df['Premium'] >= min_premium) &
                        (df['Volume'] >= min_volume) &
                        (df['Open Interest'] >= min_open_interest) &
                        (df['Annualized ROI (%)'] >= min_roi) &
                        (df['Days to Expiry'] >= min_days) &
                        (df['Days to Expiry'] <= max_days) &
                        (df['Implied Volatility'] >= min_iv)
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

                        # Create a copy for display with proper formatting
                        display_df = filtered_df.copy()

                        # Format the display columns
                        display_df['Strike Price'] = display_df['Strike Price'].map('${:,.2f}'.format)
                        display_df['Premium'] = display_df['Premium'].map('${:,.2f}'.format)
                        display_df['Bid'] = display_df['Bid'].map('${:,.2f}'.format)
                        display_df['Ask'] = display_df['Ask'].map('${:,.2f}'.format)
                        display_df['Implied Volatility'] = display_df['Implied Volatility'].map('{:,.2f}%'.format)

                        # Display dataframe with proper column configuration
                        st.dataframe(
                            display_df,
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

                    else:
                        st.warning("No options data matching the selected filters.")
                else:
                    st.error("No valid options data available for processing.")
                    with st.expander("Show Technical Details"):
                        st.code("The options data was retrieved but could not be processed correctly. This might be due to missing or invalid data in the API response.", language="text")
                    st.info("💡 Try a different ticker symbol with more active options trading.")
            else:
                st.error("Failed to fetch options data. Please try again in a few minutes.")
                with st.expander("Show Technical Details"):
                    st.code("The request to Yahoo Finance API did not return any data or returned an invalid response format.", language="text")
                st.info("💡 Tip: While waiting, you can try searching for a different stock symbol or check if the ticker has options available.")
    else:
        st.error("Failed to fetch stock information. Please check the ticker symbol and try again.")
        with st.expander("Show Technical Details"):
            st.code("The request to Yahoo Finance API did not return any data or returned an invalid response format.", language="text")
        st.info("💡 Make sure the ticker symbol is correct and try again in a few moments.")