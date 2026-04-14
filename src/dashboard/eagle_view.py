"""
Eagle View — The Home Page.

One screen, full picture. Total cost, category breakdown,
phase summary, daily trend, anomaly alerts, and daily register.
This is what dad opens every morning.
"""

import streamlit as st
import plotly.express as px
from datetime import timedelta

from . import data

COLORS = {
    "labour": "#2E7D32",
    "diesel": "#F57F17",
    "chemicals": "#1565C0",
    "workshop": "#6A1B9A",
    "toiletries": "#00838F",
}


def render():
    st.title("Eagle View")
    st.caption("All operating costs across the farm — one view, no silos.")

    # ── Filters ───────────────────────────────────────────────────────
    min_date, max_date = data.get_date_range()
    phases = data.get_phases()

    col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
    with col_f1:
        date_from = st.date_input(
            "From", value=min_date,
            min_value=min_date, max_value=max_date,
        )
    with col_f2:
        date_to = st.date_input(
            "To", value=max_date,
            min_value=min_date, max_value=max_date,
        )
    with col_f3:
        phase_filter = st.selectbox("Phase", ["All Phases"] + phases)

    phase = None if phase_filter == "All Phases" else phase_filter

    # ── KPI row ───────────────────────────────────────────────────────
    total = data.total_cost(date_from, date_to, phase)
    num_days = (date_to - date_from).days + 1

    prior_from = date_from - timedelta(days=num_days)
    prior_to = date_from - timedelta(days=1)
    prior_total = data.total_cost(prior_from, prior_to, phase)
    delta = total - prior_total if prior_total > 0 else None
    delta_pct = (
        f"{(delta / prior_total) * 100:+.1f}%"
        if prior_total > 0 and delta is not None else None
    )

    k1, k2, k3 = st.columns(3)
    k1.metric("Total Cost", f"R{total:,.0f}", delta_pct,
              delta_color="inverse")
    k2.metric("Period", f"{num_days} days",
              f"{date_from.strftime('%d %b')} – {date_to.strftime('%d %b')}")
    k3.metric("Daily Average", f"R{total / max(num_days, 1):,.0f}")

    # ── Anomaly Alerts ────────────────────────────────────────────────
    anomalies = data.detect_all_anomalies(date_from, date_to)
    alert_count = sum(
        len(df) for df in anomalies.values() if not df.empty
    )

    if alert_count > 0:
        with st.container(border=True):
            st.subheader(f"Alerts ({alert_count})")

            # Fuel anomalies
            fuel_flags = anomalies["fuel"]
            if not fuel_flags.empty:
                for _, r in fuel_flags.iterrows():
                    st.error(
                        f"**{r['vehicle']}** is burning "
                        f"**{r['litres_per_hour']:.1f} L/hr** — "
                        f"{r['pct_above']:.0f}% above fleet average "
                        f"({r['avg_litres_per_hour']:.1f} L/hr). "
                        "Investigate for mechanical issues or theft."
                    )

            # Block cost outliers
            block_flags = anomalies["blocks"]
            if not block_flags.empty:
                block_names = block_flags["block"].tolist()
                worst = block_flags.iloc[0]
                st.warning(
                    f"**{len(block_flags)} block(s)** above 125% of "
                    f"average cost/ha (R{worst['avg_cost_per_ha']:,.0f}/ha): "
                    f"**{', '.join(block_names)}**. "
                    f"Highest: {worst['block']} at "
                    f"R{worst['cost_per_ha']:,.0f}/ha "
                    f"({worst['pct_above']:.0f}% above avg)."
                )

            # Stock gaps
            stock_flags = anomalies["stock"]
            if not stock_flags.empty:
                top3 = stock_flags.head(3)
                items = [
                    f"{r['product']} (R{r['gap_value']:,.0f} unused)"
                    for _, r in top3.iterrows()
                ]
                st.warning(
                    f"**{len(stock_flags)} product(s)** with >50% of "
                    "purchased value sitting unused: "
                    f"**{', '.join(items)}**"
                    + (f" and {len(stock_flags) - 3} more."
                       if len(stock_flags) > 3 else ".")
                )

    st.divider()

    # ── Cost by Category (donut + bar) ────────────────────────────────
    cat_df = data.cost_by_category(date_from, date_to, phase)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Cost Breakdown")
        if not cat_df.empty:
            fig = px.pie(
                cat_df, values="total", names="category",
                color="category", color_discrete_map=COLORS,
                hole=0.4,
            )
            fig.update_traces(
                textposition="inside",
                textinfo="label+percent",
                textfont_size=12,
            )
            fig.update_layout(
                showlegend=False,
                margin=dict(t=10, b=10, l=10, r=10),
                height=350,
            )
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No cost data for this period.")

    with col2:
        st.subheader("By Category")
        if not cat_df.empty:
            fig = px.bar(
                cat_df, x="total", y="category",
                orientation="h", color="category",
                color_discrete_map=COLORS,
                text=cat_df["total"].apply(lambda v: f"R{v:,.0f}"),
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(
                showlegend=False,
                xaxis_title="Cost (ZAR)", yaxis_title="",
                margin=dict(t=10, b=10),
                height=350,
            )
            st.plotly_chart(fig, width="stretch")

    # ── Phase Summary Cards ───────────────────────────────────────────
    st.subheader("Cost by Phase")
    phase_df = data.cost_by_phase(date_from, date_to)

    farm_phases = phase_df[phase_df["phase"].str.startswith("Phase")]
    other_phases = phase_df[~phase_df["phase"].str.startswith("Phase")]

    if not farm_phases.empty:
        cols = st.columns(len(farm_phases))
        for i, (_, row) in enumerate(farm_phases.iterrows()):
            with cols[i]:
                st.metric(row["phase"], f"R{row['total']:,.0f}")

    if not other_phases.empty:
        with st.expander("Other cost centres"):
            cols = st.columns(len(other_phases))
            for i, (_, row) in enumerate(other_phases.iterrows()):
                with cols[i]:
                    st.metric(row["phase"], f"R{row['total']:,.0f}")

    st.divider()

    # ── Daily Cost Trend ──────────────────────────────────────────────
    st.subheader("Daily Cost Trend")
    trend_df = data.daily_cost_trend(date_from, date_to, phase)

    if not trend_df.empty:
        fig = px.bar(
            trend_df, x="date", y="total", color="category",
            color_discrete_map=COLORS,
            labels={"total": "Cost (ZAR)", "date": "Date"},
        )
        fig.update_layout(
            barmode="stack",
            legend=dict(
                orientation="h", yanchor="bottom",
                y=1.02, xanchor="right", x=1,
            ),
            margin=dict(t=40, b=10),
            height=400,
        )
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("No cost data for this period.")

    # ── Daily Register ────────────────────────────────────────────────
    st.subheader("Daily Register")
    st.caption(
        "Every rand for a single day — fertilizer, fuel, "
        "tractor drivers, scouts, toilet cleaning, everything."
    )

    # Navigation: prev / date picker / next
    if "reg_date_input" not in st.session_state:
        st.session_state.reg_date_input = min_date

    def go_prev():
        new = st.session_state.reg_date_input - timedelta(days=1)
        if new >= min_date:
            st.session_state.reg_date_input = new

    def go_next():
        new = st.session_state.reg_date_input + timedelta(days=1)
        if new <= max_date:
            st.session_state.reg_date_input = new

    nav1, nav2, nav3 = st.columns([1, 3, 1])
    with nav1:
        st.button("< Previous Day", on_click=go_prev,
                  use_container_width=True)
    with nav2:
        st.date_input(
            "Day", min_value=min_date, max_value=max_date,
            key="reg_date_input", label_visibility="collapsed",
        )
    with nav3:
        st.button("Next Day >", on_click=go_next,
                  use_container_width=True)

    reg_date = st.session_state.reg_date_input
    reg_summary = data.daily_register_summary(reg_date, phase)

    if not reg_summary.empty:
        day_total = reg_summary["total_cost"].sum()
        line_count = int(reg_summary["lines"].sum())

        st.metric(
            f"{reg_date.strftime('%A, %d %B %Y')}",
            f"R{day_total:,.0f}",
            f"{line_count} cost lines",
        )

        for cat in reg_summary["category"].unique():
            cat_rows = reg_summary[reg_summary["category"] == cat].copy()
            cat_total = cat_rows["total_cost"].sum()
            color = COLORS.get(cat, "#666666")

            with st.expander(
                f"**{cat.upper()}** — R{cat_total:,.0f} "
                f"({cat_total / day_total * 100:.0f}%)",
                expanded=True,
            ):
                fig = px.bar(
                    cat_rows, x="total_cost", y="subcategory",
                    orientation="h",
                    text=cat_rows["total_cost"].apply(
                        lambda v: f"R{v:,.0f}"
                    ),
                    color_discrete_sequence=[color],
                    labels={"total_cost": "Cost (ZAR)", "subcategory": ""},
                )
                fig.update_traces(textposition="outside")
                fig.update_layout(
                    showlegend=False,
                    yaxis=dict(autorange="reversed"),
                    margin=dict(t=5, b=5, l=5, r=60),
                    height=max(len(cat_rows) * 35 + 40, 120),
                )
                st.plotly_chart(fig, width="stretch")

        with st.expander("View all line items"):
            reg_detail = data.daily_register(reg_date, phase)
            st.dataframe(
                reg_detail.style.format({
                    "cost_rands": "R{:,.2f}",
                    "quantity": "{:,.1f}",
                }),
                width="stretch", hide_index=True, height=400,
            )
    else:
        st.info(f"No costs recorded for {reg_date.strftime('%d %B %Y')}.")

    st.divider()

    # ── Phase × Category Matrix ───────────────────────────────────────
    st.subheader("Phase × Category Breakdown")
    matrix_df = data.cost_by_phase_category(date_from, date_to)

    if not matrix_df.empty:
        pivot = matrix_df.pivot_table(
            index="phase", columns="category",
            values="total", aggfunc="sum", fill_value=0,
        )
        pivot["Total"] = pivot.sum(axis=1)
        pivot = pivot.sort_values("Total", ascending=False)

        styled = pivot.style.format("R{:,.0f}")
        st.dataframe(styled, width="stretch")
