# app.py
import streamlit as st
import numpy as np
import pandas as pd
import imageio

from ui import parse_csv, add_option_form, remove_option_ui
from portfolio import (
    build_portfolio,
    plot_value_evolution,
    plot_all_greeks,
)
from app.src.vol_surface import VolSurface, create_vol_surface_evolution_video

st.set_page_config(layout="centered")
st.title("Vol Surfer")

# Session state initialization
if "portfolio_options" not in st.session_state:
    st.session_state["portfolio_options"] = []

# --- User inputs for Underlying Price & DTEs ---
underlying_price = st.number_input("Underlying Stock Price", min_value=0.0, max_value=200.0, value=100.0)
dtes_input = st.text_input("DTEs (days)", "")
dtes = parse_csv(dtes_input)

st.header("Add Options to Portfolio")
submitted, flag, strike, dte, pos = add_option_form(dtes)
if submitted:
    st.session_state["portfolio_options"].append({
        "flag": "c" if flag == "Call" else "p",
        "strike": strike,
        "dte_days": dte,
        "pos": pos,
        "underlying_price": underlying_price,
    })

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
    elapsed_time = st.slider("Elapsed Time (days)", min_value=0.1, max_value=60.0, value=10.0, step=0.1)
    timesteps = st.slider("Timesteps", min_value=1, max_value=30, value=10)
    S_min = st.number_input("Min Underlying Price", min_value=50.0, max_value=150.0, value=80.0)
    S_max = st.number_input("Max Underlying Price", min_value=80.0, max_value=200.0, value=120.0)
    S_points = st.slider("Number of Price Steps", min_value=5, max_value=50, value=20)
    S_range = np.linspace(S_min, S_max, S_points)

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
btn1, btn2, btn3 = st.columns(3)
with btn1:
    plot_value_btn = st.button("Plot Value Evolution")

with btn2:
    plot_greek_btn = st.button("Plot Greek Evolution")

with btn3:
    plot_volsurf_btn = st.button("Animate Vol Surface")

# --- Plot Value Evolution ---
if plot_value_btn:
    portfolio = build_portfolio(underlying_price, st.session_state["portfolio_options"])
    vol_surface = VolSurface(atm_strike=underlying_price, dtes=dtes, atm_vols=atm_vols, skews=skews, kurtosis=kurtosis)
    
    st.header("3D Portfolio Evolution: Value")
    fig = plot_value_evolution(
        portfolio,
        vol_surface,
        new_atm_vols,
        new_skews,
        new_kurtosis,
        elapsed_time,
        timesteps,
        S_range
    )
    st.pyplot(fig, use_container_width=True)

# --- Plot Greek Evolution ---
if plot_greek_btn:
    portfolio = build_portfolio(underlying_price, st.session_state["portfolio_options"])
    vol_surface = VolSurface(atm_strike=underlying_price, dtes=dtes, atm_vols=atm_vols, skews=skews, kurtosis=kurtosis)
    
    st.header("3D Portfolio Evolution: All Greeks")
    figs = plot_all_greeks(
        portfolio,
        vol_surface,
        new_atm_vols,
        new_skews,
        new_kurtosis,
        elapsed_time,
        timesteps,
        S_range
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

# --- Animate Vol Surface ---
if plot_volsurf_btn:
    vol_surface = VolSurface(atm_strike=underlying_price, dtes=dtes, atm_vols=atm_vols, skews=skews, kurtosis=kurtosis)
    frames = create_vol_surface_evolution_video(vol_surface, timesteps, new_atm_vols, new_skews, new_kurtosis)
    
    # Example: writing frames to a file, or display as video
    video_filename = "vol_surface.mp4"
    imageio.mimwrite(video_filename, frames, fps=2)
    st.video(video_filename, format="video/mp4")
