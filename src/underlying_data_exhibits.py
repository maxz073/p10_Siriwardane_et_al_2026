"""Generate spread-input-focused tables and figures for the replication writeup."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from settings import config

DATA_DIR = Path(config("DATA_DIR"))
OUTPUT_DIR = Path(config("OUTPUT_DIR"))

TENOR_TO_TICKER = {
    "2Y": "TU2 Comdty",
    "5Y": "FV2 Comdty",
    "10Y": "TY2 Comdty",
    "20Y": "WN2 Comdty",
    "30Y": "US2 Comdty",
}
TENOR_ORDER = ["2Y", "5Y", "10Y", "20Y", "30Y"]

OIS_MONTH_TICKERS = {
    2: "USSOB CMPN Curncy",
    3: "USSOC CMPN Curncy",
    6: "USSOF CMPN Curncy",
}
OIS_MONTH_ORDER = [2, 3, 6]

FUTURES_FIELDS = [
    "px_last",
    "px_volume",
    "fut_ctd_cusip",
    "fut_cnvs_factor",
    "current_contract_month_yr",
]


def get_field_series(df: pd.DataFrame, ticker: str, field: str) -> pd.Series | None:
    """Extract a Bloomberg field from wide multi-index or flattened columns."""
    if isinstance(df.columns, pd.MultiIndex):
        if (ticker, field) in df.columns:
            return df[(ticker, field)]
        for col in df.columns:
            if col[0] == ticker and str(col[1]).lower() == field.lower():
                return df[col]
        return None

    for col in df.columns:
        col_s = str(col).lower()
        if ticker.lower() in col_s and field.lower() in col_s:
            return df[col]
    return None


def _normalize_date_index(df: pd.DataFrame, date_col: str = "Date") -> pd.DataFrame:
    out = df.copy()
    if date_col in out.columns:
        out = out.set_index(date_col)
    out.index = pd.to_datetime(out.index).normalize()
    return out.sort_index()


def _ensure_exists(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load all data pieces used directly in spread construction."""
    bbg_path = DATA_DIR / "bloomberg.parquet"
    spreads_path = DATA_DIR / "arbitrage_spreads.parquet"
    implied_repo_path = DATA_DIR / "implied_repo_first_deferred.parquet"
    holding_path = DATA_DIR / "holding_period_days.parquet"
    irr_bonds_path = DATA_DIR / "TFZ_IRR.parquet"

    for path in [bbg_path, spreads_path, implied_repo_path, holding_path, irr_bonds_path]:
        _ensure_exists(path)

    bloomberg = _normalize_date_index(pd.read_parquet(bbg_path))
    spreads = _normalize_date_index(pd.read_parquet(spreads_path))
    implied_repo = _normalize_date_index(pd.read_parquet(implied_repo_path))
    holding_period_days = _normalize_date_index(pd.read_parquet(holding_path))

    irr_bonds = pd.read_parquet(irr_bonds_path)
    if "caldt" in irr_bonds.columns:
        irr_bonds["caldt"] = pd.to_datetime(irr_bonds["caldt"]).dt.normalize()

    return bloomberg, spreads, implied_repo, holding_period_days, irr_bonds


def _float_format(x: float) -> str:
    return f"{x:,.2f}"


