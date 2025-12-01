"""
BitFrost Revenue Forecasting Engine
Mathematical revenue modeling with scenario analysis
Production-ready Streamlit application
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import io

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

DAYS_PER_YEAR = 365
MONTHS_PER_YEAR = 12
BPS_PER_UNIT = 10000

# Scenario defaults
SCENARIOS = {
    "Bear Case": {
        "daily_volume_usd": 500_000_000,
        "internal_match_ratio": 0.30,
        "clearing_fee_bps": 1.5,
        "netting_fee_bps": 0.5,
        "hl_funding_rate_apr": 0.02,
        "arch_borrow_rate_apr": 0.03,
        "friction_cost_bps": 1.5,
        "equity_usd": 50_000_000,
        "leverage": 2.0,
        "monthly_liquidations_usd": 10_000_000,
        "liquidation_fee_pct": 0.3,
        "daily_hedge_notional_usd": 50_000_000,
        "hedge_efficiency_bps_per_day": 0.2,
    },
    "Base Case": {
        "daily_volume_usd": 2_000_000_000,
        "internal_match_ratio": 0.50,
        "clearing_fee_bps": 1.5,
        "netting_fee_bps": 0.5,
        "hl_funding_rate_apr": 0.08,
        "arch_borrow_rate_apr": 0.025,
        "friction_cost_bps": 1.2,
        "equity_usd": 100_000_000,
        "leverage": 8.0,
        "monthly_liquidations_usd": 50_000_000,
        "liquidation_fee_pct": 0.4,
        "daily_hedge_notional_usd": 200_000_000,
        "hedge_efficiency_bps_per_day": 0.5,
    },
    "Bull Case": {
        "daily_volume_usd": 5_000_000_000,
        "internal_match_ratio": 0.65,
        "clearing_fee_bps": 1.5,
        "netting_fee_bps": 0.5,
        "hl_funding_rate_apr": 0.25,
        "arch_borrow_rate_apr": 0.02,
        "friction_cost_bps": 0.8,
        "equity_usd": 200_000_000,
        "leverage": 12.0,
        "monthly_liquidations_usd": 150_000_000,
        "liquidation_fee_pct": 0.5,
        "daily_hedge_notional_usd": 500_000_000,
        "hedge_efficiency_bps_per_day": 1.0,
    },
}

# ============================================================================
# REVENUE CALCULATOR ENGINE
# ============================================================================

class RevenueCalculator:
    """Mathematical revenue modeling engine for BitFrost."""

    def __init__(self):
        self.days_per_year = DAYS_PER_YEAR
        self.months_per_year = MONTHS_PER_YEAR
        self.bps_per_unit = BPS_PER_UNIT

    def calculate(self, params):
        """
        Calculate all revenue streams based on parameters.

        Mathematical Model:
        R_total = R_clearing + R_funding + R_liq + R_hedge

        Where:
        - R_clearing = 365 * V_d * α * (f_c + f_n)
        - R_funding = (f_H - r_ℓ - κ) * L * E
        - R_liq = 12 * L_m * φ
        - R_hedge = 365 * H_d * η
        """
        
        # Extract and normalize parameters
        V_d = params["daily_volume_usd"]
        alpha = params["internal_match_ratio"]
        f_c = params["clearing_fee_bps"] / self.bps_per_unit
        f_n = params["netting_fee_bps"] / self.bps_per_unit
        f_H = params["hl_funding_rate_apr"] / 100  # Convert APR to decimal
        r_l = params["arch_borrow_rate_apr"] / 100
        kappa = params["friction_cost_bps"] / self.bps_per_unit
        E = params["equity_usd"]
        L = params["leverage"]
        L_m = params["monthly_liquidations_usd"]
        phi = params["liquidation_fee_pct"] / 100
        H_d = params["daily_hedge_notional_usd"]
        eta = params["hedge_efficiency_bps_per_day"] / self.bps_per_unit

        # ======== REVENUE STREAM 1: Clearing & Internal Matching ========
        # Formula: R_clear = 365 * V_d * α * (f_c + f_n)
        R_clear = self.days_per_year * V_d * alpha * (f_c + f_n)

        # ======== REVENUE STREAM 2: Funding-Rate Arbitrage ========
        # Net spread: s = f_H - r_ℓ - κ
        # Deployed notional: N = L * E
        # Revenue: R_funding = s * N (can be negative in bear case)
        s = f_H - r_l - kappa
        N = L * E
        R_funding = s * N

        # ======== REVENUE STREAM 3: Liquidation Engine ========
        # Formula: R_liq = 12 * L_m * φ
        R_liq = self.months_per_year * L_m * phi

        # ======== REVENUE STREAM 4: Hedge Routing ========
        # Formula: R_hedge = 365 * H_d * η
        R_hedge = self.days_per_year * H_d * eta

        # ======== TOTAL & DERIVED METRICS ========
        R_total = R_clear + R_funding + R_liq + R_hedge

        # Derived calculations
        funding_roe = s * L * 100  # As percentage
        monthly_avg = R_total / self.months_per_year
        daily_avg = R_total / self.days_per_year
        clearing_daily = R_clear / self.days_per_year
        hedge_daily = R_hedge / self.days_per_year

        return {
            "total": R_total,
            "clearing": R_clear,
            "funding": R_funding,
            "liquidations": R_liq,
            "hedging": R_hedge,
            "monthly_avg": monthly_avg,
            "daily_avg": daily_avg,
            "funding_spread": s,
            "deployed_notional": N,
            "funding_roe": funding_roe,
            "clearing_daily": clearing_daily,
            "hedge_daily": hedge_daily,
        }

    def generate_monthly_forecast(self, params, months=12):
        """Generate month-by-month revenue forecast."""
        monthly_data = []
        result = self.calculate(params)
        
        for month in range(1, months + 1):
            monthly_data.append({
                "Month": month,
                "Clearing": result["clearing"] / self.days_per_year,
                "Funding": result["funding"] / self.days_per_year,
                "Liquidations": result["liquidations"] / self.days_per_year,
                "Hedging": result["hedging"] / self.days_per_year,
                "Total": result["daily_avg"],
            })
        
        return pd.DataFrame(monthly_data)


# ============================================================================
# UI COMPONENTS & FORMATTING
# ============================================================================

def format_currency(value):
    """Format value as currency."""
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    elif value >= 1_000:
        return f"${value / 1_000:.2f}K"
    else:
        return f"${value:.2f}"


def format_percentage(value):
    """Format value as percentage."""
    return f"{value:.2f}%"


def format_basis_points(value):
    """Format value as basis points."""
    return f"{value:.1f} bps"


def create_revenue_pie_chart(result):
    """Create revenue composition pie chart."""
    labels = ["Clearing", "Funding Arb", "Liquidations", "Hedging"]
    values = [
        result["clearing"],
        max(0, result["funding"]),  # Don't show negative
        result["liquidations"],
        result["hedging"],
    ]
    colors = ["#208480", "#32b8c6", "#f38ba8", "#fab387"]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                marker=dict(colors=colors),
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>%{value:$,.0f}<br>%{percent}<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        title="Revenue Composition by Stream",
        template="plotly_white",
        height=400,
    )
    return fig


def create_monthly_forecast_chart(df):
    """Create monthly revenue forecast stacked bar chart."""
    fig = go.Figure()

    streams = ["Clearing", "Funding", "Liquidations", "Hedging"]
    colors = ["#208480", "#32b8c6", "#f38ba8", "#fab387"]

    for stream, color in zip(streams, colors):
        fig.add_trace(
            go.Bar(
                x=df["Month"],
                y=df[stream],
                name=stream,
                marker=dict(color=color),
                hovertemplate="<b>%{fullData.name}</b><br>Month %{x}<br>%{y:$,.0f}<extra></extra>",
            )
        )

    fig.update_layout(
        title="Monthly Revenue Forecast (12 Months)",
        xaxis_title="Month",
        yaxis_title="Daily Revenue (USD)",
        barmode="stack",
        template="plotly_white",
        height=400,
        hovermode="x unified",
    )
    return fig


def create_metrics_cards(result):
    """Create metric cards display."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Annual Revenue",
            format_currency(result["total"]),
            delta=None,
        )

    with col2:
        st.metric(
            "Monthly Average",
            format_currency(result["monthly_avg"]),
            delta=None,
        )

    with col3:
        st.metric(
            "Funding ROE",
            format_percentage(result["funding_roe"]),
            delta=None,
        )

    with col4:
        st.metric(
            "Funding Spread",
            format_percentage(result["funding_spread"] * 100),
            delta=None,
        )


