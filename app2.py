# Set page config (must be the first Streamlit command)
import streamlit as st
st.set_page_config(
    page_title="Smart Investment Advisor",
    page_icon="📈",
    layout="wide"
)

# Import other libraries
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from prophet import Prophet
from datetime import datetime, timedelta
import requests
from firebase_admin import auth, credentials, initialize_app, get_app
import os

# Define your Finnhub API key here
FINNHUB_API_KEY = "cvl4t91r01qs0ops3avgcvl4t91r01qs0ops3b00"  # Replace with your actual API key

# Initialize Firebase Admin SDK
try:
    app = get_app()
except ValueError:
    # Replace "firebase_config.json" with the actual name of your Firebase Admin SDK JSON file
    cred = credentials.Certificate("firebase_config.json")  
    initialize_app(cred)

# Remove the login page and routing logic
# Commented out the login_page() function and its usage
# def login_page():
#     st.title("Login to Smart Investment Advisor")
#     st.markdown("Please choose a login method below.")
#     # Tabs for Email and Admin Login
#     tab1, tab2 = st.tabs(["Email Login", "Admin Login"])
#     # Email Login
#     with tab1:
#         st.subheader("Login with Email")
#         email = st.text_input("Email", placeholder="Enter your email")
#         password = st.text_input("Password", placeholder="Enter your password", type="password")
#         if st.button("Login with Email"):
#             if email and password:
#                 try:
#                     user = auth.get_user_by_email(email)
#                     st.success(f"Welcome, {user.email}!")
#                     st.session_state["user"] = user.email  # Store user in session state
#                     st.experimental_rerun()  # Redirect to the home page
#                 except Exception as e:
#                     st.error(f"Login failed: {str(e)}")
#             else:
#                 st.warning("Please enter both email and password.")
#     # Admin Login
#     with tab2:
#         st.subheader("Admin Login")
#         admin_email = st.text_input("Admin Email", placeholder="Enter your admin email")
#         admin_password = st.text_input("Admin Password", placeholder="Enter your admin password", type="password")
#         ADMIN_EMAIL = "somak.paul.fiem.cse23@teamfuture.in"  # Replace with your admin email
#         ADMIN_PASSWORD = "admin@123"  # Replace with your admin password
#         if st.button("Login as Admin"):
#             if admin_email and admin_password:
#                 if admin_email == ADMIN_EMAIL and admin_password == ADMIN_PASSWORD:
#                     st.success("Welcome, Admin!")
#                     st.session_state["admin"] = True  # Store admin session
#                     st.experimental_rerun()  # Redirect to admin dashboard
#                 else:
#                     st.error("Invalid admin email or password.")
#             else:
#                 st.warning("Please enter both email and password.")

# Directly load the main app content
st.title("📈 Smart Investment Advisor")
st.markdown("""
This app fetches stock price data and makes predictions using Facebook Prophet.
Search for a stock symbol or enter a valid stock symbol (e.g., AAPL, GOOGL, MSFT) to get started.
""")

# The rest of your app logic (e.g., stock analysis, predictions, etc.)
# Example: Fetch stock data
def fetch_stock_data(symbol, period='5y'):
    """Fetch stock data using yfinance"""
    try:
        stock = yf.Ticker(symbol)
        # Validate if the stock symbol exists
        if not stock.info or 'regularMarketPrice' not in stock.info:
            st.error(f"Invalid stock symbol: {symbol}. Please check the symbol and try again.")
            return None
        
        # Fetch historical data
        data = stock.history(period=period)
        if data is None or data.empty:
            st.error(f"No historical data found for symbol: {symbol}. Please try another symbol.")
            return None
        
        return data
    except Exception as e:
        st.error(f"Error fetching data for symbol {symbol}: {str(e)}")
        return None

def prepare_data_for_prophet(data):
    """Prepare data for Prophet model"""
    df = data.reset_index()[['Date', 'Close']]
    df.columns = ['ds', 'y']
    # Remove timezone information from datetime column
    df['ds'] = df['ds'].dt.tz_localize(None)
    return df

def make_prediction(data, periods=30):
    """Make predictions using Prophet"""
    model = Prophet(
        daily_seasonality=True,
        yearly_seasonality=True,
        weekly_seasonality=True,
        changepoint_prior_scale=0.05
    )
    model.fit(data)
    future_dates = model.make_future_dataframe(periods=periods)
    forecast = model.predict(future_dates)
    return forecast

