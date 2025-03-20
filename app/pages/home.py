import streamlit as st
import numpy as np

from ui import parse_csv, init_session_state, init_session_state_csv
from src.contracts import set_risk_free_rate
from src.vol_surface import VolSurface

st.set_page_config(layout="centered")
st.title("Vol Surfer - An Options Calculator")
st.image(r"app\assets\logo.png")

# --- Vol Surface & Simulation Params ---
st.title("Vol Surface and Simulation Parameters")

with st.expander("Underlying and DTEs"):
    underlying_price = st.number_input(
        "Underlying Stock Price", min_value=0.0, max_value=1000.0, 
        value=init_session_state("underlying_price", 100.0)
    )
    dtes_input = st.text_input("DTEs (days)", init_session_state_csv("dtes", "7"))
    strike_width_input = st.number_input("Strike Width", min_value=1, max_value=None, value=init_session_state("strike_width", 5))

with st.expander("Underlying & Simulation Parameters"):
    elapsed_time = st.slider(
        "Elapsed Time (days)", min_value=0.1, max_value=60.0, 
        value=init_session_state("elapsed_time", 10.0), step=0.1
    )
    timesteps = st.slider(
        "Timesteps", min_value=1, max_value=30, 
        value=init_session_state("timesteps", 10)
    )

    s_min_init, s_max_init = (underlying_price * 0.8, underlying_price * 1.2)
    s_min = st.number_input("Min Underlying Price", min_value=0.0, max_value=2000.0, 
                            value=init_session_state("s_min", s_min_init))
    s_max = st.number_input("Max Underlying Price", min_value=0.0, max_value=2000.0, 
                            value=init_session_state("s_max", s_max_init))
    s_points = st.slider("Number of Price Steps", min_value=5, max_value=50, 
                         value=init_session_state("s_points", 20))
    s_range = np.linspace(s_min, s_max, s_points)
    rfr = st.number_input("Risk Free Rate", min_value=0.0, max_value=0.1, 
                          value=init_session_state("rfr", 0.04))

    set_risk_free_rate(rfr)

with st.expander("Current Vol Surface"):
    atm_vols_input = st.text_input("ATM Vols", init_session_state_csv("atm_vols",""))
    skews_input = st.text_input("Skews", init_session_state_csv("skews",""))
    kurtosis_input = st.text_input("Kurtosis",  init_session_state_csv("kurtosis",""))

with st.expander("Future Vol Surface (Optional)"):
    new_atm_vols_input = st.text_input("New ATM Vols", init_session_state_csv("new_atm_vols",""))
    new_skews_input = st.text_input("New Skews", init_session_state_csv("new_skews",""))
    new_kurtosis_input = st.text_input("New Kurtosis",init_session_state_csv("new_kurtosis",""))

# --- Submit Button to Initialize Session State ---
if st.button("Submit"):
    st.session_state["underlying_price"] = underlying_price
    st.session_state["dtes"] = parse_csv(dtes_input)
    st.session_state["strike_width"] = strike_width_input
    st.session_state["elapsed_time"] = elapsed_time
    st.session_state["timesteps"] = timesteps
    st.session_state["s_min"] = s_min
    st.session_state["s_max"] = s_max
    st.session_state["s_points"] = s_points
    st.session_state["s_range"] = s_range
    st.session_state["rfr"] = rfr
    st.session_state["atm_vols"] = parse_csv(atm_vols_input)
    st.session_state["skews"] = parse_csv(skews_input)
    st.session_state["kurtosis"] = parse_csv(kurtosis_input)
    
    st.session_state["new_atm_vols"] = parse_csv(new_atm_vols_input) or st.session_state["atm_vols"]
    st.session_state["new_skews"] = parse_csv(new_skews_input) or st.session_state["skews"]
    st.session_state["new_kurtosis"] = parse_csv(new_kurtosis_input) or st.session_state["kurtosis"]

    # --- Validation Step ---
    length_check = [
        len(st.session_state["dtes"]),
        len(st.session_state["atm_vols"]),
        len(st.session_state["skews"]),
        len(st.session_state["kurtosis"]),
        len(st.session_state["new_atm_vols"]),
        len(st.session_state["new_skews"]),
        len(st.session_state["new_kurtosis"]),
    ]

    if len(set(length_check)) != 1:
        st.error("Error: The lists for DTEs, ATM Vols, Skews, Kurtosis, New ATM Vols, New Skews, and New Kurtosis must all have the same length.")
    else:
        vol_surface = VolSurface(
            atm_strike=st.session_state["underlying_price"],
            dtes=st.session_state["dtes"],
            atm_vols=st.session_state["atm_vols"],
            skews=st.session_state["skews"],
            kurtosis=st.session_state["kurtosis"],
        )

        st.session_state["vol_surface"] = vol_surface
        st.success("Session state variables initialized!")
