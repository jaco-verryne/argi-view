"""
Cost Category Deep-Dive page.

Pick a category (diesel, chemicals, labour) and see:
trend over time, top cost drivers, purchase vs usage for stock.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from . import data


def render():
    st.title("Cost Category Deep-Dive")
    st.caption("Drill into a single cost category — trends, " "top drivers, purchase vs usage.")

    # ── Filters ───────────────────────────────────────────────────────
    min_date, max_date = data.get_date_range()
    categories = data.get_categories()

    col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
    with col_f1:
        date_from = st.date_input(
            "From", value=min_date, min_value=min_date, max_value=max_date, key="cd_from"
        )
    with col_f2:
        date_to = st.date_input(
            "To", value=max_date, min_value=min_date, max_value=max_date, key="cd_to"
        )
    with col_f3:
        category = st.selectbox("Category", categories, key="cd_cat")

    # ── KPI ───────────────────────────────────────────────────────────
    cat_total_df = data.cost_by_category(date_from, date_to)
    cat_total = cat_total_df.loc[cat_total_df["category"] == category, "total"]
    cat_amount = float(cat_total.iloc[0]) if not cat_total.empty else 0
    overall = float(cat_total_df["total"].sum())
    pct = (cat_amount / overall * 100) if overall > 0 else 0

    k1, k2 = st.columns(2)
    k1.metric(f"Total {category.title()} Cost", f"R{cat_amount:,.0f}")
    k2.metric("Share of Total Spend", f"{pct:.1f}%")

    st.divider()

    # ── Daily Trend ───────────────────────────────────────────────────
    st.subheader(f"Daily {category.title()} Spend")
    trend_df = data.category_trend(date_from, date_to, category)

    if not trend_df.empty:
        fig = px.area(
            trend_df,
            x="date",
            y="total",
            labels={"total": "Cost (ZAR)", "date": "Date"},
            color_discrete_sequence=["#2E7D32"],
        )
        avg = trend_df["total"].mean()
        fig.add_hline(
            y=avg,
            line_dash="dash",
            line_color="gray",
            annotation_text=f"Daily avg: R{avg:,.0f}",
        )
        fig.update_layout(
            margin=dict(t=30, b=10),
            height=350,
        )
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("No data for this category in the selected period.")
        return

    # ── Top Drivers ───────────────────────────────────────────────────
    st.subheader(f"Top {category.title()} Drivers")
    drivers_df = data.category_top_drivers(date_from, date_to, category)

    if not drivers_df.empty:
        col1, col2 = st.columns([1, 1])

        with col1:
            fig = px.bar(
                drivers_df.head(10),
                x="total",
                y="subcategory",
                orientation="h",
                text=drivers_df.head(10)["total"].apply(lambda v: f"R{v:,.0f}"),
                color_discrete_sequence=["#2E7D32"],
                labels={"total": "Cost (ZAR)", "subcategory": ""},
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(
                yaxis=dict(autorange="reversed"),
                margin=dict(t=10, b=10, l=10),
                height=400,
            )
            st.plotly_chart(fig, width="stretch")

        with col2:
            st.dataframe(
                drivers_df.style.format(
                    {
                        "total": "R{:,.0f}",
                        "total_qty": "{:,.1f}",
                    }
                ),
                width="stretch",
                hide_index=True,
            )

    # ── Purchase vs Usage (stock categories only) ─────────────────────
    if category in ("chemicals", "workshop", "toiletries"):
        st.divider()
        st.subheader("Purchase vs Usage (Stock)")
        st.caption(
            "Compares GRV (goods received) against usage. "
            "Large gaps may indicate overstock or unrecorded usage."
        )

        pvu_df = data.stock_purchase_vs_usage(date_from, date_to)

        if not pvu_df.empty:
            # Filter to products relevant to this category
            # Show top 15 by purchase value
            pvu_top = pvu_df.head(15)

            fig = go.Figure()
            fig.add_trace(
                go.Bar(
                    name="Purchased (GRV)",
                    x=pvu_top["product"],
                    y=pvu_top["purchase_value"],
                    marker_color="#1565C0",
                )
            )
            fig.add_trace(
                go.Bar(
                    name="Used",
                    x=pvu_top["product"],
                    y=pvu_top["usage_value"],
                    marker_color="#F57F17",
                )
            )
            fig.update_layout(
                barmode="group",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                ),
                xaxis_title="",
                yaxis_title="Value (ZAR)",
                margin=dict(t=40, b=10),
                height=400,
            )
            st.plotly_chart(fig, width="stretch")

            # Flag large gaps
            pvu_df["gap_pct"] = (
                (pvu_df["purchase_value"] - pvu_df["usage_value"])
                / pvu_df["purchase_value"].replace(0, 1)
                * 100
            )
            overstocked = pvu_df[(pvu_df["gap_pct"] > 50) & (pvu_df["purchase_value"] > 0)]
            if not overstocked.empty:
                st.warning(
                    f"**{len(overstocked)} product(s)** with >50% of "
                    "purchased value unused: " + ", ".join(overstocked["product"].head(5).tolist())
                )