def plot_stock_data(data, symbol):
    """Create stock price chart using plotly"""
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Market Data'
    ))
    fig.update_layout(
        title=f'{symbol} Stock Price',
        yaxis_title='Stock Price (USD)',
        xaxis_title='Date',
        template='plotly_dark'
    )
    return fig

def plot_prediction(forecast, data):
    """Plot the prediction results"""
    fig = go.Figure()
    
    # Historical data
    fig.add_trace(go.Scatter(
        x=data['ds'],
        y=data['y'],
        name='Historical',
        line=dict(color='blue')
    ))
    
    # Predicted values
    fig.add_trace(go.Scatter(
        x=forecast['ds'],
        y=forecast['yhat'],
        name='Predicted',
        line=dict(color='red')
    ))
    
    # Confidence interval
    fig.add_trace(go.Scatter(
        x=pd.concat([forecast['ds'], forecast['ds'][::-1]]),
        y=pd.concat([forecast['yhat_upper'], forecast['yhat_lower'][::-1]]),
        fill='toself',
        fillcolor='rgba(0,100,80,0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Confidence Interval'
    ))
    
    fig.update_layout(
        title='Stock Price Prediction',
        yaxis_title='Stock Price (USD)',
        xaxis_title='Date',
        template='plotly_dark',
        showlegend=True
    )
    return fig

def search_stock_symbols(query):
    """Search for stock symbols using Finnhub API"""
    try:
        url = f"https://finnhub.io/api/v1/search"
        params = {
            "q": query,
            "token": FINNHUB_API_KEY
        }
        response = requests.get(url, params=params)
        data = response.json()
        
        # Check if the API returned results
        if "result" in data and data["result"]:
            # Filter out symbols that are not compatible with Yahoo Finance
            results = []
            for item in data["result"]:
                if ":" not in item["symbol"]:  # Exclude symbols with ':'
                    # Add beginner-friendly notes for stock markets
                    market_note = " - NASDAQ"  # Default to NASDAQ
                    if ".BSE" in item["symbol"]:
                        market_note = " - Bombay Stock Exchange"
                    elif ".NS" in item["symbol"]:
                        market_note = " - National Stock Exchange"
                    elif ".L" in item["symbol"]:
                        market_note = " - London Stock Exchange"
                    elif ".T" in item["symbol"]:
                        market_note = " - Tokyo Stock Exchange"
                    elif ".SS" in item["symbol"]:
                        market_note = " - Shanghai Stock Exchange"
                    elif ".HK" in item["symbol"]:
                        market_note = " - Hong Kong Stock Exchange"
                    
                    # Append the market note to the company name
                    results.append({
                        "symbol": item["symbol"],
                        "name": f"{item['description']}{market_note}"
                    })
            return results
        else:
            return []
    except Exception as e:
        st.error(f"Error searching for stock symbols: {str(e)}")
        return []

# Validate stock symbols using yfinance
def validate_stock_symbol(symbol):
    """Check if the stock symbol is valid using yfinance."""
    try:
        stock = yf.Ticker(symbol)
        # Check if the stock has valid information
        if stock.info and 'regularMarketPrice' in stock.info:
            return True
        return False
    except Exception:
        return False

# Main app layout
col1, col2 = st.columns([1, 2])

# List of supported stock markets
stock_markets = {
    "Default (No Market)": "",
    "Bombay Stock Exchange (BSE)": ".BSE",
    "National Stock Exchange (NSE)": ".NS",
    "London Stock Exchange (LSE)": ".L",
    "NASDAQ": "",
    "New York Stock Exchange (NYSE)": "",
    "Tokyo Stock Exchange (TSE)": ".T",
    "Shanghai Stock Exchange (SSE)": ".SS",
    "Hong Kong Stock Exchange (HKEX)": ".HK"
}

