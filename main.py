import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import plotly.graph_objects as go

from clients import HyperliquidClient
from clients import DerivClient
from clients import BinanceClient

INSTRUMENT_MAPPING = {
    "BTC": {
        "hyperliquid": "BTC",
        "derive": "BTC-PERP",
        "binance": "BTCUSDT",
    }
}


@st.cache_data(show_spinner=True)
def load_raw_funding_data(coin: str, days: int = 7):
    """
    Load raw funding data from Hyperliquid, Deriv, and Binance for a given coin.
    """
    if coin not in INSTRUMENT_MAPPING:
        raise ValueError(f"Unsupported coin: {coin}")

    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)
    mapping = INSTRUMENT_MAPPING[coin]

    hl_client = HyperliquidClient()
    derive_client = DerivClient()
    binance_client = BinanceClient()

    df_hl = hl_client.get_funding_history(
        coin=mapping["hyperliquid"],
        start_time=start,
        end_time=now,
    )

    df_derive = derive_client.get_funding_history(
        instrument_name=mapping["derive"],
        start_time=start,
        end_time=now,
    )

    df_binance = binance_client.get_funding_history(
        symbol=mapping["binance"],
        start_time=start,
        end_time=now,
    )

    return df_hl, df_derive, df_binance


def prepare_merged_timeseries(
    df_hl: pd.DataFrame,
    df_derive: pd.DataFrame,
    df_binance: pd.DataFrame,
    freq: str = "1h",
) -> pd.DataFrame:
    """
    Take raw dataframes from each venue and build a unified time series
    with hourly (or other) resampling and spreads in bps.
    """
    frames = []

    # Hyperliquid
    if df_hl is not None and not df_hl.empty:
        hl = df_hl.copy()
        hl["time"] = pd.to_datetime(hl["time"], utc=True)
        hl = (
            hl[["time", "funding_rate"]]
            .set_index("time")
            .sort_index()
            .resample(freq)
            .mean()
            .rename(columns={"funding_rate": "funding_hl"})
        )
        frames.append(hl)

    # Deriv
    if df_derive is not None and not df_derive.empty:
        dv = df_derive.copy()
        dv["time"] = pd.to_datetime(dv["time"], utc=True)
        dv = (
            dv[["time", "funding_rate"]]
            .set_index("time")
            .sort_index()
            .resample(freq)
            .mean()
            .rename(columns={"funding_rate": "funding_derive"})
        )
        frames.append(dv)

    # Binance
    if df_binance is not None and not df_binance.empty:
        bn = df_binance.copy()
        bn["funding_time"] = pd.to_datetime(bn["funding_time"], utc=True)
        bn = (
            bn[["funding_time", "funding_rate"]]
            .rename(columns={"funding_time": "time"})
            .set_index("time")
            .sort_index()
            .resample(freq)
            .ffill()
            .rename(columns={"funding_rate": "funding_binance"})
        )
        frames.append(bn)

    if not frames:
        return pd.DataFrame()

    merged = frames[0]
    for f in frames[1:]:
        merged = merged.join(f, how="outer")

    merged = merged.sort_index()
    merged = merged.reset_index().rename(columns={"index": "time"})

    # Funding in bps
    for col in ["funding_hl", "funding_derive", "funding_binance"]:
        if col in merged.columns:
            merged[f"{col}_bps"] = merged[col] * 10000.0

    # Spreads in bps
    if {"funding_hl_bps", "funding_derive_bps"}.issubset(merged.columns):
        merged["spread_hl_derive_bps"] = (
            merged["funding_hl_bps"] - merged["funding_derive_bps"]
        )

    if {"funding_hl_bps", "funding_binance_bps"}.issubset(merged.columns):
        merged["spread_hl_binance_bps"] = (
            merged["funding_hl_bps"] - merged["funding_binance_bps"]
        )

    if {"funding_derive_bps", "funding_binance_bps"}.issubset(merged.columns):
        merged["spread_derive_binance_bps"] = (
            merged["funding_derive_bps"] - merged["funding_binance_bps"]
        )

    return merged


