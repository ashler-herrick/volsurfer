import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder
from src.chain import Chain

st.set_page_config(layout="wide")
st.title("Vol Surfer - Option Chain")

# Session state initialization
if "portfolio_options" not in st.session_state:
    st.session_state["portfolio_options"] = []

# Create the chain instance from session state variables
chain = Chain(
    dtes=st.session_state["dtes"],
    vol_surface=st.session_state["vol_surface"],
    underlying_price=st.session_state["underlying_price"],
    s_range=st.session_state["s_range"],
    strike_width=st.session_state["strike_width"],
)

# Get the chain dataframe
df = chain.df

# Get unique DTE values
unique_dtes = sorted(df["DTE"].unique())

# Create a tab for each DTE
tabs = st.tabs([f"DTE: {d}" for d in unique_dtes])

for i, d in enumerate(unique_dtes):
    with tabs[i]:
        st.subheader(f"Call Options for DTE = {d}")

        # Filter Calls for current DTE
        call_df = df[(df["DTE"] == d) & (df["Type"] == "Call")].reset_index(drop=True)
        call_gb = GridOptionsBuilder.from_dataframe(call_df)
        call_gb.configure_selection("multiple", use_checkbox=True)
        call_grid_options = call_gb.build()

        # Render AgGrid for Calls
        call_grid_response = AgGrid(call_df, gridOptions=call_grid_options, height=400, fit_columns_on_grid_load=True)
        selected_calls = pd.DataFrame(call_grid_response.get("selected_rows", []))

        st.subheader(f"Put Options for DTE = {d}")

        # Filter Puts for current DTE
        put_df = df[(df["DTE"] == d) & (df["Type"] == "Put")].reset_index(drop=True)
        put_gb = GridOptionsBuilder.from_dataframe(put_df)
        put_gb.configure_selection("multiple", use_checkbox=True)
        put_grid_options = put_gb.build()

        # Render AgGrid for Puts
        put_grid_response = AgGrid(put_df, gridOptions=put_grid_options, height=400, fit_columns_on_grid_load=True)
        selected_puts = pd.DataFrame(put_grid_response.get("selected_rows", []))

        # Combine selected options
        selected_options = pd.concat([selected_calls, selected_puts], ignore_index=True)

        if not selected_options.empty:
            st.write("### Selected Options:")
            st.table(selected_options)

            # Initialize session state for contract sizes
            if "contract_sizes" not in st.session_state:
                st.session_state["contract_sizes"] = {}

            # Create input fields for each selected option
            for index, row in selected_options.iterrows():  # Correctly unpack row data
                option_key = f"{row['Type']}_Strike{row['Strike']}_DTE{row['DTE']}"

                # Default value if not already in session state
                if option_key not in st.session_state["contract_sizes"]:
                    st.session_state["contract_sizes"][option_key] = 1

                # User input for contract size
                st.session_state["contract_sizes"][option_key] = st.number_input(
                    f"Contracts for {row['Type']} Strike {row['Strike']} DTE {row['DTE']}",
                    min_value=-100,
                    max_value=100,
                    value=st.session_state["contract_sizes"][option_key],
                    key=option_key
                )

            # Button to add selected options with contract sizes to portfolio
            if st.button(f"Add Selected Options for DTE {d} to Portfolio"):
                for index, row in selected_options.iterrows():  # Correct loop
                    option_key = f"{row['Type']}_Strike{row['Strike']}_DTE{row['DTE']}"
                    contract_size = st.session_state["contract_sizes"].get(option_key, 1)  # Get stored contract size
                    
                    st.session_state["portfolio_options"].append({
                        "flag": "c" if row["Type"] == "Call" else "p",
                        "strike": row["Strike"],
                        "dte_days": row["DTE"],
                        "pos": contract_size,  # Correct contract size added
                        "underlying_price": st.session_state["underlying_price"],
                    })

                st.success(f"Added {len(selected_options)} option(s) to portfolio!")

# Show the portfolio
st.subheader("Current Portfolio Options")
if st.session_state["portfolio_options"]:
    portfolio_df = pd.DataFrame(st.session_state["portfolio_options"])
    st.table(portfolio_df)
else:
    st.write("No options added yet.")
