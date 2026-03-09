"""Create arbitrage spread plots (HTML + PNG) by tenor."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go

from settings import config

DATA_DIR = Path(config("DATA_DIR"))
OUTPUT_DIR = Path(config("OUTPUT_DIR"))
TENOR_ORDER = ["2Y", "5Y", "10Y", "20Y", "30Y"]


def load_spreads(path: Path) -> pd.DataFrame:
    """Load arbitrage spreads and normalize date index."""
    if not path.exists():
        raise FileNotFoundError(f"Arbitrage spread file not found: {path}")

    df = pd.read_parquet(path)
    if "Date" in df.columns:
        df = df.set_index("Date")
    df.index = pd.to_datetime(df.index)
    return df.sort_index()


def select_tenors(df: pd.DataFrame) -> list[str]:
    """Select tenor columns in a stable order."""
    tenors = [tenor for tenor in TENOR_ORDER if tenor in df.columns]
    if not tenors:
        raise ValueError("No tenor columns found in arbitrage spread data.")
    return tenors


def build_html_chart(df: pd.DataFrame, tenors: list[str], output_path: Path):
    """Write interactive HTML chart with one line per tenor."""
    fig = go.Figure()
    for tenor in tenors:
        s = df[tenor].dropna()
        if s.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=s.index,
                y=s.values,
                mode="lines",
                name=tenor,
            )
        )

    fig.add_hline(y=0.0, line_dash="dash", line_color="black")
    fig.update_layout(
        title="Treasury Spot-Futures Arbitrage Spreads by Tenor",
        xaxis_title="Date",
        yaxis_title="Spread (bps)",
        template="plotly_white",
        hovermode="x unified",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(output_path)


def build_png_chart(df: pd.DataFrame, tenors: list[str], output_path: Path):
    """Write static PNG chart for reports."""
    plt.figure(figsize=(12, 6))
    for tenor in tenors:
        s = df[tenor].dropna()
        if s.empty:
            continue
        plt.plot(s.index, s.values, linewidth=1.2, label=tenor)

    plt.axhline(0.0, color="black", linestyle="--", linewidth=1.0)
    plt.title("Treasury Spot-Futures Arbitrage Spreads by Tenor")
    plt.xlabel("Date")
    plt.ylabel("Spread (bps)")
    plt.legend(title="Tenor")
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()


def main():
    spread_path = DATA_DIR / "arbitrage_spreads.parquet"
    html_path = OUTPUT_DIR / "arbitrage_spreads_by_tenor.html"
    png_path = OUTPUT_DIR / "arbitrage_spreads_by_tenor.png"

    spreads = load_spreads(spread_path)
    tenors = select_tenors(spreads)

    build_html_chart(spreads, tenors, html_path)
    build_png_chart(spreads, tenors, png_path)

    print(f"Wrote {html_path}")
    print(f"Wrote {png_path}")


if __name__ == "__main__":
    main()
