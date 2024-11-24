import streamlit as st
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Stock Analysis Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Alpha Vantage API Key
API_KEY = "ALH36ZVG26EVQNYP"
BASE_URL = "https://www.alphavantage.co/query"

# Styling for headers and sections
st.markdown("""
<style>
.section-header {
    font-size: 1.5rem;
    font-weight: bold;
    color: #2e86c1;
    margin-top: 20px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# Sidebar Inputs
with st.sidebar:
    st.title("📊 Stock Analysis Dashboard")
    ticker = st.text_input("Stock Ticker (e.g., AAPL, MSFT):", value="AAPL")
    analysis_type = st.selectbox("Select Analysis Type:", ["Overview", "Technical Analysis", "Financial Analysis"])
    indicator = None
    if analysis_type == "Technical Analysis":
        indicator = st.selectbox("Select Technical Indicator:", ["None", "SMA", "EMA", "MACD", "RSI", "Bollinger Bands"])

# Title
st.title("📈 Stock Analysis Dashboard")

# Fetch Stock Data
@st.cache_data
def fetch_stock_data(ticker):
    """Fetch historical stock data using Alpha Vantage."""
    try:
        response = requests.get(
            BASE_URL,
            params={
                "function": "TIME_SERIES_DAILY_ADJUSTED",
                "symbol": ticker,
                "apikey": API_KEY,
                "outputsize": "compact"
            }
        )
        data = response.json()
        # Log the full API response for debugging
        st.write("API Response:", data)
        if "Time Series (Daily)" in data:
            df = pd.DataFrame.from_dict(data["Time Series (Daily)"], orient="index")
            df = df.rename(columns={
                "1. open": "Open",
                "2. high": "High",
                "3. low": "Low",
                "4. close": "Close",
                "5. adjusted close": "Adj Close",
                "6. volume": "Volume"
            })
            df.index = pd.to_datetime(df.index)
            df = df.astype(float)
            return df.sort_index(), None
        elif "Note" in data:
            return None, data["Note"]
        elif "Error Message" in data:
            return None, data["Error Message"]
        else:
            return None, "Unknown error occurred while fetching data."
    except Exception as e:
        return None, str(e)

# Fetch Company Overview
@st.cache_data
def fetch_company_overview(ticker):
    """Fetch company overview using Alpha Vantage."""
    try:
        response = requests.get(
            BASE_URL,
            params={
                "function": "OVERVIEW",
                "symbol": ticker,
                "apikey": API_KEY
            }
        )
        data = response.json()
        if "Symbol" in data:
            return data, None
        elif "Note" in data:
            return None, data["Note"]
        elif "Error Message" in data:
            return None, data["Error Message"]
        else:
            return None, "Unknown error occurred while fetching company overview."
    except Exception as e:
        return None, str(e)

# Calculate Technical Indicators
def calculate_sma(df, window=20):
    """Calculate Simple Moving Average (SMA)."""
    df["SMA"] = df["Close"].rolling(window=window).mean()
    return df

def calculate_ema(df, window=20):
    """Calculate Exponential Moving Average (EMA)."""
    df["EMA"] = df["Close"].ewm(span=window, adjust=False).mean()
    return df

def calculate_macd(df):
    """Calculate MACD and Signal Line."""
    df["MACD"] = df["Close"].ewm(span=12, adjust=False).mean() - df["Close"].ewm(span=26, adjust=False).mean()
    df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    return df

def calculate_rsi(df, window=14):
    """Calculate Relative Strength Index (RSI)."""
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

def calculate_bollinger_bands(df, window=20):
    """Calculate Bollinger Bands."""
    df["Middle"] = df["Close"].rolling(window=window).mean()
    df["Upper"] = df["Middle"] + 2 * df["Close"].rolling(window=window).std()
    df["Lower"] = df["Middle"] - 2 * df["Close"].rolling(window=window).std()
    return df

# Overview Section
if analysis_type == "Overview":
    st.header("Company Overview")
    company_data, error = fetch_company_overview(ticker)
    if error:
        st.error(f"Error fetching company overview: {error}")
    else:
        st.subheader(company_data.get("Name", ticker))
        st.write(company_data.get("Description", "No company description available."))
        st.write(f"**Industry:** {company_data.get('Industry', 'N/A')}")
        st.write(f"**Market Cap:** ${company_data.get('MarketCapitalization', 'N/A')}")
        st.write(f"**Dividend Yield:** {company_data.get('DividendYield', 'N/A')}")
        st.write(f"**Headquarters:** {company_data.get('Address', 'N/A')}")

# Technical Analysis Section
if analysis_type == "Technical Analysis":
    st.header("Technical Analysis")
    stock_data, error = fetch_stock_data(ticker)
    if error:
        st.error(f"Error fetching stock data: {error}")
        if "Note" in error:
            st.warning("You may have hit the API request limit. Try again later.")
        elif "Error Message" in error:
            st.warning("Invalid ticker or unsupported stock symbol.")
    elif stock_data is not None:
        st.line_chart(stock_data["Close"])
        if indicator == "SMA":
            stock_data = calculate_sma(stock_data)
            st.line_chart(stock_data[["Close", "SMA"]])
        elif indicator == "EMA":
            stock_data = calculate_ema(stock_data)
            st.line_chart(stock_data[["Close", "EMA"]])
        elif indicator == "MACD":
            stock_data = calculate_macd(stock_data)
            st.line_chart(stock_data[["MACD", "Signal"]])
        elif indicator == "RSI":
            stock_data = calculate_rsi(stock_data)
            st.line_chart(stock_data[["RSI"]])
        elif indicator == "Bollinger Bands":
            stock_data = calculate_bollinger_bands(stock_data)
            st.line_chart(stock_data[["Close", "Upper", "Middle", "Lower"]])

# Financial Analysis Section
if analysis_type == "Financial Analysis":
    st.header("Financial Analysis")
    st.write("**Financial metrics and insights coming soon!**")
