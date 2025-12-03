import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta

from clients import BinanceClient, HyperliquidClient, DerivClient


def inject_css() -> None:
    st.markdown(
        """
    <style>
    body, .stApp, [data-testid="stAppViewContainer"], .main {
        background-color: #020617 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Inter", system-ui, sans-serif;
    }

    [data-testid="block-container"] {
        max-width: 1360px;
        padding-top: 24px;
        padding-bottom: 40px;
    }

    header h1 {
        font-size: 30px;
        margin-bottom: 4px;
        font-weight: 700;
        color: #f9fafb;
    }

    .header-subtitle {
        font-size: 13px;
        color: #9ca3af;
        margin-top: 0px;
        margin-bottom: 18px;
    }

    .alert-info {
        padding: 10px 14px;
        background-color: #0f172a;
        border-radius: 6px;
        border: 1px solid #1f2937;
        color: #e5e7eb;
        font-size: 13px;
        margin-bottom: 18px;
    }

    .controls-row {
        display: grid;
        grid-template-columns: 1.1fr 1.1fr 1.1fr auto;
        gap: 12px;
        margin-bottom: 18px;
    }

    .controls-row .stNumberInput > label,
    .controls-row .stSelectbox > label {
        font-size: 11px !important;
        text-transform: uppercase;
        color: #9ca3af;
        letter-spacing: 0.04em;
        font-weight: 600;
    }

    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 18px;
    }

    .metric-card {
        background: #020617;
        border-radius: 8px;
        border: 1px solid #1f2937;
        padding: 14px 18px;
        color: #e5e7eb;
    }

    .metric-label {
        font-size: 12px;
        font-weight: 600;
        color: #9ca3af;
        margin-bottom: 4px;
    }

    .metric-value {
        font-size: 20px;
        font-weight: 700;
        margin-top: 2px;
    }

    .metric-positive {
        color: #22c55e;
    }

    .metric-negative {
        color: #f97373;
    }

    .metric-sublabel {
        font-size: 11px;
        color: #6b7280;
        margin-top: 2px;
    }

    .table-wrapper {
        margin-top: 10px;
        background: #020617;
        border-radius: 8px;
        border: 1px solid #1f2937;
        padding: 0;
    }

    .table-header-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 14px 18px;
        border-bottom: 1px solid #1f2937;
    }

    .table-title {
        font-size: 14px;
        font-weight: 600;
        color: #e5e7eb;
    }

    .filter-chip {
        padding: 4px 11px;
        background: #020617;
        border-radius: 16px;
        border: 1px solid #374151;
        color: #9ca3af;
        font-size: 11px;
        cursor: pointer;
        margin-left: 6px;
    }

    .filter-chip.active {
        background: #2563eb;
        border-color: #2563eb;
        color: #f9fafb;
    }

    .timestamp {
        text-align: right;
        font-size: 11px;
        color: #6b7280;
        margin-top: 6px;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def fetch_funding() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    binance = BinanceClient()
    hl = HyperliquidClient()
    dv = DerivClient()

    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=8)

    df_bin = binance.get_funding_history("BTCUSDT", start, now)
    df_hl = hl.get_funding_history("BTC", start, now)
    df_dv = dv.get_funding_history("BTC-PERP", start, now)

    return df_bin, df_hl, df_dv


def compute_best(
    df_bin: pd.DataFrame,
    df_hl: pd.DataFrame,
    df_dv: pd.DataFrame,
):
    latest: dict[str, float] = {}

    if not df_bin.empty:
        latest["Binance"] = float(df_bin["funding_rate"].iloc[-1])
    if not df_hl.empty:
        latest["Hyperliquid"] = float(df_hl["funding_rate"].iloc[-1])
    if not df_dv.empty:
        latest["Deriv"] = float(df_dv["funding_rate"].iloc[-1])

    if not latest:
        return None, None, 0.0, 0.0, latest

    ranked = sorted(latest.items(), key=lambda x: x[1], reverse=True)
    long_ex, long_rate = ranked[0]
    short_ex, short_rate = ranked[-1]

    spread = long_rate - short_rate
    apy = spread * 3.0 * 365.0 * 100.0

    return long_ex, short_ex, spread, apy, latest


def compute_opportunity_stats(
    df_bin: pd.DataFrame,
    df_hl: pd.DataFrame,
    df_dv: pd.DataFrame,
    min_spread_pct: float,
) -> tuple[int, float, float]:
    def make_series(df: pd.DataFrame) -> pd.Series | None:
        if df is None or df.empty:
            return None
        if "time" in df.columns:
            tcol = "time"
        elif "funding_time" in df.columns:
            tcol = "funding_time"
        else:
            return None
        s = df[[tcol, "funding_rate"]].copy()
        s[tcol] = pd.to_datetime(s[tcol], utc=True)
        s = s.set_index(tcol).sort_index()["funding_rate"]
        return s

    s_bin = make_series(df_bin)
    s_hl = make_series(df_hl)
    s_dv = make_series(df_dv)

    series_dict: dict[str, pd.Series] = {}
    if s_bin is not None:
        series_dict["binance"] = s_bin
    if s_hl is not None:
        series_dict["hyperliquid"] = s_hl
    if s_dv is not None:
        series_dict["deriv"] = s_dv

    if len(series_dict) < 2:
        return 0, 0.0, 0.0

    merged = pd.concat(series_dict.values(), axis=1, join="inner")
    if merged.empty:
        return 0, 0.0, 0.0

    spreads = merged.max(axis=1) - merged.min(axis=1)
    spreads_pct = spreads * 100.0

    opportunities_found = int((spreads_pct >= min_spread_pct).sum())
    avg_spread_pct = float(spreads_pct.mean())
    max_spread_pct = float(spreads_pct.max())

    return opportunities_found, avg_spread_pct, max_spread_pct


def main() -> None:
    st.set_page_config(
        page_title="Funding Rate Arbitrage Monitor",
        layout="wide",
    )

    inject_css()

    st.markdown(
        """
        <header>
            <h1>Funding Rate Arbitrage Monitor</h1>
            <p class="header-subtitle">
                Real-time funding rate comparison between Binance, Hyperliquid and Deriv perpetuals
            </p>
        </header>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="alert-info">
            Info: This dashboard shows live BTC funding rates and the best long/short combo across Binance, Hyperliquid and Deriv.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------- controls ----------
    st.markdown('<div class="controls-row">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])

    with c1:
        min_spread_pct = st.number_input(
            "Minimum Spread (%)",
            min_value=0.0,
            value=0.05,
            step=0.01,
        )

    with c2:
        refresh_interval = st.number_input(
            "Refresh Interval (s)",
            min_value=1,
            max_value=60,
            value=5,
            step=1,
        )

    with c3:
        sort_by = st.selectbox(
            "Sort By",
            ["Spread (Highest)", "Binance Rate", "Hyperliquid Rate", "Deriv Rate"],
            index=0,
        )

    with c4:
        # две кнопки в одной строке
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            refresh_clicked = st.button("Refresh Now", use_container_width=True)
        with col_btn2:
            export_clicked = st.button("Export CSV", type="secondary", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # st.markdown(
    #     f"<meta http-equiv='refresh' content='{int(refresh_interval)}'>",
    #     unsafe_allow_html=True,
    # )

    # ---------- data ----------
    if refresh_clicked or "data_cache" not in st.session_state:
        df_bin, df_hl, df_dv = fetch_funding()
        st.session_state["data_cache"] = (df_bin, df_hl, df_dv)
        st.session_state["last_updated"] = datetime.now(timezone.utc)
    else:
        df_bin, df_hl, df_dv = st.session_state["data_cache"]

    if export_clicked:
        out = []
        for venue, df in [
            ("Binance", df_bin),
            ("Hyperliquid", df_hl),
            ("Deriv", df_dv),
        ]:
            if df.empty:
                continue
            if "time" in df.columns:
                tcol = "time"
            elif "funding_time" in df.columns:
                tcol = "funding_time"
            else:
                continue
            tmp = df[[tcol, "funding_rate"]].copy()
            tmp.rename(columns={tcol: "time"}, inplace=True)
            tmp["venue"] = venue
            out.append(tmp)
        if out:
            all_df = pd.concat(out, ignore_index=True)
            csv = all_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download CSV",
                data=csv,
                file_name="funding_rates_btc.csv",
                mime="text/csv",
            )

    long_ex, short_ex, spread, apy, latest = compute_best(df_bin, df_hl, df_dv)
    opportunities_found, avg_spread_pct, max_spread_pct = compute_opportunity_stats(
        df_bin, df_hl, df_dv, min_spread_pct
    )

    ts = st.session_state.get("last_updated", datetime.now(timezone.utc))
    ts_str = ts.strftime("%Y-%m-%d %H:%M:%S UTC")

    spread_pct = spread * 100.0
    spread_str = f"{spread_pct:.4f}%"
    apy_str = f"{apy:.1f}%"

    best_long = long_ex or "N/A"
    best_short = short_ex or "N/A"

    # ---------- metrics ----------
    metrics_html = f"""
    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-label">Opportunities Found</div>
        <div class="metric-value">{opportunities_found}</div>
        <div class="metric-sublabel">
            Spread greater or equal to {min_spread_pct:.2f}% (all timestamps)
        </div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Avg Spread</div>
        <div class="metric-value metric-positive">{avg_spread_pct:.4f}%</div>
        <div class="metric-sublabel">Average spread over lookback window</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Max Spread</div>
        <div class="metric-value metric-positive">{max_spread_pct:.4f}%</div>
        <div class="metric-sublabel">Maximum observed spread</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Last Updated</div>
        <div class="metric-value">{ts_str}</div>
        <div class="metric-sublabel">UTC time of last data fetch</div>
      </div>
    </div>
    """
    st.markdown(metrics_html, unsafe_allow_html=True)

    # ---------- table ----------
    st.markdown(
        """
        <div class="table-wrapper">
          <div class="table-header-bar">
            <div class="table-title">Arbitrage Opportunities</div>
            <div>
              <span class="filter-chip active">All</span>
              <span class="filter-chip">Profitable Only</span>
              <span class="filter-chip">High Spread</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    def fmt_rate(x: float | None) -> str:
        if x is None:
            return "-"
        return f"{x * 100.0:.4f}%"

    bin_rate = latest.get("Binance")
    hl_rate = latest.get("Hyperliquid")
    dv_rate = latest.get("Deriv")

    row = {
        "Asset": "BTC",
        "Long / Short": f"Long {best_long} / Short {best_short}",
        "Binance": fmt_rate(bin_rate),
        "Hyperliquid": fmt_rate(hl_rate),
        "Deriv": fmt_rate(dv_rate),
        "Spread (%)": spread_str,
        "Annual APY (%)": apy_str,
    }

    table_df = pd.DataFrame([row])

    st.dataframe(
        table_df,
        hide_index=True,
        width="stretch",
    )

    # ---------- timestamp ----------
    st.markdown(
        f"<div class='timestamp'>Last updated: {ts_str}</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
