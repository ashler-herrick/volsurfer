from typing import List

import streamlit as st


def parse_csv(text: str):
    """Convert a comma-separated string into a list of floats."""
    if not text:
        return []
    return [float(x.strip()) for x in text.split(",") if x.strip()]


def init_session_state(key, default):
    if key not in st.session_state:
        st.session_state[key] = default
    return st.session_state[key]

def init_session_state_csv(key, default=""):
    if key not in st.session_state:
        st.session_state[key] = default
    arr = st.session_state[key]
    return ", ".join(str(x) for x in arr)

def add_option_form(dtes: List):
    """Renders a form to add an option, returns True if submitted."""
    with st.form("option_form", clear_on_submit=True):
        flag = st.selectbox("Option Type", ["Call", "Put"])
        strike = st.number_input("Strike", value=100.0)
        dte = st.selectbox("Days to Expiry (DTE)", dtes)
        pos = st.number_input(
            "Position (positive=long, negative=short)", value=1, step=1
        )
        submitted = st.form_submit_button("Add Option")
    return submitted, flag, strike, dte, pos


def remove_option_ui(portfolio_options_key="portfolio_options"):
    """Displays UI for removing an option from session state."""
    if portfolio_options_key not in st.session_state:
        return

    if st.session_state[portfolio_options_key]:
        with st.expander("Remove an Option"):
            option_strings = [
                f"Option {i+1}: Type={opt['flag'].upper()}, Strike={opt['strike']}, DTE={opt['dte_days']}, Pos={opt['pos']}"
                for i, opt in enumerate(st.session_state[portfolio_options_key])
            ]
            st.selectbox(
                "Select an option to remove",
                options=range(len(st.session_state[portfolio_options_key])),
                format_func=lambda i: option_strings[i],
                key="remove_index",
            )

            def remove_option():
                idx = st.session_state.remove_index
                st.session_state[portfolio_options_key].pop(idx)

            st.button("Remove Option", on_click=remove_option)
