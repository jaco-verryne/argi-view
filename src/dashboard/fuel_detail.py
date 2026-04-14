"""
Fuel Detail page.

Per-vehicle fuel analysis: consumption, litres/hour efficiency,
daily anomaly detection, transaction log.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from . import data


def render():
    st.title("Fuel Detail")
    st.caption("Vehicle-level fuel analysis — consumption, efficiency, " "and anomaly flags.")

    # ── Filters ───────────────────────────────────────────────────────
    min_date, max_date = data.get_date_range()

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        date_from = st.date_input(
            "From", value=min_date, min_value=min_date, max_value=max_date, key="fd_from"
        )
    with col_f2:
        date_to = st.date_input(
            "To", value=max_date, min_value=min_date, max_value=max_date, key="fd_to"
        )

    # ── Vehicle Summary ───────────────────────────────────────────────
    st.subheader("Vehicle Summary")
    veh_df = data.fuel_by_vehicle(date_from, date_to)

    if veh_df.empty:
        st.info("No fuel data for this period.")
        return

    # KPIs
    total_litres = veh_df["total_litres"].sum()
    total_cost = veh_df["total_cost"].sum()
    k1, k2, k3 = st.columns(3)
    k1.metric("Total Litres", f"{total_litres:,.0f} L")
    k2.metric("Total Fuel Cost", f"R{total_cost:,.0f}")
    k3.metric("Avg Cost/Litre", f"R{total_cost / max(total_litres, 1):,.2f}")

    # Litres by vehicle bar chart
    col1, col2 = st.columns([1, 1])

    with col1:
        fig = px.bar(
            veh_df,
            x="vehicle",
            y="total_litres",
            color="vehicle_type",
            text=veh_df["total_litres"].apply(lambda v: f"{v:,.0f}L"),
            labels={"total_litres": "Litres", "vehicle": "Vehicle"},
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            showlegend=True,
            margin=dict(t=30, b=10),
            height=400,
        )
        st.plotly_chart(fig, width="stretch")

    with col2:
        # Litres per hour — efficiency metric
        tractors = veh_df[
            (veh_df["vehicle_type"] == "tractor") & (veh_df["litres_per_hour"] > 0)
        ].copy()

        if not tractors.empty:
            avg_lph = tractors["litres_per_hour"].mean()
            tractors["above_avg"] = tractors["litres_per_hour"] > avg_lph * 1.2
            tractors["flag"] = tractors["above_avg"].map(
                {True: "High consumption", False: "Normal"}
            )

            fig = px.bar(
                tractors,
                x="vehicle",
                y="litres_per_hour",
                color="flag",
                color_discrete_map={
                    "High consumption": "#C62828",
                    "Normal": "#2E7D32",
                },
                text=tractors["litres_per_hour"].apply(lambda v: f"{v:.1f}"),
                labels={
                    "litres_per_hour": "Litres/Hour",
                    "vehicle": "Vehicle",
                },
            )
            fig.add_hline(
                y=avg_lph,
                line_dash="dash",
                line_color="gray",
                annotation_text=f"Avg: {avg_lph:.1f} L/hr",
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(
                title="Litres per Hour (tractors)",
                showlegend=True,
                legend_title_text="",
                margin=dict(t=40, b=10),
                height=400,
            )
            st.plotly_chart(fig, width="stretch")

            # Flag high-consumption vehicles
            flagged = tractors[tractors["above_avg"]]
            if not flagged.empty:
                st.warning(
                    f"**{len(flagged)} tractor(s) above 120% of average "
                    f"L/hr ({avg_lph:.1f}):** "
                    + ", ".join(flagged["vehicle"].tolist())
                    + ". Investigate for mechanical issues or theft."
                )

    st.divider()

    # ── Daily Consumption per Vehicle ─────────────────────────────────
    st.subheader("Daily Consumption by Vehicle")
    daily_df = data.fuel_daily_by_vehicle(date_from, date_to)

    if not daily_df.empty:
        fig = px.line(
            daily_df,
            x="date",
            y="litres",
            color="vehicle",
            labels={"litres": "Litres", "date": "Date"},
        )
        fig.update_layout(
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

    # ── Transaction Log ───────────────────────────────────────────────
    st.subheader("Transaction Log")

    vehicles = ["All"] + veh_df["vehicle"].tolist()
    selected_vehicle = st.selectbox("Filter by vehicle", vehicles, key="fd_vehicle")
    vehicle_filter = None if selected_vehicle == "All" else selected_vehicle

    txn_df = data.fuel_transactions(date_from, date_to, vehicle_filter)
    if not txn_df.empty:
        st.dataframe(
            txn_df.style.format(
                {
                    "litres": "{:,.1f}",
                    "cost_rands": "R{:,.2f}",
                    "pump_reading_start": "{:,.1f}",
                    "pump_reading_end": "{:,.1f}",
                    "hours": "{:.1f}",
                    "odometer": "{:,.0f}",
                }
            ),
            width="stretch",
            hide_index=True,
            height=400,
        )
    else:
        st.info("No transactions found.")

    # ── Vehicle Detail Table ──────────────────────────────────────────
    st.subheader("Vehicle Efficiency Table")
    st.dataframe(
        veh_df.style.format(
            {
                "total_litres": "{:,.1f}",
                "total_cost": "R{:,.0f}",
                "total_hours": "{:,.1f}",
                "litres_per_hour": "{:.2f}",
            }
        ),
        width="stretch",
        hide_index=True,
    )
