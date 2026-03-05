from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from settings import config

DATA_DIR = Path(config("DATA_DIR"))
OUTPUT_DIR = Path(config("OUTPUT_DIR"))

# Load the Bloomberg futures data
df = pd.read_parquet(DATA_DIR / "bloomberg.parquet")

# Extract all px_last columns for futures (tickers ending with 'Comdty')
futures_tickers = [col[0] for col in df.columns if col[0].endswith('Comdty') and col[1] == 'px_last']

# Create a figure
fig = go.Figure()

# Add a line for each future
for ticker in futures_tickers:
    # Get the px_last data for this ticker
    price_data = df[(ticker, 'px_last')].dropna()
    
    fig.add_trace(go.Scatter(
        x=price_data.index,
        y=price_data.values,
        mode='lines',
        name=ticker,
        hovertemplate='<b>%{fullData.name}</b><br>Date: %{x}<br>Price: %{y:.2f}<extra></extra>'
    ))

# Update layout
fig.update_layout(
    title='Treasury Futures Prices Over Time',
    xaxis_title='Date',
    yaxis_title='Price',
    hovermode='x unified',
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01
    ),
    template='plotly_white'
)

# Save as interactive HTML file
output_file = OUTPUT_DIR / "treasury_futures_prices.html"
fig.write_html(output_file)

print(f"Chart saved to: {output_file}")
