import streamlit as st
import numpy as np
import pandas as pd
import imageio
from st_aggrid import AgGrid, GridOptionsBuilder

from ui import parse_csv, add_option_form, remove_option_ui
from portfolio import (
    build_portfolio,
    plot_value_evolution,
    plot_all_greeks,
)
from src.vol_surface import VolSurface, create_vol_surface_evolution_video
from src.contracts import set_risk_free_rate

st.set_page_config(layout="centered")
st.title("Vol Surfer - An Options Calculator")
st.image(r"app\assets\logo.png")

# Session state initialization
if "portfolio_options" not in st.session_state:
    st.session_state["portfolio_options"] = []

# --- User inputs for Underlying Price & DTEs ---
underlying_price = st.number_input(
    "Underlying Stock Price", min_value=0.0, max_value=1000.0, value=100.0
)
dtes_input = st.text_input("DTEs (days)", "7, 14")
dtes = parse_csv(dtes_input)

# Create two main tabs: one for manual entry and one for chain selection.
tab_manual, tab_chain = st.tabs(["Manual Entry", "Select from Chain"])

# --- Manual Entry Tab ---
with tab_manual:
    submitted, flag, strike, dte, pos = add_option_form(dtes)
    if submitted:
        st.session_state["portfolio_options"].append(
            {
                "flag": "c" if flag == "Call" else "p",
                "strike": strike,
                "dte_days": dte,
                "pos": pos,
                "underlying_price": underlying_price,
            }
        )
        st.success("Option added to portfolio!")

# --- Select from Chain Tab ---
with tab_chain:
    st.subheader("Select Option from Chain")
    # For demonstration, we simulate a chain dictionary.
    # Replace this with your actual Chain object as needed.
    strikes = np.linspace(underlying_price * 0.8, underlying_price * 1.2, 5)
    chain = {
        (d, s, f): {
            "flag": f,
            "strike": s,
            "dte_days": d,
            "pos": 1,  # default position, can be adjusted
            "underlying_price": underlying_price,
        }
        for d in dtes for s in strikes for f in ["c", "p"]
    }

    # Create subtabs for each DTE
    dte_tabs = st.tabs([f"DTE: {d}" for d in dtes])
    for i, d in enumerate(dtes):
        with dte_tabs[i]:
            st.write(f"Available Options for DTE: {d}")
            # Filter the chain for this DTE
            options_for_dte = {key: val for key, val in chain.items() if key[0] == d}

            if options_for_dte:
                # Display available options in a table for reference
                options_df = pd.DataFrame(
                    [{"Strike": key[1], "Flag": key[2]} for key in options_for_dte.keys()]
                )
                gb = GridOptionsBuilder.from_dataframe(options_df)
                gb.configure_selection('single', use_checkbox=True)
                grid_options = gb.build()

                grid_response = AgGrid(options_df, gridOptions=grid_options, height=200, fit_columns_on_grid_load=True)

                selected_rows = grid_response.get("selected_rows", [])
                if selected_rows and st.button("Add Selected Options to Portfolio"):
                    # Initialize session state portfolio if needed
                    if "portfolio_options" not in st.session_state:
                        st.session_state["portfolio_options"] = []
                        
                    # Add each selected row (option) to the portfolio
                    for row in selected_rows:
                        st.session_state["portfolio_options"].append(row)
                    st.success(f"Added {len(selected_rows)} options to portfolio!")

# --- Display current portfolio options ---
st.subheader("Current Portfolio Options")
if st.session_state["portfolio_options"]:
    df = pd.DataFrame(st.session_state["portfolio_options"])
    st.table(df)
else:
    st.write("No options added yet.")

remove_option_ui("portfolio_options")

# --- Sidebar for Vol Surface & Simulation Params ---
st.sidebar.title("Vol Surface and Simulation Parameters")

with st.sidebar.expander("Underlying & Simulation Parameters", expanded=True):
    elapsed_time = st.slider(
        "Elapsed Time (days)", min_value=0.1, max_value=60.0, value=10.0, step=0.1
    )
    timesteps = st.slider("Timesteps", min_value=1, max_value=30, value=10)

    s_min_init, s_max_init = (underlying_price * 0.8, underlying_price * 1.2)
    S_min = st.number_input(
        "Min Underlying Price", min_value=0.0, max_value=2000.0, value=s_min_init
    )
    S_max = st.number_input(
        "Max Underlying Price", min_value=0.0, max_value=2000.0, value=s_max_init
    )
    S_points = st.slider("Number of Price Steps", min_value=5, max_value=50, value=20)
    S_range = np.linspace(S_min, S_max, S_points)
    rfr = st.number_input("Risk Free Rate", min_value=0.0, max_value=0.1, value=0.04)
    set_risk_free_rate(rfr)

