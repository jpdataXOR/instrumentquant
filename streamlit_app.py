import streamlit as st
import yfinance as yf
import pandas as pd
import os

# File path for storing ETF list
ETF_FILE = "etfs.txt"

# Function to fetch top 100 US ETFs
def fetch_top_etfs():
    # Placeholder for API or scraping logic to get ETF list
    etfs = [
        "SPY", "IVV", "VOO", "QQQ", "VTI", "VTV", "VUG", "IWM", "IJH", "DIA", "XLK", "XLE", "XLF", "XLV", "XLY", "XLI", "XLC", "XLB", "XLP", "XLU"
    ]  # Add more ETFs as required

    # Save to file
    with open(ETF_FILE, "w") as f:
        f.write("\n".join(etfs))

# Function to calculate average projections
def calculate_projections(data):
    if len(data) > 5:
        # Calculate the percentage change over the last 5 data points
        returns_last_5 = data['Close'].pct_change(5).iloc[-1] * 100

        # Ensure returns_last_5 is a scalar value
        if pd.notna(returns_last_5):  # Check for a valid numeric value
            projections = {
                "1h": returns_last_5 * 40,
                "1d": returns_last_5 * 20,
            }
        else:
            projections = {
                "1h": None,
                "1d": None,
            }
    else:
        projections = {
            "1h": None,
            "1d": None,
        }
    return projections


# Fetch ETF list if not already done
if not os.path.exists(ETF_FILE):
    fetch_top_etfs()

# Read ETF list
with open(ETF_FILE, "r") as f:
    etf_list = f.read().splitlines()

# Streamlit App
st.set_page_config(page_title="ETF Analysis", layout="wide")

# Tabs for UI
tab1, tab2 = st.tabs(["Charts", "Projections Table"])

# Tab 1: Charts with user-selected ETF
with tab1:
    st.header("ETF Analysis: Price and Indicators")

    # Dropdown to select ETF symbol
    selected_etf = st.selectbox("Select an ETF", etf_list)

    # Fetch ETF data
    if selected_etf:
        data = yf.download(selected_etf, period="6mo", interval="1h")

        if not data.empty:
            # Calculate averages and projections
            avg_positive = data['Close'].pct_change().clip(lower=0).mean() * 50
            avg_negative = data['Close'].pct_change().clip(upper=0).mean() * 50
            current_change = data['Close'].pct_change().iloc[-1] * 100
            projections = calculate_projections(data)

            # Plot price chart
            st.subheader(f"Price Chart: {selected_etf}")
            st.line_chart(data['Close'])

            # Plot indicators
            st.subheader("Indicators")
            indicator_data = pd.DataFrame({
                "Avg Positive": [avg_positive],
                "Avg Negative": [avg_negative],
                "Current Change": [current_change],
                "1h Projection": [projections["1h"]],
                "1d Projection": [projections["1d"]],
            })
            st.bar_chart(indicator_data.T)
        else:
            st.warning("No data available for the selected ETF.")

# Tab 2: Projections Table
with tab2:
    st.header("Projections for All ETFs")

    # Create a DataFrame for all ETFs
    projection_results = []
    for etf in etf_list:
        data = yf.download(etf, period="10d", interval="1h")
        if not data.empty:
            projections = calculate_projections(data)
            projection_results.append({
                "ETF": etf,
                "1h Projection": projections["1h"],
                "1d Projection": projections["1d"],
            })

    # Create and display sortable DataFrame
    if projection_results:
        projection_df = pd.DataFrame(projection_results)
        st.dataframe(projection_df.sort_values(by="1d Projection", ascending=False))
    else:
        st.warning("No data available to display projections.")
