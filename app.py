import streamlit as st
from st_pages import get_nav_from_toml, add_page_title

# if "page_config_set" not in st.session_state:
#     st.set_page_config(layout="wide")
#     st.session_state["page_config_set"] = True  # Ensure

st.set_page_config(layout="wide")
nav = get_nav_from_toml("resources/pages.toml")
pg = st.navigation(nav)
add_page_title(pg)
pg.run()
