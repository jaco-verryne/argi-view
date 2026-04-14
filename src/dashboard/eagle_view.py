"""
Eagle View — The Home Page.

One screen, full picture. Total cost, category breakdown,
phase summary, and daily trend. This is what dad opens every morning.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta

from . import data


def render():
    st.title("Eagle View")
    st.caption("All operating costs across the farm — one view, no silos.")

    # ── Filters ───────────────────────────────────────────────────────
    min_date, max_date = data.get_date_range()
    phases = data.get_phases()

    col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
    with col_f1:
        date_from = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date)
    with col_f2:
        date_to = st.date_input("To", value=max_date, min_value=min_date, max_value=max_date)
    with col_f3:
        phase_filter = st.selectbox("Phase", ["All Phases"] + phases)

    phase = None if phase_filter == "All Phases" else phase_filter

    # ── KPI row ───────────────────────────────────────────────────────
    total = data.total_cost(date_from, date_to, phase)
    num_days = (date_to - date_from).days + 1

    # Compare to prior period of same length
    prior_from = date_from - timedelta(days=num_days)
    prior_to = date_from - timedelta(days=1)
    prior_total = data.total_cost(prior_from, prior_to, phase)
    delta = total - prior_total if prior_total > 0 else None
    delta_pct = (
        f"{(delta / prior_total) * 100:+.1f}%" if prior_total > 0 and delta is not None else None
    )

    k1, k2, k3 = st.columns(3)
    k1.metric("Total Cost", f"R{total:,.0f}", delta_pct, delta_color="inverse")
    k2.metric(
        "Period", f"{num_days} days", f"{date_from.strftime('%d %b')} – {date_to.strftime('%d %b')}"
    )
    k3.metric("Daily Average", f"R{total / max(num_days, 1):,.0f}")

    st.divider()

    # ── Cost by Category (donut + bar) ────────────────────────────────
    cat_df = data.cost_by_category(date_from, date_to, phase)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Cost Breakdown")
        if not cat_df.empty:
            colors = {
                "labour": "#2E7D32",
                "diesel": "#F57F17",
                "chemicals": "#1565C0",
                "workshop": "#6A1B9A",
                "toiletries": "#00838F",
            }
            fig = px.pie(
                cat_df,
                values="total",
                names="category",
                color="category",
                color_discrete_map=colors,
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
                cat_df,
                x="total",
                y="category",
                orientation="h",
                color="category",
                color_discrete_map=colors,
                text=cat_df["total"].apply(lambda v: f"R{v:,.0f}"),
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(
                showlegend=False,
                xaxis_title="Cost (ZAR)",
                yaxis_title="",
                margin=dict(t=10, b=10),
                height=350,
            )
            st.plotly_chart(fig, width="stretch")

    # ── Phase Summary Cards ───────────────────────────────────────────
    st.subheader("Cost by Phase")
    phase_df = data.cost_by_phase(date_from, date_to)

    # Only show the 4 main farm phases in cards
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
        colors = {
            "labour": "#2E7D32",
            "diesel": "#F57F17",
            "chemicals": "#1565C0",
            "workshop": "#6A1B9A",
            "toiletries": "#00838F",
        }
        fig = px.bar(
            trend_df,
            x="date",
            y="total",
            color="category",
            color_discrete_map=colors,
            labels={"total": "Cost (ZAR)", "date": "Date"},
        )
        fig.update_layout(
            barmode="stack",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
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
        "Pick a day — see every cost line: fertilizer, fuel, "
        "tractor drivers, scouts, toilet cleaning, everything."
    )

    reg_date = st.date_input(
        "Select day",
        value=min_date,
        min_value=min_date,
        max_value=max_date,
        key="reg_date",
    )

    reg_summary = data.daily_register_summary(reg_date, phase)

    if not reg_summary.empty:
        day_total = reg_summary["total_cost"].sum()
        st.metric(
            f"Total for {reg_date.strftime('%A, %d %B %Y')}",
            f"R{day_total:,.0f}",
        )

        # Show grouped by category with subcategory detail
        colors = {
            "labour": "#2E7D32",
            "diesel": "#F57F17",
            "chemicals": "#1565C0",
            "workshop": "#6A1B9A",
            "toiletries": "#00838F",
        }

        for cat in reg_summary["category"].unique():
            cat_rows = reg_summary[reg_summary["category"] == cat].copy()
            cat_total = cat_rows["total_cost"].sum()
            color = colors.get(cat, "#666666")

            with st.expander(
                f"**{cat.upper()}** — R{cat_total:,.0f} " f"({cat_total / day_total * 100:.0f}%)",
                expanded=True,
            ):
                # Horizontal bar of subcategories
                fig = px.bar(
                    cat_rows,
                    x="total_cost",
                    y="subcategory",
                    orientation="h",
                    text=cat_rows["total_cost"].apply(lambda v: f"R{v:,.0f}"),
                    color_discrete_sequence=[color],
                    labels={
                        "total_cost": "Cost (ZAR)",
                        "subcategory": "",
                    },
                )
                fig.update_traces(textposition="outside")
                fig.update_layout(
                    showlegend=False,
                    yaxis=dict(autorange="reversed"),
                    margin=dict(t=5, b=5, l=5, r=60),
                    height=max(len(cat_rows) * 35 + 40, 120),
                )
                st.plotly_chart(fig, width="stretch")

        # Full line-item detail in a table
        with st.expander("View all line items"):
            reg_detail = data.daily_register(reg_date, phase)
            st.dataframe(
                reg_detail.style.format(
                    {
                        "cost_rands": "R{:,.2f}",
                        "quantity": "{:,.1f}",
                    }
                ),
                width="stretch",
                hide_index=True,
                height=400,
            )
    else:
        st.info(f"No costs recorded for {reg_date.strftime('%d %B %Y')}.")

    st.divider()

    # ── Phase × Category Matrix ───────────────────────────────────────
    st.subheader("Phase × Category Breakdown")
    matrix_df = data.cost_by_phase_category(date_from, date_to)

    if not matrix_df.empty:
        pivot = matrix_df.pivot_table(
            index="phase",
            columns="category",
            values="total",
            aggfunc="sum",
            fill_value=0,
        )
        pivot["Total"] = pivot.sum(axis=1)
        pivot = pivot.sort_values("Total", ascending=False)

        # Format as Rands
        styled = pivot.style.format("R{:,.0f}")
        st.dataframe(styled, width="stretch")
