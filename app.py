"""Entry point for Streamlit Community Cloud."""

import streamlit as st

st.set_page_config(
    page_title="AgriView",
    page_icon="\U0001f331",
    layout="wide",
)

# Navigation
pages = {
    "Eagle View": "eagle",
    "Block Drill-Down": "block",
    "Cost Category": "category",
    "Fuel Detail": "fuel",
    "Yield & Efficiency": "yield",
}

with st.sidebar:
    st.title("AgriView")
    st.caption("Farm cost analytics")
    st.divider()
    page = st.radio("Navigate", list(pages.keys()), label_visibility="collapsed")

if pages[page] == "eagle":
    from src.dashboard.eagle_view import render

    render()
elif pages[page] == "block":
    from src.dashboard.block_drilldown import render

    render()
elif pages[page] == "category":
    from src.dashboard.category_detail import render

    render()
elif pages[page] == "fuel":
    from src.dashboard.fuel_detail import render

    render()
elif pages[page] == "yield":
    from src.dashboard.yield_view import render

    render()
