import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from datetime import datetime
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Portfolio Management Tool",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# Alpha Vantage API Key (Replace with your key)
API_KEY = "ALH36ZVG26EVQNYP"
BASE_URL = "https://www.alphavantage.co/query"

# Sidebar Inputs
with st.sidebar:
    st.title("📊 Portfolio Management Tool")
    st.write("Enter your stock portfolio details below:")

    tickers = st.text_input("Stock Tickers (comma-separated):", value="AAPL,MSFT,GOOGL")
    investment_amount = st.number_input("Total Investment Amount ($):", value=10000.0, step=100.0)
    weighting_strategy = st.selectbox("Weighting Strategy:", ["Equal Weight", "Custom"])

    # Custom weights input if selected
    weights = []
    if weighting_strategy == "Custom":
        st.write("Enter weights for each stock (total = 100%):")
        for ticker in tickers.split(","):
            weight = st.number_input(f"{ticker.strip()} weight (%):", min_value=0.0, max_value=100.0, step=0.1)
            weights.append(weight)
        if sum(weights) != 100:
            st.warning("Weights must sum up to 100%.")

# Function to fetch stock data
@st.cache
def fetch_stock_data(symbol):
    """Fetch historical stock data from Alpha Vantage."""
    try:
        response = requests.get(
            BASE_URL,
            params={
                "function": "TIME_SERIES_DAILY_ADJUSTED",
                "symbol": symbol,
                "apikey": API_KEY,
                "outputsize": "full"
            }
        )
        data = response.json()
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
            return df.sort_index()
        else:
            st.error(f"Error fetching data for {symbol}: {data.get('Note', 'Unknown error')}")
            return None
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {e}")
        return None

# Calculate Technical Indicators
def calculate_indicators(df):
    """Calculate RSI, MACD, and Bollinger Bands."""
    df = df.copy()
    df["Close"] = pd.to_numeric(df["Close"])

    # RSI Calculation
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # MACD Calculation
    ema_12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema_26 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema_12 - ema_26
    df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

    # Bollinger Bands
    rolling_mean = df["Close"].rolling(window=20).mean()
    rolling_std = df["Close"].rolling(window=20).std()
    df["Upper Band"] = rolling_mean + (rolling_std * 2)
    df["Lower Band"] = rolling_mean - (rolling_std * 2)

    return df

# Fetch and analyze data for each ticker
portfolio_data = {}
for ticker in tickers.split(","):
    ticker = ticker.strip().upper()
    st.markdown(f'<div class="section-header">{ticker} Analysis</div>', unsafe_allow_html=True)

    data = fetch_stock_data(ticker)
    if data is not None:
        portfolio_data[ticker] = calculate_indicators(data)

        # Plot Closing Prices
        st.subheader("Closing Price and Technical Indicators")
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(data.index, data["Close"], label="Closing Price", color="blue")
        ax.plot(data.index, data["Upper Band"], label="Upper Bollinger Band", linestyle="--", color="green")
        ax.plot(data.index, data["Lower Band"], label="Lower Bollinger Band", linestyle="--", color="red")
        ax.set_title(f"{ticker} Price and Bollinger Bands")
        ax.legend()
        st.pyplot(fig)

        # RSI and MACD
        st.subheader("RSI and MACD")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data["RSI"], name="RSI", line=dict(color="orange")))
        fig.add_trace(go.Scatter(x=data.index, y=data["MACD"], name="MACD", line=dict(color="blue")))
        fig.add_trace(go.Scatter(x=data.index, y=data["Signal"], name="Signal Line", line=dict(color="red")))
        fig.update_layout(title=f"{ticker} RSI and MACD", xaxis_title="Date", yaxis_title="Value")
        st.plotly_chart(fig)

# Portfolio Allocation Visualization
if weighting_strategy == "Equal Weight":
    weights = [100 / len(tickers.split(","))] * len(tickers.split(","))
allocations = [investment_amount * (weight / 100) for weight in weights]

st.markdown('<div class="section-header">Portfolio Allocation</div>', unsafe_allow_html=True)
fig = go.Figure(data=[go.Pie(labels=tickers.split(","), values=allocations)])
fig.update_layout(title="Portfolio Allocation by Investment")
st.plotly_chart(fig)

st.markdown('<div class="section-header">Summary</div>', unsafe_allow_html=True)
for ticker, weight, allocation in zip(tickers.split(","), weights, allocations):
    st.write(f"**{ticker.strip().upper()}**: {weight:.2f}% -> ${allocation:,.2f}")
