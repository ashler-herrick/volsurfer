import streamlit as st

home_page = st.Page("pages/home.py", title="Home")
payoff_page = st.Page("pages/payoff.py", title="Payoff and Greeks")
chain_page = st.Page("pages/chain.py", title="Option Chain")
about_page = st.Page("pages/about.py", title="About")

pg = st.navigation([home_page, chain_page, payoff_page, about_page])
pg.run()
