import streamlit as st
import yfinance as yf
import pandas as pd
import os
import plotly.graph_objs as go
import plotly.express as px

# File path for storing ETF list
ETF_FILE = "etfs.txt"

# Function to fetch top 100 US ETFs
def fetch_top_etfs():
    # Comprehensive list of popular ETFs
    etfs = [
        "SPY", "IVV", "VOO", "QQQ", "VTI", "VTV", "VUG", "IWM", "IJH", "DIA", 
        "XLK", "XLE", "XLF", "XLV", "XLY", "XLI", "XLC", "XLB", "XLP", "XLU",
        "SCHD", "VEA", "VWO", "VXUS", "AGG", "BND", "VIG", "VTIP", "GLD", "SLV"
    ]

    # Save to file
    with open(ETF_FILE, "w") as f:
        f.write("\n".join(etfs))

# Function to create the advanced indicators graph
def create_indicators_graph(data):
    # Ensure 'Close' is a Series, not a multi-dimensional array
    close_prices = data['Close'].squeeze()
    
    # Calculate returns (percentage change)
    returns = close_prices.pct_change()

    # Calculate average positive and negative returns
    total_positive = returns[returns > 0].mean() * 100 if len(returns[returns > 0]) > 0 else 0
    total_negative = returns[returns < 0].mean() * 100 if len(returns[returns < 0]) > 0 else 0

    # Current percentage change (most recent period)
    current_change = returns.iloc[-1] * 100 if len(returns) > 0 else 0
    
    # Calculate thresholds for positive and negative movements (33%, 50%, 100%)
    thresholds_pos = [total_positive * (1 + (i + 1) * 0.33) for i in range(3)]
    thresholds_neg = [total_negative * (1 - (i + 1) * 0.33) for i in range(3)]

    # Projected returns based on the last 5 periods (similar to TradingView logic)
    projected_return_1h = returns.tail(5).mean() * 40
    projected_return_1d = returns.tail(5).mean() * 20

    # Create the figure
    fig = go.Figure()

    # Plot average positive and negative returns
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[total_positive, total_positive],
        mode='lines', name='Average Positive', line=dict(color='green', dash='solid')
    ))
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[total_negative, total_negative],
        mode='lines', name='Average Negative', line=dict(color='red', dash='solid')
    ))

    # Plot current price change
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[current_change, current_change],
        mode='lines', name='Current Change', line=dict(color='black', dash='dot')
    ))

    # Plot thresholds for positive and negative moves
    for i, threshold in enumerate(thresholds_pos):
        fig.add_trace(go.Scatter(
            x=[0, 1], y=[threshold, threshold],
            mode='lines', name=f'Positive {33 * (i+1)}%', line=dict(color=f'rgba(0,255,0,{(i+1)*0.5})')
        ))
    for i, threshold in enumerate(thresholds_neg):
        fig.add_trace(go.Scatter(
            x=[0, 1], y=[threshold, threshold],
            mode='lines', name=f'Negative {33 * (i+1)}%', line=dict(color=f'rgba(255,0,0,{(i+1)*0.5})')
        ))

    # Plot projected returns (1-hour and 1-day)
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[projected_return_1h, projected_return_1h],
        mode='lines', name='1 Hour Projection', line=dict(color='orange', dash='solid')
    ))
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[projected_return_1d, projected_return_1d],
        mode='lines', name='1 Day Projection', line=dict(color='blue', dash='solid')
    ))

    # Add a horizontal line at 0 (zero line)
    fig.add_hline(y=0, line_dash="dash", line_color="gray")

    # Customize layout
    fig.update_layout(
        title="ETF Performance Indicators",
        xaxis_title="Time Period",
        yaxis_title="Percentage Change",
        height=500,
        width=800,
        showlegend=True
    )

    return fig

# Function to calculate average projections
def calculate_projections(data):
    try:
        # Ensure 'Close' is a Series
        close_prices = data['Close'].squeeze()
        
        if len(close_prices) > 5:
            # Calculate the percentage change over the last 5 data points
            returns_series = close_prices.pct_change(5)
            
            # Get the last value safely
            returns_last_5 = returns_series.iloc[-1]
            
            # Check if it's a valid number
            if pd.notna(returns_last_5) and isinstance(returns_last_5, (int, float)):
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
    except Exception as e:
        print(f"Error in calculate_projections: {e}")
        return {
            "1h": None,
            "1d": None,
        }

# Fetch ETF list if not already done
if not os.path.exists(ETF_FILE):
    fetch_top_etfs()

# Read ETF list
with open(ETF_FILE, "r") as f:
    etf_list = f.read().splitlines()

# Streamlit App Configuration
st.set_page_config(page_title="ETF Analysis", layout="wide")

# Main App
def main():
    # Tabs for UI
    tab1, tab2 = st.tabs(["Charts", "Projections Table"])

    # Tab 1: Charts with user-selected ETF
    with tab1:
        st.header("ETF Analysis: Price and Indicators")

        # Dropdown to select ETF symbol
        selected_etf = st.selectbox("Select an ETF", etf_list)

        # Fetch ETF data
        if selected_etf:
            try:
                # Specify columns to download and ensure single column
                data = yf.download(selected_etf, period="6mo", interval="1h")[['Close']]
                
                # Ensure data is a Series
                close_prices = data['Close'].squeeze()

                if not close_prices.empty:
                    # Price Chart
                    st.subheader(f"Price Chart: {selected_etf}")
                    price_fig = px.line(x=close_prices.index, y=close_prices.values, title=f'{selected_etf} Price Over Time')
                    price_fig.update_layout(
                        height=400, 
                        width=700,
                        xaxis_title='Date',
                        yaxis_title='Price'
                    )
                    st.plotly_chart(price_fig)

                    # Indicators Graph
                    st.subheader("Performance Indicators")
                    indicators_fig = create_indicators_graph(pd.DataFrame({'Close': close_prices}))
                    st.plotly_chart(indicators_fig)

                else:
                    st.warning("No data available for the selected ETF.")
            except Exception as e:
                st.error(f"Error fetching data for {selected_etf}: {e}")

    # Tab 2: Projections Table
    with tab2:
        st.header("Projections for All ETFs")

        # Create a DataFrame for all ETFs
        projection_results = []
        progress_bar = st.progress(0)
        
        for i, etf in enumerate(etf_list):
            try:
                # Specify columns to download and ensure single column
                data = yf.download(etf, period="10d", interval="1h")[['Close']]
                close_prices = data['Close'].squeeze()

                if not close_prices.empty:
                    projections = calculate_projections(pd.DataFrame({'Close': close_prices}))
                    projection_results.append({
                        "ETF": etf,
                        "1h Projection": projections["1h"],
                        "1d Projection": projections["1d"],
                    })
                
                # Update progress bar
                progress = int((i + 1) / len(etf_list) * 100)
                progress_bar.progress(progress)
            
            except Exception as e:
                print(f"Error processing {etf}: {e}")

        # Create and display sortable DataFrame
        if projection_results:
            projection_df = pd.DataFrame(projection_results)
            st.dataframe(projection_df.sort_values(by="1d Projection", ascending=False))
        else:
            st.warning("No data available to display projections.")

# Run the app
if __name__ == "__main__":
    main()