def create_parameter_section(scenario_name, scenario_params, key_prefix):
    """Create interactive parameter section for a scenario."""
    
    with st.expander("📊 Volumes & Fees", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            daily_volume = st.slider(
                "Daily Volume (USD)",
                min_value=100_000_000,
                max_value=10_000_000_000,
                value=int(scenario_params["daily_volume_usd"]),
                step=100_000_000,
                key=f"{key_prefix}_daily_volume",
                format="$%d",
            )
            internal_match_ratio = st.slider(
                "Internal Match Ratio",
                min_value=0.0,
                max_value=1.0,
                value=scenario_params["internal_match_ratio"],
                step=0.01,
                key=f"{key_prefix}_match_ratio",
            )
        with col2:
            clearing_fee = st.slider(
                "Clearing Fee (bps)",
                min_value=0.0,
                max_value=5.0,
                value=scenario_params["clearing_fee_bps"],
                step=0.1,
                key=f"{key_prefix}_clearing_fee",
            )
            netting_fee = st.slider(
                "Netting Fee (bps)",
                min_value=0.0,
                max_value=2.0,
                value=scenario_params["netting_fee_bps"],
                step=0.1,
                key=f"{key_prefix}_netting_fee",
            )

    with st.expander("⚡ Funding Arbitrage", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            hl_funding_rate = st.slider(
                "HL Funding Rate (APR)",
                min_value=-0.1,
                max_value=0.5,
                value=scenario_params["hl_funding_rate_apr"],
                step=0.01,
                key=f"{key_prefix}_hl_funding",
                format="%.2f",
            )
            arch_borrow_rate = st.slider(
                "Arch Borrow Rate (APR)",
                min_value=0.0,
                max_value=0.1,
                value=scenario_params["arch_borrow_rate_apr"],
                step=0.001,
                key=f"{key_prefix}_arch_borrow",
                format="%.3f",
            )
        with col2:
            friction_cost = st.slider(
                "Friction Cost (bps)",
                min_value=0.0,
                max_value=5.0,
                value=scenario_params["friction_cost_bps"],
                step=0.1,
                key=f"{key_prefix}_friction",
            )
            equity = st.slider(
                "Equity Deployed (USD)",
                min_value=10_000_000,
                max_value=500_000_000,
                value=int(scenario_params["equity_usd"]),
                step=10_000_000,
                key=f"{key_prefix}_equity",
                format="$%d",
            )
        col3, col4 = st.columns(2)
        with col3:
            leverage = st.slider(
                "Leverage (L)",
                min_value=1.0,
                max_value=20.0,
                value=scenario_params["leverage"],
                step=0.5,
                key=f"{key_prefix}_leverage",
            )

    with st.expander("💀 Liquidations", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            monthly_liquidations = st.slider(
                "Monthly Liquidations Notional (USD)",
                min_value=1_000_000,
                max_value=500_000_000,
                value=int(scenario_params["monthly_liquidations_usd"]),
                step=5_000_000,
                key=f"{key_prefix}_monthly_liq",
                format="$%d",
            )
        with col2:
            liquidation_fee = st.slider(
                "Liquidation Fee (%)",
                min_value=0.1,
                max_value=1.0,
                value=scenario_params["liquidation_fee_pct"],
                step=0.05,
                key=f"{key_prefix}_liq_fee",
            )

    with st.expander("🔀 Hedging", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            daily_hedge = st.slider(
                "Daily Hedge Notional (USD)",
                min_value=10_000_000,
                max_value=1_000_000_000,
                value=int(scenario_params["daily_hedge_notional_usd"]),
                step=10_000_000,
                key=f"{key_prefix}_daily_hedge",
                format="$%d",
            )
        with col2:
            hedge_efficiency = st.slider(
                "Hedge Efficiency (bps/day)",
                min_value=0.0,
                max_value=2.0,
                value=scenario_params["hedge_efficiency_bps_per_day"],
                step=0.05,
                key=f"{key_prefix}_hedge_efficiency",
            )

    # Return updated parameters
    return {
        "daily_volume_usd": daily_volume,
        "internal_match_ratio": internal_match_ratio,
        "clearing_fee_bps": clearing_fee,
        "netting_fee_bps": netting_fee,
        "hl_funding_rate_apr": hl_funding_rate,
        "arch_borrow_rate_apr": arch_borrow_rate,
        "friction_cost_bps": friction_cost,
        "equity_usd": equity,
        "leverage": leverage,
        "monthly_liquidations_usd": monthly_liquidations,
        "liquidation_fee_pct": liquidation_fee,
        "daily_hedge_notional_usd": daily_hedge,
        "hedge_efficiency_bps_per_day": hedge_efficiency,
    }


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main Streamlit application."""
    
    # Page configuration
    st.set_page_config(
        page_title="BitFrost Revenue Engine",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom CSS
    st.markdown(
        """
        <style>
        .main {
            padding: 2rem;
        }
        .metric-card {
            background-color: #f0f2f6;
            padding: 1.5rem;
            border-radius: 0.5rem;
            text-align: center;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Header
    st.title("📊 BitFrost Revenue Forecasting Engine")
    st.markdown(
        "Mathematical revenue modeling with scenario analysis | "
        "Production-grade financial forecasting system"
    )
    st.divider()

    # Initialize calculator
    calculator = RevenueCalculator()

    # Scenario selection tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        ["🐻 Bear Case", "📈 Base Case", "🚀 Bull Case", "📋 Comparison"]
    )

    # ========== BEAR CASE ==========
    with tab1:
        st.subheader("Bear Case Scenario")
        st.markdown(
            "**Low volume, negative funding spread, minimal leverage**"
        )

        params_bear = create_parameter_section(
            "Bear Case",
            SCENARIOS["Bear Case"],
            "bear",
        )

        st.divider()

        # Calculate results
        result_bear = calculator.calculate(params_bear)

        # Display metrics
        create_metrics_cards(result_bear)

        st.divider()

        # Charts
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(
                create_revenue_pie_chart(result_bear),
                use_container_width=True,
            )
        with col2:
            forecast_df = calculator.generate_monthly_forecast(params_bear)
            st.plotly_chart(
                create_monthly_forecast_chart(forecast_df),
                use_container_width=True,
            )

        # Detailed breakdown
        st.divider()
        st.subheader("Revenue Stream Breakdown")
        breakdown_bear = pd.DataFrame({
            "Revenue Stream": ["Clearing", "Funding Arb", "Liquidations", "Hedging", "TOTAL"],
            "Annual (USD)": [
                result_bear["clearing"],
                result_bear["funding"],
                result_bear["liquidations"],
                result_bear["hedging"],
                result_bear["total"],
            ],
            "Daily Avg (USD)": [
                result_bear["clearing"] / DAYS_PER_YEAR,
                result_bear["funding"] / DAYS_PER_YEAR,
                result_bear["liquidations"] / DAYS_PER_YEAR,
                result_bear["hedging"] / DAYS_PER_YEAR,
                result_bear["daily_avg"],
            ],
            "% of Total": [
                (result_bear["clearing"] / result_bear["total"] * 100) if result_bear["total"] > 0 else 0,
                (result_bear["funding"] / result_bear["total"] * 100) if result_bear["total"] > 0 else 0,
                (result_bear["liquidations"] / result_bear["total"] * 100) if result_bear["total"] > 0 else 0,
                (result_bear["hedging"] / result_bear["total"] * 100) if result_bear["total"] > 0 else 0,
                100.0,
            ],
        })
        st.dataframe(breakdown_bear, use_container_width=True, hide_index=True)

    # ========== BASE CASE ==========
    with tab2:
        st.subheader("Base Case Scenario")
        st.markdown(
            "**Moderate volume, healthy funding spread, 8x leverage**"
        )

        params_base = create_parameter_section(
            "Base Case",
            SCENARIOS["Base Case"],
            "base",
        )

        st.divider()

        # Calculate results
        result_base = calculator.calculate(params_base)

        # Display metrics
        create_metrics_cards(result_base)

        st.divider()

        # Charts
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(
                create_revenue_pie_chart(result_base),
                use_container_width=True,
            )
        with col2:
            forecast_df = calculator.generate_monthly_forecast(params_base)
            st.plotly_chart(
                create_monthly_forecast_chart(forecast_df),
                use_container_width=True,
            )

        # Detailed breakdown
        st.divider()
        st.subheader("Revenue Stream Breakdown")
        breakdown_base = pd.DataFrame({
            "Revenue Stream": ["Clearing", "Funding Arb", "Liquidations", "Hedging", "TOTAL"],
            "Annual (USD)": [
                result_base["clearing"],
                result_base["funding"],
                result_base["liquidations"],
                result_base["hedging"],
                result_base["total"],
            ],
            "Daily Avg (USD)": [
                result_base["clearing"] / DAYS_PER_YEAR,
                result_base["funding"] / DAYS_PER_YEAR,
                result_base["liquidations"] / DAYS_PER_YEAR,
                result_base["hedging"] / DAYS_PER_YEAR,
                result_base["daily_avg"],
            ],
            "% of Total": [
                (result_base["clearing"] / result_base["total"] * 100) if result_base["total"] > 0 else 0,
                (result_base["funding"] / result_base["total"] * 100) if result_base["total"] > 0 else 0,
                (result_base["liquidations"] / result_base["total"] * 100) if result_base["total"] > 0 else 0,
                (result_base["hedging"] / result_base["total"] * 100) if result_base["total"] > 0 else 0,
                100.0,
            ],
        })
        st.dataframe(breakdown_base, use_container_width=True, hide_index=True)

    # ========== BULL CASE ==========
    with tab3:
        st.subheader("Bull Case Scenario")
        st.markdown(
            "**High volume, explosive funding spread, 12x unified margin leverage**"
        )

        params_bull = create_parameter_section(
            "Bull Case",
            SCENARIOS["Bull Case"],
            "bull",
        )

        st.divider()

        # Calculate results
        result_bull = calculator.calculate(params_bull)

        # Display metrics
        create_metrics_cards(result_bull)

        st.divider()

        # Charts
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(
                create_revenue_pie_chart(result_bull),
                use_container_width=True,
            )
        with col2:
            forecast_df = calculator.generate_monthly_forecast(params_bull)
            st.plotly_chart(
                create_monthly_forecast_chart(forecast_df),
                use_container_width=True,
            )

        # Detailed breakdown
        st.divider()
        st.subheader("Revenue Stream Breakdown")
        breakdown_bull = pd.DataFrame({
            "Revenue Stream": ["Clearing", "Funding Arb", "Liquidations", "Hedging", "TOTAL"],
            "Annual (USD)": [
                result_bull["clearing"],
                result_bull["funding"],
                result_bull["liquidations"],
                result_bull["hedging"],
                result_bull["total"],
            ],
            "Daily Avg (USD)": [
                result_bull["clearing"] / DAYS_PER_YEAR,
                result_bull["funding"] / DAYS_PER_YEAR,
                result_bull["liquidations"] / DAYS_PER_YEAR,
                result_bull["hedging"] / DAYS_PER_YEAR,
                result_bull["daily_avg"],
            ],
            "% of Total": [
                (result_bull["clearing"] / result_bull["total"] * 100) if result_bull["total"] > 0 else 0,
                (result_bull["funding"] / result_bull["total"] * 100) if result_bull["total"] > 0 else 0,
                (result_bull["liquidations"] / result_bull["total"] * 100) if result_bull["total"] > 0 else 0,
                (result_bull["hedging"] / result_bull["total"] * 100) if result_bull["total"] > 0 else 0,
                100.0,
            ],
        })
        st.dataframe(breakdown_bull, use_container_width=True, hide_index=True)

    # ========== COMPARISON ==========
    with tab4:
        st.subheader("Scenario Comparison")

        # Calculate all scenarios with defaults
        result_bear_default = calculator.calculate(SCENARIOS["Bear Case"])
        result_base_default = calculator.calculate(SCENARIOS["Base Case"])
        result_bull_default = calculator.calculate(SCENARIOS["Bull Case"])

        # Comparison table
        comparison_df = pd.DataFrame({
            "Metric": [
                "Daily Volume",
                "Annual Revenue",
                "Monthly Avg Revenue",
                "Daily Avg Revenue",
                "Funding Spread",
                "Funding ROE",
                "Deployed Notional",
                "Clearing %",
                "Funding %",
                "Liquidation %",
                "Hedging %",
            ],
            "Bear Case": [
                format_currency(SCENARIOS["Bear Case"]["daily_volume_usd"]),
                format_currency(result_bear_default["total"]),
                format_currency(result_bear_default["monthly_avg"]),
                format_currency(result_bear_default["daily_avg"]),
                format_percentage(result_bear_default["funding_spread"] * 100),
                format_percentage(result_bear_default["funding_roe"]),
                format_currency(result_bear_default["deployed_notional"]),
                f"{(result_bear_default['clearing'] / result_bear_default['total'] * 100):.1f}%" if result_bear_default["total"] > 0 else "N/A",
                f"{(result_bear_default['funding'] / result_bear_default['total'] * 100):.1f}%" if result_bear_default["total"] > 0 else "N/A",
                f"{(result_bear_default['liquidations'] / result_bear_default['total'] * 100):.1f}%" if result_bear_default["total"] > 0 else "N/A",
                f"{(result_bear_default['hedging'] / result_bear_default['total'] * 100):.1f}%" if result_bear_default["total"] > 0 else "N/A",
            ],
            "Base Case": [
                format_currency(SCENARIOS["Base Case"]["daily_volume_usd"]),
                format_currency(result_base_default["total"]),
                format_currency(result_base_default["monthly_avg"]),
                format_currency(result_base_default["daily_avg"]),
                format_percentage(result_base_default["funding_spread"] * 100),
                format_percentage(result_base_default["funding_roe"]),
                format_currency(result_base_default["deployed_notional"]),
                f"{(result_base_default['clearing'] / result_base_default['total'] * 100):.1f}%",
                f"{(result_base_default['funding'] / result_base_default['total'] * 100):.1f}%",
                f"{(result_base_default['liquidations'] / result_base_default['total'] * 100):.1f}%",
                f"{(result_base_default['hedging'] / result_base_default['total'] * 100):.1f}%",
            ],
            "Bull Case": [
                format_currency(SCENARIOS["Bull Case"]["daily_volume_usd"]),
                format_currency(result_bull_default["total"]),
                format_currency(result_bull_default["monthly_avg"]),
                format_currency(result_bull_default["daily_avg"]),
                format_percentage(result_bull_default["funding_spread"] * 100),
                format_percentage(result_bull_default["funding_roe"]),
                format_currency(result_bull_default["deployed_notional"]),
                f"{(result_bull_default['clearing'] / result_bull_default['total'] * 100):.1f}%",
                f"{(result_bull_default['funding'] / result_bull_default['total'] * 100):.1f}%",
                f"{(result_bull_default['liquidations'] / result_bull_default['total'] * 100):.1f}%",
                f"{(result_bull_default['hedging'] / result_bull_default['total'] * 100):.1f}%",
            ],
        })

        st.dataframe(comparison_df, use_container_width=True, hide_index=True)

        st.divider()

        # Visualization
        st.subheader("Revenue Comparison")
        scenarios_list = ["Bear Case", "Base Case", "Bull Case"]
        revenues = [
            result_bear_default["total"],
            result_base_default["total"],
            result_bull_default["total"],
        ]

        fig = go.Figure(
            data=[
                go.Bar(
                    x=scenarios_list,
                    y=revenues,
                    marker=dict(color=["#ff7f0e", "#2ca02c", "#d62728"]),
                    text=[format_currency(r) for r in revenues],
                    textposition="auto",
                    hovertemplate="<b>%{x}</b><br>%{y:$,.0f}<extra></extra>",
                )
            ]
        )
        fig.update_layout(
            title="Annual Revenue by Scenario",
            xaxis_title="Scenario",
            yaxis_title="Annual Revenue (USD)",
            template="plotly_white",
            height=400,
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    # ========== FOOTER & EXPORTS ==========
    st.divider()
    st.markdown("---")
    st.markdown(
        """
        **BitFrost Revenue Forecasting Engine** | Mathematical modeling for institutional investors
        
        Model Version: 1.0 | Last Updated: 2025-11-30
        
        This model implements the complete revenue mathematics outlined in the BitFrost protocol design.
        """
    )


if __name__ == "__main__":
    main()