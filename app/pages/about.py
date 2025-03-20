import os

import streamlit as st

st.set_page_config(layout="centered")
st.title("About Vol Surfer")
logo_path = os.path.join("app", "assets", "logo.png")
st.image(logo_path)

st.markdown(
    """
    # **Welcome to Vol Surfer!**

    This app is designed to be a fun and interactive tool for researching how **implied volatility surfaces** impact an options portfolio’s **payoff and Greeks**.

    ### **How to Use the App**
    - **Model Setup**: Input the **DTEs** (Days to Expiration) you want to model, along with the **underlying price** and **strike width**.
    - **Assumptions**: The model assumes **zero dividends**.
    - **Simulation Parameters**: You can customize the **elapsed time, number of timesteps, underlying range, and risk-free rate** in the simulation settings dropdown.
    - **Volatility Surface Parameters**: 
      - Specify at least one set of volatility surface parameters.
      - The **ATM Vols** entry should be a comma-separated list of values corresponding to the number of expirations being modeled.
      - **Important:** Volatility values should be in decimal form (e.g., `0.45`, not `45`).
      - The **skew parameter** affects the "tilt" of the surface. A **negative skew** means that implied volatility is higher for OTM puts than for OTM calls (which is typically seen in equities).
      - The **kurtosis parameter** (or **"smile"**) influences the wings of the surface by increasing implied volatility for options further from the underlying.

    ### **Volatility Surface Formula**
    The exact formula used to compute the implied volatility is:

    $$
    \sigma_{atm} + s(m - 1) + k(m - 1)^2
    $$

    where:

    - $$m = \\frac{K}{S}$$ (strike over stock price) is the **moneyness** of the option,
    - $$s$$ is the **skew parameter**, and
    - $$k$$ is the **kurtosis parameter**.

    ### **Option Chain**
    The Option Chain page constructs an option chain for you to build a hypothetical portfolio. 
    Simply select the options to include in your portfolio, then scroll down to the **Selected Options** 
    section to input the number of contracts you want to add. The option chain dynamically updates based on 
    the expiration dates and strike prices selected. 

    Once you have selected your options and set the contract quantities, the portfolio is constructed using 
    the chosen positions. These selections will be used in subsequent pages to analyze portfolio performance 
    and risk metrics.

    ### **Payoff and Greeks**
    The Payoff and Greeks page allows you to analyze the financial impact of your portfolio over time. 
    Here, you can plot the evolution of the portfolio's **profit and loss (PnL)**, as well as track key risk metrics.

    - **Payoff Analysis**: Displays how the portfolio's value changes under different underlying price scenarios.
    - **Greeks Visualization**: Examines how **delta, gamma, theta, vega, and rho** evolve over time, as well as how they respond to changes in the underlying asset price and implied volatility.
    - **Scenario Testing**: If volatility surface evolution parameters are specified, the app simulates how changes in volatility, skew, and kurtosis affect the portfolio over time.

    """
)