def write_table_pair(
    table_df: pd.DataFrame,
    tabular_filename: str,
    table_filename: str,
    caption: str,
    label: str,
):
    """Write a tabular .tex and a full table wrapper that auto-fits page width."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    tabular_tex = table_df.to_latex(
        index=False,
        float_format=_float_format,
        na_rep="",
        escape=True,
    )
    (OUTPUT_DIR / tabular_filename).write_text(tabular_tex, encoding="utf-8")

    full_table_tex = "\n".join(
        [
            r"\begin{table}[htbp]",
            r"\centering",
            rf"\caption{{{caption}}}",
            rf"\label{{{label}}}",
            r"\resizebox{\textwidth}{!}{%",
            rf"\input{{\PathToOutput/{tabular_filename}}}",
            r"}",
            r"\end{table}",
            "",
        ]
    )
    (OUTPUT_DIR / table_filename).write_text(full_table_tex, encoding="utf-8")


def write_figure_snippet(
    snippet_filename: str,
    image_filename: str,
    caption: str,
    label: str,
):
    snippet = "\n".join(
        [
            r"\begin{figure}[htbp]",
            r"\centering",
            rf"\includegraphics[width=0.85\linewidth]{{\PathToOutput/{image_filename}}}",
            rf"\caption{{{caption}}}",
            rf"\label{{{label}}}",
            r"\end{figure}",
            "",
        ]
    )
    (OUTPUT_DIR / snippet_filename).write_text(snippet, encoding="utf-8")


def write_line_chart(df: pd.DataFrame, title: str, y_label: str, png_filename: str, html_filename: str):
    """Write PNG and interactive HTML line charts from a Date-indexed DataFrame."""
    chart_df = df.copy().sort_index().dropna(how="all")
    if chart_df.empty:
        raise ValueError(f"Cannot build chart '{title}': no non-missing data.")

    plt.figure(figsize=(12, 6))
    for col in chart_df.columns:
        plt.plot(chart_df.index, chart_df[col], linewidth=1.2, label=str(col))
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel(y_label)
    plt.legend(title="Series")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / png_filename, dpi=300)
    plt.close()

    fig = go.Figure()
    for col in chart_df.columns:
        fig.add_trace(
            go.Scatter(
                x=chart_df.index,
                y=chart_df[col],
                mode="lines",
                name=str(col),
            )
        )
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title=y_label,
        template="plotly_white",
        hovermode="x unified",
    )
    fig.write_html(OUTPUT_DIR / html_filename)


def build_primary_summary_table(bloomberg: pd.DataFrame, spreads: pd.DataFrame) -> pd.DataFrame:
    """Summary of futures activity and resulting spread moments by tenor."""
    rows = []
    for tenor in TENOR_ORDER:
        ticker = TENOR_TO_TICKER[tenor]
        px = get_field_series(bloomberg, ticker, "px_last")
        vol = get_field_series(bloomberg, ticker, "px_volume")
        spr = spreads[tenor] if tenor in spreads.columns else pd.Series(dtype=float)
        spr = pd.to_numeric(spr, errors="coerce").dropna()
        vol_clean = pd.to_numeric(vol, errors="coerce").dropna() if vol is not None else pd.Series(dtype=float)

        rows.append(
            {
                "Tenor": tenor,
                "Contract": ticker,
                "Futures Price Obs": int(px.notna().sum()) if px is not None else 0,
                "Median Daily Volume": float(vol_clean.median()) if not vol_clean.empty else float("nan"),
                "Spread Mean (bps)": float(spr.mean()) if not spr.empty else float("nan"),
                "Spread Std (bps)": float(spr.std()) if not spr.empty else float("nan"),
                "Spread Min (bps)": float(spr.min()) if not spr.empty else float("nan"),
                "Spread Max (bps)": float(spr.max()) if not spr.empty else float("nan"),
            }
        )
    return pd.DataFrame(rows)


def build_futures_input_coverage_table(bloomberg: pd.DataFrame) -> pd.DataFrame:
    """Coverage of the exact futures fields used in calc_spread.py."""
    rows = []
    for tenor in TENOR_ORDER:
        ticker = TENOR_TO_TICKER[tenor]
        raw = pd.DataFrame(index=bloomberg.index)
        for field in FUTURES_FIELDS:
            series = get_field_series(bloomberg, ticker, field)
            raw[field] = series if series is not None else np.nan

        raw["px_volume"] = pd.to_numeric(raw["px_volume"], errors="coerce")
        volume_positive = raw["px_volume"] > 0
        complete_mask = (
            volume_positive
            & raw["px_last"].notna()
            & raw["fut_ctd_cusip"].notna()
            & raw["fut_cnvs_factor"].notna()
            & raw["current_contract_month_yr"].notna()
        )

        obs_total = len(raw)
        pass_count = int(complete_mask.sum())
        rows.append(
            {
                "Tenor": tenor,
                "Ticker": ticker,
                "Trading Days": int(obs_total),
                "Price Obs": int(raw["px_last"].notna().sum()),
                "Positive Volume Obs": int(volume_positive.sum()),
                "Conv Factor Obs": int(raw["fut_cnvs_factor"].notna().sum()),
                "CTD CUSIP Obs": int(raw["fut_ctd_cusip"].notna().sum()),
                "Contract Month Obs": int(raw["current_contract_month_yr"].notna().sum()),
                "Rows Passing Raw Filter": pass_count,
                "Pass Rate (%)": float((100.0 * pass_count / obs_total) if obs_total else float("nan")),
            }
        )
    return pd.DataFrame(rows)


def extract_ois_inputs(bloomberg: pd.DataFrame) -> pd.DataFrame:
    """Extract 2M/3M/6M OIS rates used in interpolation."""
    out = pd.DataFrame(index=bloomberg.index)
    for month in OIS_MONTH_ORDER:
        ticker = OIS_MONTH_TICKERS[month]
        series = get_field_series(bloomberg, ticker, "px_last")
        out[f"{month}M OIS"] = pd.to_numeric(series, errors="coerce") if series is not None else np.nan
    return out.sort_index()


def build_ois_input_summary_table(ois_inputs: pd.DataFrame) -> pd.DataFrame:
    """Summary stats for OIS curve points used in spread construction."""
    rows = []
    for month in OIS_MONTH_ORDER:
        col = f"{month}M OIS"
        series = pd.to_numeric(ois_inputs[col], errors="coerce").dropna() if col in ois_inputs else pd.Series(dtype=float)
        rows.append(
            {
                "OIS Tenor": f"{month}M",
                "Bloomberg Ticker": OIS_MONTH_TICKERS[month],
                "Obs": int(series.shape[0]),
                "Mean Rate (%)": float(series.mean()) if not series.empty else float("nan"),
                "Std Rate (%)": float(series.std()) if not series.empty else float("nan"),
                "Min Rate (%)": float(series.min()) if not series.empty else float("nan"),
                "Max Rate (%)": float(series.max()) if not series.empty else float("nan"),
            }
        )
    return pd.DataFrame(rows)


def build_ctd_bond_coverage_table(irr_bonds: pd.DataFrame) -> pd.DataFrame:
    """Coverage diagnostics for CTD bond fields used by implied-repo calculations."""
    n_obs = int(len(irr_bonds))
    start_date = pd.to_datetime(irr_bonds["caldt"]).min() if "caldt" in irr_bonds else pd.NaT
    end_date = pd.to_datetime(irr_bonds["caldt"]).max() if "caldt" in irr_bonds else pd.NaT

    rows = [
        {"Metric": "Bond-date observations", "Value": n_obs},
        {"Metric": "Unique CUSIPs", "Value": int(irr_bonds["tcusip"].nunique()) if "tcusip" in irr_bonds else 0},
        {"Metric": "Non-missing clean_price", "Value": int(irr_bonds["clean_price"].notna().sum()) if "clean_price" in irr_bonds else 0},
        {"Metric": "Non-missing coupon_rate", "Value": int(irr_bonds["coupon_rate"].notna().sum()) if "coupon_rate" in irr_bonds else 0},
        {"Metric": "Non-missing coupon_frequency", "Value": int(irr_bonds["coupon_frequency"].notna().sum()) if "coupon_frequency" in irr_bonds else 0},
        {"Metric": "Non-missing next_coupon_date", "Value": int(irr_bonds["next_coupon_date"].notna().sum()) if "next_coupon_date" in irr_bonds else 0},
        {"Metric": "Non-missing prev_coupon_date", "Value": int(irr_bonds["prev_coupon_date"].notna().sum()) if "prev_coupon_date" in irr_bonds else 0},
        {"Metric": "Sample start date", "Value": start_date.strftime("%Y-%m-%d") if pd.notna(start_date) else ""},
        {"Metric": "Sample end date", "Value": end_date.strftime("%Y-%m-%d") if pd.notna(end_date) else ""},
    ]
    return pd.DataFrame(rows)


def build_holding_period_summary_table(holding_period_days: pd.DataFrame) -> pd.DataFrame:
    """Distribution summary of the holding-period input used in OIS interpolation."""
    rows = []
    for tenor in TENOR_ORDER:
        if tenor not in holding_period_days.columns:
            continue
        series = pd.to_numeric(holding_period_days[tenor], errors="coerce").dropna()
        rows.append(
            {
                "Tenor": tenor,
                "Obs": int(series.shape[0]),
                "Mean Days": float(series.mean()) if not series.empty else float("nan"),
                "Median Days": float(series.median()) if not series.empty else float("nan"),
                "P10 Days": float(series.quantile(0.10)) if not series.empty else float("nan"),
                "P90 Days": float(series.quantile(0.90)) if not series.empty else float("nan"),
                "Min Days": float(series.min()) if not series.empty else float("nan"),
                "Max Days": float(series.max()) if not series.empty else float("nan"),
            }
        )
    return pd.DataFrame(rows)


def interpolate_ois_to_holding_period(ois_inputs: pd.DataFrame, holding_period_days: pd.DataFrame) -> pd.DataFrame:
    """Interpolate OIS from 2M/3M/6M onto tenor-specific holding periods (in bps)."""
    missing_cols = [f"{month}M OIS" for month in OIS_MONTH_ORDER if f"{month}M OIS" not in ois_inputs.columns]
    if missing_cols:
        raise ValueError(f"Missing OIS input columns required for interpolation: {missing_cols}")

    available_tenors = [tenor for tenor in TENOR_ORDER if tenor in holding_period_days.columns]
    if not available_tenors:
        raise ValueError("No holding-period tenor columns found for OIS interpolation.")

    common_idx = holding_period_days.index.copy()
    for month in OIS_MONTH_ORDER:
        common_idx = common_idx.intersection(ois_inputs[f"{month}M OIS"].dropna().index)
    common_idx = common_idx.sort_values()
    if common_idx.empty:
        raise ValueError(
            "No overlapping dates between holding-period series and required OIS inputs."
        )

    tenors_months = np.array(OIS_MONTH_ORDER, dtype=float)
    hold_months = holding_period_days.loc[common_idx, available_tenors].astype(float) / (365.0 / 12.0)
    ois_curve_matrix = np.array(
        [pd.to_numeric(ois_inputs.loc[common_idx, f"{month}M OIS"], errors="coerce").values for month in OIS_MONTH_ORDER]
    )

    out_values = np.full((len(common_idx), len(available_tenors)), np.nan)
    for i in range(len(common_idx)):
        ois_row_pct = ois_curve_matrix[:, i]
        if np.any(np.isnan(ois_row_pct)):
            continue
        for j in range(len(available_tenors)):
            month_val = hold_months.iloc[i, j]
            if np.isnan(month_val):
                continue
            out_values[i, j] = np.interp(
                np.clip(month_val, tenors_months.min(), tenors_months.max()),
                tenors_months,
                ois_row_pct,
            ) * 100.0

    return pd.DataFrame(out_values, index=common_idx, columns=available_tenors)


def build_spread_component_summary_table(
    implied_repo: pd.DataFrame,
    interpolated_ois_bps: pd.DataFrame,
    spreads: pd.DataFrame,
    holding_period_days: pd.DataFrame,
) -> pd.DataFrame:
    """Summary table for the exact decomposition: spread = implied repo - interpolated OIS."""
    rows = []
    tenors = [
        tenor
        for tenor in TENOR_ORDER
        if tenor in implied_repo.columns
        and tenor in interpolated_ois_bps.columns
        and tenor in spreads.columns
        and tenor in holding_period_days.columns
    ]
    for tenor in tenors:
        comp = pd.concat(
            [
                pd.to_numeric(implied_repo[tenor], errors="coerce").rename("Implied Repo (bps)"),
                pd.to_numeric(interpolated_ois_bps[tenor], errors="coerce").rename("Interpolated OIS (bps)"),
                pd.to_numeric(spreads[tenor], errors="coerce").rename("Spread (bps)"),
                pd.to_numeric(holding_period_days[tenor], errors="coerce").rename("Holding Days"),
            ],
            axis=1,
        ).dropna()

        corr = comp["Implied Repo (bps)"].corr(comp["Interpolated OIS (bps)"]) if len(comp) > 1 else float("nan")
        rows.append(
            {
                "Tenor": tenor,
                "Obs": int(comp.shape[0]),
                "Mean Implied Repo (bps)": float(comp["Implied Repo (bps)"].mean()) if not comp.empty else float("nan"),
                "Mean Interpolated OIS (bps)": float(comp["Interpolated OIS (bps)"].mean()) if not comp.empty else float("nan"),
                "Mean Spread (bps)": float(comp["Spread (bps)"].mean()) if not comp.empty else float("nan"),
                "Spread Std (bps)": float(comp["Spread (bps)"].std()) if not comp.empty else float("nan"),
                "Corr(IRR, OIS)": float(corr) if pd.notna(corr) else float("nan"),
                "Mean Holding Days": float(comp["Holding Days"].mean()) if not comp.empty else float("nan"),
            }
        )
    return pd.DataFrame(rows)


def build_underlying_futures_prices_chart(bloomberg: pd.DataFrame):
    chart_df = pd.DataFrame(index=bloomberg.index)
    for tenor in TENOR_ORDER:
        ticker = TENOR_TO_TICKER[tenor]
        series = get_field_series(bloomberg, ticker, "px_last")
        chart_df[tenor] = pd.to_numeric(series, errors="coerce") if series is not None else np.nan

    write_line_chart(
        df=chart_df,
        title="Underlying Treasury Futures Prices by Tenor (Second Deferred)",
        y_label="Price",
        png_filename="underlying_futures_prices_by_tenor.png",
        html_filename="underlying_futures_prices_by_tenor.html",
    )
    write_figure_snippet(
        snippet_filename="underlying_futures_prices_figure.tex",
        image_filename="underlying_futures_prices_by_tenor.png",
        caption=(
            "Underlying second-deferred Treasury futures prices by tenor. "
            "Takeaway: these are the exact futures price inputs used in implied-repo "
            "construction, and they move together but with tenor-specific levels and variation."
        ),
        label="fig:underlying_futures_prices_by_tenor",
    )


def build_ois_input_chart(ois_inputs: pd.DataFrame):
    write_line_chart(
        df=ois_inputs,
        title="OIS Inputs Used for Interpolation (2M, 3M, 6M)",
        y_label="Rate (%)",
        png_filename="ois_input_rates.png",
        html_filename="ois_input_rates.html",
    )
    write_figure_snippet(
        snippet_filename="ois_input_rates_figure.tex",
        image_filename="ois_input_rates.png",
        caption=(
            "OIS input rates at 2M, 3M, and 6M. Takeaway: these curve points are the "
            "only OIS inputs used to interpolate the financing leg in spread construction."
        ),
        label="fig:ois_input_rates",
    )


def build_holding_period_chart(holding_period_days: pd.DataFrame):
    chart_df = holding_period_days[[tenor for tenor in TENOR_ORDER if tenor in holding_period_days.columns]]
    write_line_chart(
        df=chart_df,
        title="Holding Period (Days) Used for OIS Interpolation by Tenor",
        y_label="Days",
        png_filename="holding_period_days_by_tenor.png",
        html_filename="holding_period_days_by_tenor.html",
    )
    write_figure_snippet(
        snippet_filename="holding_period_days_by_tenor_figure.tex",
        image_filename="holding_period_days_by_tenor.png",
        caption=(
            "Tenor-specific holding periods (in days) used to map futures trades into "
            "interpolated OIS rates. Takeaway: holding horizons vary substantially over time and by tenor."
        ),
        label="fig:holding_period_days_by_tenor",
    )


def build_implied_repo_vs_ois_chart(implied_repo: pd.DataFrame, interpolated_ois_bps: pd.DataFrame):
    tenors = [tenor for tenor in TENOR_ORDER if tenor in implied_repo.columns and tenor in interpolated_ois_bps.columns]
    if not tenors:
        raise ValueError("No overlapping tenor columns between implied repo and interpolated OIS.")

    common_idx = implied_repo.index.intersection(interpolated_ois_bps.index).sort_values()
    implied_repo = implied_repo.loc[common_idx, tenors].apply(pd.to_numeric, errors="coerce")
    interpolated_ois_bps = interpolated_ois_bps.loc[common_idx, tenors].apply(pd.to_numeric, errors="coerce")

    color_cycle = plt.rcParams["axes.prop_cycle"].by_key().get("color", [])
    color_map = {
        tenor: color_cycle[i % len(color_cycle)] if color_cycle else None
        for i, tenor in enumerate(tenors)
    }

    plt.figure(figsize=(13, 7))
    for tenor in tenors:
        plt.plot(
            common_idx,
            implied_repo[tenor],
            linewidth=1.2,
            color=color_map[tenor],
            label=f"{tenor} IRR",
        )
        plt.plot(
            common_idx,
            interpolated_ois_bps[tenor],
            linewidth=1.2,
            linestyle="--",
            color=color_map[tenor],
            label=f"{tenor} OIS",
        )
    plt.title("Implied Repo vs Interpolated OIS by Tenor")
    plt.xlabel("Date")
    plt.ylabel("Basis Points")
    plt.legend(ncol=2, fontsize=8)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "implied_repo_vs_interpolated_ois_by_tenor.png", dpi=300)
    plt.close()

    fig = go.Figure()
    for tenor in tenors:
        fig.add_trace(
            go.Scatter(
                x=common_idx,
                y=implied_repo[tenor],
                mode="lines",
                name=f"{tenor} IRR",
                line={"dash": "solid"},
            )
        )
        fig.add_trace(
            go.Scatter(
                x=common_idx,
                y=interpolated_ois_bps[tenor],
                mode="lines",
                name=f"{tenor} OIS",
                line={"dash": "dash"},
            )
        )
    fig.update_layout(
        title="Implied Repo vs Interpolated OIS by Tenor",
        xaxis_title="Date",
        yaxis_title="Basis Points",
        template="plotly_white",
        hovermode="x unified",
    )
    fig.write_html(OUTPUT_DIR / "implied_repo_vs_interpolated_ois_by_tenor.html")

    write_figure_snippet(
        snippet_filename="implied_repo_vs_interpolated_ois_by_tenor_figure.tex",
        image_filename="implied_repo_vs_interpolated_ois_by_tenor.png",
        caption=(
            "Implied repo (solid) versus interpolated OIS (dashed) by tenor. "
            "Takeaway: arbitrage spreads are generated by these two components, and "
            "their wedge varies materially across maturities and over time."
        ),
        label="fig:implied_repo_vs_interpolated_ois_by_tenor",
    )


def main():
    bloomberg, spreads, implied_repo, holding_period_days, irr_bonds = load_inputs()
    ois_inputs = extract_ois_inputs(bloomberg)
    interpolated_ois_bps = interpolate_ois_to_holding_period(ois_inputs, holding_period_days)

    primary_summary = build_primary_summary_table(bloomberg, spreads)
    futures_coverage = build_futures_input_coverage_table(bloomberg)
    ois_summary = build_ois_input_summary_table(ois_inputs)
    ctd_coverage = build_ctd_bond_coverage_table(irr_bonds)
    holding_summary = build_holding_period_summary_table(holding_period_days)
    component_summary = build_spread_component_summary_table(
        implied_repo=implied_repo,
        interpolated_ois_bps=interpolated_ois_bps,
        spreads=spreads,
        holding_period_days=holding_period_days,
    )

    write_table_pair(
        table_df=primary_summary,
        tabular_filename="underlying_summary_stats_tabular.tex",
        table_filename="underlying_summary_stats_table.tex",
        caption=(
            "Underlying data coverage and spread distribution by tenor. "
            "Takeaway: each tenor has broad daily coverage in futures prices, and spread moments "
            "differ meaningfully across maturities, motivating tenor-by-tenor analysis."
        ),
        label="table:underlying_summary_stats",
    )
    write_table_pair(
        table_df=futures_coverage,
        tabular_filename="futures_input_coverage_tabular.tex",
        table_filename="futures_input_coverage_table.tex",
        caption=(
            "Coverage of futures-side inputs used in implied-repo calculations. "
            "Takeaway: most tenor-date rows pass the raw input filters "
            "(positive volume plus non-missing required contract fields)."
        ),
        label="table:futures_input_coverage",
    )
    write_table_pair(
        table_df=ois_summary,
        tabular_filename="ois_input_summary_tabular.tex",
        table_filename="ois_input_summary_table.tex",
        caption=(
            "Summary statistics for OIS tenors used in interpolation (2M, 3M, 6M). "
            "Takeaway: these rates provide the financing leg against which implied repo is compared."
        ),
        label="table:ois_input_summary",
    )
    write_table_pair(
        table_df=ctd_coverage,
        tabular_filename="ctd_bond_input_coverage_tabular.tex",
        table_filename="ctd_bond_input_coverage_table.tex",
        caption=(
            "Coverage of CTD-bond inputs used in implied-repo construction. "
            "Takeaway: bond-side pricing and coupon-timing fields are broadly available in the sample."
        ),
        label="table:ctd_bond_input_coverage",
    )
    write_table_pair(
        table_df=holding_summary,
        tabular_filename="holding_period_summary_tabular.tex",
        table_filename="holding_period_summary_table.tex",
        caption=(
            "Holding-period distribution used to interpolate OIS for each tenor. "
            "Takeaway: tenor-specific holding horizons differ and therefore map into different interpolated OIS rates."
        ),
        label="table:holding_period_summary",
    )
    write_table_pair(
        table_df=component_summary,
        tabular_filename="spread_component_summary_tabular.tex",
        table_filename="spread_component_summary_table.tex",
        caption=(
            "Component decomposition summary by tenor: implied repo, interpolated OIS, and spread. "
            "Takeaway: spread behavior is jointly determined by both legs and not by one component alone."
        ),
        label="table:spread_component_summary",
    )

    build_underlying_futures_prices_chart(bloomberg)
    build_ois_input_chart(ois_inputs)
    build_holding_period_chart(holding_period_days)
    build_implied_repo_vs_ois_chart(implied_repo, interpolated_ois_bps)

    outputs = [
        "underlying_summary_stats_tabular.tex",
        "underlying_summary_stats_table.tex",
        "futures_input_coverage_tabular.tex",
        "futures_input_coverage_table.tex",
        "ois_input_summary_tabular.tex",
        "ois_input_summary_table.tex",
        "ctd_bond_input_coverage_tabular.tex",
        "ctd_bond_input_coverage_table.tex",
        "holding_period_summary_tabular.tex",
        "holding_period_summary_table.tex",
        "spread_component_summary_tabular.tex",
        "spread_component_summary_table.tex",
        "underlying_futures_prices_by_tenor.png",
        "underlying_futures_prices_by_tenor.html",
        "underlying_futures_prices_figure.tex",
        "ois_input_rates.png",
        "ois_input_rates.html",
        "ois_input_rates_figure.tex",
        "holding_period_days_by_tenor.png",
        "holding_period_days_by_tenor.html",
        "holding_period_days_by_tenor_figure.tex",
        "implied_repo_vs_interpolated_ois_by_tenor.png",
        "implied_repo_vs_interpolated_ois_by_tenor.html",
        "implied_repo_vs_interpolated_ois_by_tenor_figure.tex",
    ]
    for output in outputs:
        print(f"Wrote {OUTPUT_DIR / output}")


if __name__ == "__main__":
    main()