with st.sidebar.expander("Current Vol Surface"):
    atm_vols_input = st.text_input("ATM Vols", "")
    skews_input = st.text_input("Skews", "")
    kurtosis_input = st.text_input("Kurtosis", "")
    atm_vols = parse_csv(atm_vols_input)
    skews = parse_csv(skews_input)
    kurtosis = parse_csv(kurtosis_input)

with st.sidebar.expander("Future Vol Surface (Optional)"):
    new_atm_vols_input = st.text_input("New ATM Vols", "")
    new_skews_input = st.text_input("New Skews", "")
    new_kurtosis_input = st.text_input("New Kurtosis", "")

    new_atm_vols = parse_csv(new_atm_vols_input) or atm_vols
    new_skews = parse_csv(new_skews_input) or skews
    new_kurtosis = parse_csv(new_kurtosis_input) or kurtosis

# --- Buttons for Plotting ---
btn1, btn2, btn3, btn4 = st.columns(4)
with btn1:
    plot_value_btn = st.button("Plot Value Evolution")

with btn2:
    plot_greek_btn = st.button("Plot Greek Evolution")

with btn3:
    plot_volsurf_btn = st.button("Plot Vol Surface")

with btn4:
    animate_volsurf_btn = st.button("Animate Vol Surface Evolution")

# --- Plot Value Evolution ---
if plot_value_btn:
    portfolio = build_portfolio(underlying_price, st.session_state["portfolio_options"])
    vol_surface = VolSurface(
        atm_strike=underlying_price,
        dtes=dtes,
        atm_vols=atm_vols,
        skews=skews,
        kurtosis=kurtosis,
    )

    st.header("3D Portfolio Evolution: Value")
    fig = plot_value_evolution(
        portfolio,
        vol_surface,
        new_atm_vols,
        new_skews,
        new_kurtosis,
        elapsed_time,
        timesteps,
        S_range,
    )
    st.pyplot(fig, use_container_width=True)

# --- Plot Greek Evolution ---
if plot_greek_btn:
    portfolio = build_portfolio(underlying_price, st.session_state["portfolio_options"])
    vol_surface = VolSurface(
        atm_strike=underlying_price,
        dtes=dtes,
        atm_vols=atm_vols,
        skews=skews,
        kurtosis=kurtosis,
    )

    st.header("3D Portfolio Evolution: All Greeks")
    figs = plot_all_greeks(
        portfolio,
        vol_surface,
        new_atm_vols,
        new_skews,
        new_kurtosis,
        elapsed_time,
        timesteps,
        S_range,
    )

    tab1, tab2, tab3, tab4 = st.tabs(["Delta", "Gamma", "Theta", "Vega"])
    with tab1:
        st.pyplot(figs["delta"])
    with tab2:
        st.pyplot(figs["gamma"])
    with tab3:
        st.pyplot(figs["theta"])
    with tab4:
        st.pyplot(figs["vega"])

# --- Plot Vol Surface ---
if plot_volsurf_btn:
    vol_surface = VolSurface(
        atm_strike=underlying_price,
        dtes=dtes,
        atm_vols=atm_vols,
        skews=skews,
        kurtosis=kurtosis,
    )
    fig = vol_surface.plot_surface()
    st.pyplot(fig)

# --- Animate Vol Surface ---
if animate_volsurf_btn:
    vol_surface = VolSurface(
        atm_strike=underlying_price,
        dtes=dtes,
        atm_vols=atm_vols,
        skews=skews,
        kurtosis=kurtosis,
    )
    frames = create_vol_surface_evolution_video(
        vol_surface, timesteps, new_atm_vols, new_skews, new_kurtosis
    )

    # Example: writing frames to a file, or display as video
    video_filename = "vol_surface.mp4"
    imageio.mimwrite(video_filename, frames, fps=2)
    st.video(video_filename, format="video/mp4")