def render_hl_derive_tab(df: pd.DataFrame) -> None:
    """
    Hyperliquid vs Deriv tab.
    """
    required_cols = ["time", "funding_hl_bps", "funding_derive_bps", "spread_hl_derive_bps"]
    if not set(required_cols).issubset(df.columns):
        st.warning("Not enough data to compare Hyperliquid and Deriv.")
        return

    pair = df.dropna(subset=["funding_hl_bps", "funding_derive_bps"]).copy()
    if pair.empty:
        st.warning("No overlapping funding data for Hyperliquid and Deriv.")
        return

    avg_hl = pair["funding_hl_bps"].mean()
    avg_derive = pair["funding_derive_bps"].mean()
    avg_spread = pair["spread_hl_derive_bps"].mean()
    max_pos_spread = pair["spread_hl_derive_bps"].max()
    max_neg_spread = pair["spread_hl_derive_bps"].min()
    positive_share = (pair["spread_hl_derive_bps"] > 0).mean() * 100.0

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Avg HL funding (bps)", f"{avg_hl:.3f}")
    col2.metric("Avg Deriv funding (bps)", f"{avg_derive:.3f}")
    col3.metric("Avg spread HL - Deriv (bps)", f"{avg_spread:.3f}")
    col4.metric("Max spread (positive, bps)", f"{max_pos_spread:.3f}")
    col5.metric("Share spread > 0 (%)", f"{positive_share:.1f}")

    st.markdown("---")

    c1, c2 = st.columns(2)

    with c1:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=pair["time"],
                y=pair["funding_hl_bps"],
                mode="lines",
                name="Hyperliquid",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=pair["time"],
                y=pair["funding_derive_bps"],
                mode="lines",
                name="Deriv",
            )
        )
        fig.update_layout(
            title="Funding rates (bps)",
            xaxis_title="Time",
            yaxis_title="Funding rate (bps)",
            hovermode="x unified",
            template="plotly_white",
            height=400,
        )
        st.plotly_chart(fig, width="stretch")

    with c2:
        fig_spread = go.Figure()
        fig_spread.add_trace(
            go.Scatter(
                x=pair["time"],
                y=pair["spread_hl_derive_bps"],
                mode="lines",
                name="HL - Deriv",
            )
        )
        fig_spread.add_hline(y=0.0, line_width=1, line_dash="dash", line_color="gray")
        fig_spread.update_layout(
            title="Funding spread HL - Deriv (bps)",
            xaxis_title="Time",
            yaxis_title="Spread (bps)",
            hovermode="x unified",
            template="plotly_white",
            height=400,
        )
        st.plotly_chart(fig_spread, width="stretch")

    st.markdown("---")
    st.subheader("Top spread opportunities (by absolute value)")

    pair["abs_spread"] = pair["spread_hl_derive_bps"].abs()
    top = (
        pair[["time", "funding_hl_bps", "funding_derive_bps", "spread_hl_derive_bps", "abs_spread"]]
        .sort_values("abs_spread", ascending=False)
        .head(30)
        .reset_index(drop=True)
    )

    top.rename(
        columns={
            "time": "Time",
            "funding_hl_bps": "HL funding (bps)",
            "funding_derive_bps": "Deriv funding (bps)",
            "spread_hl_derive_bps": "Spread HL - Deriv (bps)",
            "abs_spread": "Abs spread (bps)",
        },
        inplace=True,
    )

    st.dataframe(top, width="stretch")


