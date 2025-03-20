import streamlit as st
import pandas as pd
import imageio

from ui import remove_option_ui
from portfolio import (
    build_portfolio,
    plot_pnl_evolution,
    plot_all_greeks,
)
from src.vol_surface import VolSurface, create_vol_surface_evolution_video

st.set_page_config(layout="centered")
st.title("Vol Surfer - Payoff Visualizer")

st.subheader("Current Portfolio Options")
if st.session_state["portfolio_options"]:
    df = pd.DataFrame(st.session_state["portfolio_options"])
    st.table(df)
else:
    st.write("No options added yet.")

remove_option_ui("portfolio_options")

# --- Buttons for Plotting ---
btn1, btn2, btn3, btn4 = st.columns(4)
with btn1:
    plot_value_btn = st.button("Plot PnL Evolution")

with btn2:
    plot_greek_btn = st.button("Plot Greek Evolution")

with btn3:
    plot_volsurf_btn = st.button("Plot Vol Surface")

with btn4:
    animate_volsurf_btn = st.button("Animate Vol Surface")

# --- Plot Value Evolution ---
if plot_value_btn:
    portfolio = build_portfolio(
        st.session_state["underlying_price"], st.session_state["portfolio_options"]
    )
    vol_surface = VolSurface(
        atm_strike=st.session_state["underlying_price"],
        dtes=st.session_state["dtes"],
        atm_vols=st.session_state["atm_vols"],
        skews=st.session_state["skews"],
        kurtosis=st.session_state["kurtosis"],
    )
    st.text(
        f"Portfolio Initial Value: {round(portfolio.portfolio_value(vol_surface), 6)}"
    )
    st.header("3D Portfolio Evolution: PnL")
    fig = plot_pnl_evolution(
        portfolio=portfolio,
        vol_surface=vol_surface,
        new_atm_vols=st.session_state["new_atm_vols"],
        new_skews=st.session_state["new_skews"],
        new_kurtosis=st.session_state["new_kurtosis"],
        elapsed_time=st.session_state["elapsed_time"],
        timesteps=st.session_state["timesteps"],
        s_range=st.session_state["s_range"],
    )
    st.pyplot(fig, use_container_width=True)

# --- Plot Greek Evolution ---
if plot_greek_btn:
    portfolio = build_portfolio(
        st.session_state["underlying_price"], st.session_state["portfolio_options"]
    )
    vol_surface = VolSurface(
        atm_strike=st.session_state["underlying_price"],
        dtes=st.session_state["dtes"],
        atm_vols=st.session_state["atm_vols"],
        skews=st.session_state["skews"],
        kurtosis=st.session_state["kurtosis"],
    )

    st.header("3D Portfolio Evolution: All Greeks")
    figs = plot_all_greeks(
        portfolio=portfolio,
        vol_surface=vol_surface,
        new_atm_vols=st.session_state["new_atm_vols"],
        new_skews=st.session_state["new_skews"],
        new_kurtosis=st.session_state["new_kurtosis"],
        elapsed_time=st.session_state["elapsed_time"],
        timesteps=st.session_state["timesteps"],
        s_range=st.session_state["s_range"],
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
        atm_strike=st.session_state["underlying_price"],
        dtes=st.session_state["dtes"],
        atm_vols=st.session_state["atm_vols"],
        skews=st.session_state["skews"],
        kurtosis=st.session_state["kurtosis"],
    )
    fig = vol_surface.plot_surface()
    st.pyplot(fig)

# --- Animate Vol Surface ---
if animate_volsurf_btn:
    vol_surface = VolSurface(
        atm_strike=st.session_state["underlying_price"],
        dtes=st.session_state["dtes"],
        atm_vols=st.session_state["atm_vols"],
        skews=st.session_state["skews"],
        kurtosis=st.session_state["kurtosis"],
    )
    frames = create_vol_surface_evolution_video(
        vol_surface=vol_surface,
        timesteps=st.session_state["timesteps"],
        new_atm_vols=st.session_state["new_atm_vols"],
        new_skews=st.session_state["new_skews"],
        new_kurtosis=st.session_state["new_kurtosis"],
    )

    # Example: writing frames to a file, or display as video
    video_filename = "vol_surface.mp4"
    imageio.mimwrite(video_filename, frames, fps=2)
    st.video(video_filename, format="video/mp4")
