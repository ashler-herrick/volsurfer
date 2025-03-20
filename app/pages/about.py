import os

import streamlit as st

st.title("Vol Surfer - An Options Calculator")
logo_path = os.path.join("app", "assets", "logo.png")
st.image(logo_path)

st.markdown(
    """
    Welcome to **Vol Surfer**!
    This app helps you analyze **options pricing, implied volatility**, and **payoff structures** using interactive charts 
    and an optimizer.
    
    🔹 **Features:**
    -  Visualize **Implied Volatility Surfaces**
    -  Compute **Options Payoff** Scenarios
    -  Optimize **Options Strategies**
    """
)