def render_all_exchanges_tab(df: pd.DataFrame) -> None:
    """
    All exchanges tab: all funding series and all spreads.
    """
    has_hl = "funding_hl_bps" in df.columns
    has_derive = "funding_derive_bps" in df.columns
    has_binance = "funding_binance_bps" in df.columns

    if not (has_hl or has_derive or has_binance):
        st.warning("No funding data available.")
        return

    st.subheader("Funding rates by exchange (bps)")

    fig = go.Figure()

    if has_hl:
        fig.add_trace(
            go.Scatter(
                x=df["time"],
                y=df["funding_hl_bps"],
                mode="lines",
                name="Hyperliquid",
            )
        )
    if has_derive:
        fig.add_trace(
            go.Scatter(
                x=df["time"],
                y=df["funding_derive_bps"],
                mode="lines",
                name="Deriv",
            )
        )
    if has_binance:
        fig.add_trace(
            go.Scatter(
                x=df["time"],
                y=df["funding_binance_bps"],
                mode="lines",
                name="Binance",
            )
        )

    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Funding rate (bps)",
        hovermode="x unified",
        template="plotly_white",
        height=450,
    )

    st.plotly_chart(fig, width="stretch")

    st.markdown("---")
    st.subheader("Spreads between exchanges (bps)")

    fig_spreads = go.Figure()

    if "spread_hl_derive_bps" in df.columns:
        fig_spreads.add_trace(
            go.Scatter(
                x=df["time"],
                y=df["spread_hl_derive_bps"],
                mode="lines",
                name="HL - Deriv",
            )
        )
    if "spread_hl_binance_bps" in df.columns:
        fig_spreads.add_trace(
            go.Scatter(
                x=df["time"],
                y=df["spread_hl_binance_bps"],
                mode="lines",
                name="HL - Binance",
            )
        )
    if "spread_derive_binance_bps" in df.columns:
        fig_spreads.add_trace(
            go.Scatter(
                x=df["time"],
                y=df["spread_derive_binance_bps"],
                mode="lines",
                name="Deriv - Binance",
            )
        )

    fig_spreads.add_hline(y=0.0, line_width=1, line_dash="dash", line_color="gray")
    fig_spreads.update_layout(
        xaxis_title="Time",
        yaxis_title="Spread (bps)",
        hovermode="x unified",
        template="plotly_white",
        height=450,
    )

    st.plotly_chart(fig_spreads, width="stretch")

    st.markdown("---")
    st.subheader("Summary statistics")

    rows = []

    if has_hl:
        rows.append(
            {
                "Exchange": "Hyperliquid",
                "Avg funding (bps)": df["funding_hl_bps"].mean(),
                "Std funding (bps)": df["funding_hl_bps"].std(),
            }
        )
    if has_derive:
        rows.append(
            {
                "Exchange": "Deriv",
                "Avg funding (bps)": df["funding_derive_bps"].mean(),
                "Std funding (bps)": df["funding_derive_bps"].std(),
            }
        )
    if has_binance:
        rows.append(
            {
                "Exchange": "Binance",
                "Avg funding (bps)": df["funding_binance_bps"].mean(),
                "Std funding (bps)": df["funding_binance_bps"].std(),
            }
        )

    stats_df = pd.DataFrame(rows)
    st.dataframe(stats_df, width="stretch")


def render_raw_data_tab(df: pd.DataFrame) -> None:
    """
    Raw data tab for debugging and exploration.
    """
    st.subheader("Merged funding and spread data")
    st.dataframe(df, width="stretch")


def main() -> None:
    st.set_page_config(
        page_title="Funding Arbitrage Dashboard",
        page_icon=":bar_chart:",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("Funding Rate Arbitrage Dashboard")
    st.caption("Funding rate arbitrage across Hyperliquid, Deriv, and Binance.")

    with st.sidebar:
        st.header("Controls")
        coin = st.selectbox("Instrument", ["BTC"], index=0)
        lookback_days = st.slider(
            "Lookback (days)",
            min_value=3,
            max_value=30,
            value=7,
        )
        freq = st.selectbox(
            "Resample frequency",
            options=["1h", "4h", "8h"],
            index=0,
            help="Resampling frequency for time series aggregation.",
        )

    df_hl, df_derive, df_binance = load_raw_funding_data(coin, lookback_days)
    merged = prepare_merged_timeseries(df_hl, df_derive, df_binance, freq=freq)

    if merged.empty:
        st.warning("No data returned for the selected settings.")
        return

    tab_pair, tab_all, tab_raw = st.tabs(
        ["Hyperliquid vs Deriv", "All exchanges", "Raw data"]
    )

    with tab_pair:
        render_hl_derive_tab(merged)

    with tab_all:
        render_all_exchanges_tab(merged)

    with tab_raw:
        render_raw_data_tab(merged)


if __name__ == "__main__":
    main()