with col1:
    # Search bar for company names
    search_query = st.text_input("Search for a Company Name (e.g., Reliance, TCS):", value="")
    suggestions = []
    if search_query:
        with st.spinner('Searching for companies...'):
            suggestions = search_stock_symbols(search_query)
    
    # Filter valid symbols
    valid_suggestions = [
        item for item in suggestions if validate_stock_symbol(item["symbol"])
    ]
    
    # Dropdown for company names
    selected_symbol = None
    if valid_suggestions:
        # Use session state to persist the selected value
        if "selected_option" not in st.session_state:
            st.session_state.selected_option = None

        selected_option = st.selectbox(
            "Select a Company:",
            [f"{item['name']} ({item['symbol']})" for item in valid_suggestions],
            key="company_dropdown",
            index=0 if st.session_state.selected_option is None else
            [f"{item['name']} ({item['symbol']}" for item in valid_suggestions].index(st.session_state.selected_option)
        )
        # Extract the stock symbol from the selected option
        selected_symbol = selected_option.split("(")[-1].strip(")")
    else:
        st.warning("No valid companies found. Please try a different search query.")
    
    # Dropdown for stock markets
    selected_market = st.selectbox(
        "Select a Stock Market (Optional):",
        list(stock_markets.keys())
    )
    market_suffix = stock_markets[selected_market]  # Get the market suffix

    # Separate input box for stock symbol
    st.write("Or manually enter a stock symbol:")
    symbol = st.text_input(
        "Enter Stock Symbol:",
        value=""
    ).upper()
    
    # Use the selected symbol from the dropdown if the input box is empty
    if not symbol and selected_symbol:
        symbol = selected_symbol

    # Automatically append the market suffix to the symbol if a market is selected
    if symbol and market_suffix:
        symbol += market_suffix

    # Ensure the symbol is not empty
    if not symbol:
        st.warning("Please enter a valid stock symbol or select a company from the dropdown.")
    
    # Historical data period selection
    historical_period = st.selectbox(
        "Select Historical Data Period:",
        ["1y", "2y", "5y", "10y", "max"]
    )
    
    prediction_days = st.slider("Prediction Days:", min_value=7, max_value=90, value=30)
    
    if st.button("Analyze Stock"):
        if ":" in symbol:
            st.error(f"The symbol '{symbol}' is not supported by Yahoo Finance. Please try a different symbol.")
        else:
            # Fetch data
            with st.spinner('Fetching stock data...'):
                stock_data = fetch_stock_data(symbol, period=historical_period)
            
            # Check if stock_data is None or empty
            if stock_data is None or stock_data.empty:
                st.warning("The stock symbol you entered is invalid or unavailable. Please try a different symbol.")
            else:
                # Display stock info
                stock = yf.Ticker(symbol)
                info = stock.info
                
                st.subheader("Company Info")
                st.write(f"**{info.get('longName', symbol)}**")
                st.write(f"Sector: {info.get('sector', 'N/A')}")
                st.write(f"Industry: {info.get('industry', 'N/A')}")
                
                # Market Data
                st.subheader("Market Data")
                current_price = stock_data['Close'].iloc[-1]
                price_change = stock_data['Close'].pct_change().iloc[-1]
                st.metric(
                    "Current Price (INR)",
                    f"₹{current_price:.2f}",
                    f"{price_change:.2%}"
                )
                
                # Prepare and make prediction
                with st.spinner('Generating prediction...'):
                    prophet_data = prepare_data_for_prophet(stock_data)
                    forecast = make_prediction(prophet_data, periods=prediction_days)
                
                # Display predictions
                st.subheader("Prediction Summary")
                last_price = prophet_data['y'].iloc[-1]
                predicted_price = forecast['yhat'].iloc[-1]
                price_diff = ((predicted_price - last_price) / last_price) * 100
                
                st.metric(
                    "Predicted Price (INR)",
                    f"₹{predicted_price:.2f}",
                    f"{price_diff:.2%}"
                )

with col2:
    if 'stock_data' in locals() and stock_data is not None:
        # Plot stock data
        try:
            st.plotly_chart(plot_stock_data(stock_data, symbol), use_container_width=True)
        except Exception as e:
            st.error(f"Error plotting stock data: {str(e)}")
        
        if 'forecast' in locals() and forecast is not None:
            # Plot prediction
            try:
                st.plotly_chart(plot_prediction(forecast, prophet_data), use_container_width=True)
            except Exception as e:
                st.error(f"Error plotting prediction: {str(e)}")
    else:
        st.warning("No stock data available. Please check the stock symbol and try again.")

# Footer with clickable links
st.markdown("""
    <style>
    .footer {
        font-size: 14px;
        text-align: center;
        color: #888;
        margin-top: 40px;
        padding-top: 20px;
        border-top: 1px solid #ddd;
    }
    .footer a {
        color: #4CAF50; /* Green color for links */
        text-decoration: none;
        font-weight: bold;
    }
    .footer a:hover {
        text-decoration: underline;
    }
    </style>
    <div class="footer">
        © 2025 Smart Investment Advisor. All rights reserved. | 
        <a href="https://example.com/about" target="_blank">About</a> | 
        <a href="https://example.com/contact" target="_blank">Contact</a> | 
        <a href="https://example.com/resources" target="_blank">Resources</a>
    </div>
""", unsafe_allow_html=True)

# Test code
stock = yf.Ticker("AAPL")  # Replace "AAPL" with the symbol you're testing
data = stock.history(period="2y")
print(data)
