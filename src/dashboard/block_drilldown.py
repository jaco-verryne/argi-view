"""
Block Drill-Down page.

Select a phase, see all blocks: cost per hectare, category breakdown,
side-by-side comparison, anomaly highlighting.
"""

import streamlit as st
import plotly.express as px
import pandas as pd

from . import data


def render():
    st.title("Block Drill-Down")
    st.caption(
        "Compare blocks within a phase — cost per hectare, " "category split, anomaly flags."
    )

    # ── Filters ───────────────────────────────────────────────────────
    min_date, max_date = data.get_date_range()
    phases = data.get_phases()

    col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
    with col_f1:
        date_from = st.date_input(
            "From", value=min_date, min_value=min_date, max_value=max_date, key="bd_from"
        )
    with col_f2:
        date_to = st.date_input(
            "To", value=max_date, min_value=min_date, max_value=max_date, key="bd_to"
        )
    with col_f3:
        phase_filter = st.selectbox("Phase", ["All Phases"] + phases, key="bd_phase")

    phase = None if phase_filter == "All Phases" else phase_filter

    # ── Cost per Hectare chart ────────────────────────────────────────
    st.subheader("Cost per Hectare")
    cph_df = data.cost_per_hectare(date_from, date_to, phase)

    if cph_df.empty:
        st.info("No block-level cost data for this period.")
        return

    # Calculate average for anomaly highlighting
    avg_cph = cph_df["cost_per_ha"].mean()
    cph_df["above_avg"] = cph_df["cost_per_ha"] > avg_cph * 1.25
    cph_df["color"] = cph_df["above_avg"].map({True: "Above Average (+25%)", False: "Normal"})

    fig = px.bar(
        cph_df,
        x="block",
        y="cost_per_ha",
        color="color",
        color_discrete_map={
            "Above Average (+25%)": "#C62828",
            "Normal": "#2E7D32",
        },
        text=cph_df["cost_per_ha"].apply(lambda v: f"R{v:,.0f}"),
        labels={"cost_per_ha": "Cost / Hectare (ZAR)", "block": "Block"},
    )
    fig.add_hline(
        y=avg_cph,
        line_dash="dash",
        line_color="gray",
        annotation_text=f"Avg: R{avg_cph:,.0f}/ha",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        showlegend=True,
        legend_title_text="",
        margin=dict(t=30, b=10),
        height=450,
    )
    st.plotly_chart(fig, width="stretch")

    # ── Stacked category breakdown per block ──────────────────────────
    st.subheader("Category Breakdown by Block")
    block_df = data.cost_by_block(date_from, date_to, phase)

    if not block_df.empty:
        colors = {
            "labour": "#2E7D32",
            "diesel": "#F57F17",
            "chemicals": "#1565C0",
            "workshop": "#6A1B9A",
            "toiletries": "#00838F",
        }
        fig = px.bar(
            block_df,
            x="block",
            y="total",
            color="category",
            color_discrete_map=colors,
            labels={"total": "Cost (ZAR)", "block": "Block"},
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
            height=450,
        )
        st.plotly_chart(fig, width="stretch")

    # ── Block Summary Table ───────────────────────────────────────────
    st.subheader("Block Summary")

    # Pivot: one row per block, columns = categories + total
    if not block_df.empty:
        pivot = block_df.pivot_table(
            index=["block", "hectares", "variety"],
            columns="category",
            values="total",
            aggfunc="sum",
            fill_value=0,
        ).reset_index()
        pivot["Total"] = (
            pivot.select_dtypes("number").drop(columns=["hectares"], errors="ignore").sum(axis=1)
        )
        pivot["Cost/ha"] = pivot["Total"] / pivot["hectares"]
        pivot = pivot.sort_values("Cost/ha", ascending=False)

        # Highlight high-cost blocks
        def highlight_high(row):
            styles = [""] * len(row)
            if "Cost/ha" in row.index and row["Cost/ha"] > avg_cph * 1.25:
                idx = list(row.index).index("Cost/ha")
                styles[idx] = "background-color: #FFCDD2"
            return styles

        fmt = {
            col: "R{:,.0f}" for col in pivot.columns if col not in ("block", "hectares", "variety")
        }
        fmt["hectares"] = "{:.1f}"

        styled = pivot.style.format(fmt).apply(highlight_high, axis=1)
        st.dataframe(styled, width="stretch", hide_index=True)

        # Anomaly callout
        anomalies = cph_df[cph_df["above_avg"]]
        if not anomalies.empty:
            st.warning(
                f"**{len(anomalies)} block(s) above 125% of average "
                f"cost/ha (R{avg_cph:,.0f}/ha):** " + ", ".join(anomalies["block"].tolist())
            )
