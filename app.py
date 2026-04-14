"""Entry point for Streamlit Community Cloud."""

import streamlit as st

st.set_page_config(
    page_title="AgriView",
    page_icon="\U0001f331",
    layout="wide",
)


# ── Authentication ────────────────────────────────────────────────────

def check_password():
    """Simple password gate. Set the password in .streamlit/secrets.toml
    or Streamlit Cloud secrets as:
        [auth]
        password = "your-password-here"
    """
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.title("AgriView")
    st.caption("Farm cost analytics — authorised access only.")

    password = st.text_input("Password", type="password")
    if st.button("Login", use_container_width=True):
        try:
            correct = st.secrets["auth"]["password"]
        except (KeyError, FileNotFoundError):
            # Fallback: no secrets configured, use env var or default
            import os
            correct = os.environ.get("AGRIVIEW_PASSWORD", "agriview2026")

        if password == correct:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")

    return False


if not check_password():
    st.stop()


# ── Navigation ────────────────────────────────────────────────────────

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
