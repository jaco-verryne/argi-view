"""
Yield & Efficiency page.

Kg harvested per block, kg/ha benchmarks, cost per kg —
the efficiency metrics that tie inputs to outputs.
"""

import streamlit as st
import plotly.express as px

from . import data


def render():
    st.title("Yield & Efficiency")
    st.caption(
        "Harvest output and cost efficiency — " "linking inputs (cost) to outputs (kg harvested)."
    )

    # ── Filters ───────────────────────────────────────────────────────
    min_date, max_date = data.get_date_range()
    phases = data.get_phases()

    col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
    with col_f1:
        date_from = st.date_input(
            "From", value=min_date, min_value=min_date, max_value=max_date, key="yv_from"
        )
    with col_f2:
        date_to = st.date_input(
            "To", value=max_date, min_value=min_date, max_value=max_date, key="yv_to"
        )
    with col_f3:
        phase_filter = st.selectbox("Phase", ["All Phases"] + phases, key="yv_phase")

    phase = None if phase_filter == "All Phases" else phase_filter

    # ── Yield by Block ────────────────────────────────────────────────
    yield_df = data.yield_by_block(date_from, date_to, phase)

    if yield_df.empty:
        st.info("No harvest data for this period.")
        return

    # KPIs
    total_kg = yield_df["total_kg"].sum()
    total_ha = yield_df["hectares"].sum()
    k1, k2, k3 = st.columns(3)
    k1.metric("Total Harvested", f"{total_kg:,.0f} kg")
    k2.metric("Harvested Hectares", f"{total_ha:,.1f} ha")
    k3.metric("Avg Yield", f"{total_kg / max(total_ha, 1):,.0f} kg/ha")

    st.divider()

    # ── Kg per Hectare by Block ───────────────────────────────────────
    st.subheader("Kg per Hectare by Block")

    avg_kph = yield_df["kg_per_ha"].mean()

    fig = px.bar(
        yield_df,
        x="block",
        y="kg_per_ha",
        color="variety",
        text=yield_df["kg_per_ha"].apply(lambda v: f"{v:,.0f}"),
        labels={"kg_per_ha": "Kg / Hectare", "block": "Block"},
    )
    fig.add_hline(
        y=avg_kph,
        line_dash="dash",
        line_color="gray",
        annotation_text=f"Avg: {avg_kph:,.0f} kg/ha",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        legend_title_text="Variety",
        margin=dict(t=30, b=10),
        height=450,
    )
    st.plotly_chart(fig, width="stretch")

    # ── Cost per Kg ───────────────────────────────────────────────────
    st.subheader("Cost per Kg Harvested")
    st.caption("Total input cost divided by kg harvested. " "Lower is more efficient.")

    cpk_df = data.cost_per_kg(date_from, date_to, phase)

    if not cpk_df.empty:
        cpk_valid = cpk_df[cpk_df["cost_per_kg"].notna()].copy()

        if not cpk_valid.empty:
            avg_cpk = cpk_valid["cost_per_kg"].mean()

            cpk_valid["flag"] = cpk_valid["cost_per_kg"].apply(
                lambda v: "High cost" if v > avg_cpk * 1.25 else "Normal"
            )

            fig = px.bar(
                cpk_valid,
                x="block",
                y="cost_per_kg",
                color="flag",
                color_discrete_map={
                    "High cost": "#C62828",
                    "Normal": "#2E7D32",
                },
                text=cpk_valid["cost_per_kg"].apply(lambda v: f"R{v:,.0f}"),
                labels={
                    "cost_per_kg": "Cost / Kg (ZAR)",
                    "block": "Block",
                },
            )
            fig.add_hline(
                y=avg_cpk,
                line_dash="dash",
                line_color="gray",
                annotation_text=f"Avg: R{avg_cpk:,.0f}/kg",
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(
                showlegend=True,
                legend_title_text="",
                margin=dict(t=30, b=10),
                height=450,
            )
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No blocks with both cost and harvest data.")

    st.divider()

    # ── Daily Harvest Trend ───────────────────────────────────────────
    st.subheader("Daily Harvest")
    daily_df = data.daily_yield(date_from, date_to)

    if not daily_df.empty:
        fig = px.bar(
            daily_df,
            x="date",
            y="total_kg",
            labels={"total_kg": "Kg Harvested", "date": "Date"},
            color_discrete_sequence=["#2E7D32"],
        )
        fig.update_layout(
            margin=dict(t=10, b=10),
            height=300,
        )
        st.plotly_chart(fig, width="stretch")

    # ── Yield Summary Table ───────────────────────────────────────────
    st.subheader("Block Yield Summary")
    st.dataframe(
        yield_df.style.format(
            {
                "hectares": "{:.1f}",
                "total_kg": "{:,.0f}",
                "kg_per_ha": "{:,.0f}",
                "total_lugs": "{:,.0f}",
                "total_pickers": "{:,.0f}",
            }
        ),
        width="stretch",
        hide_index=True,
    )
