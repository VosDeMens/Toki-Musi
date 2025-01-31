import streamlit as st

# from st_pages import get_nav_from_toml, add_page_title

from src.my_types import floatlist
from src.wave_generation import SAMPLE_RATE, marginify_wave


def st_audio(wave: floatlist):
    st.audio(marginify_wave(wave), sample_rate=SAMPLE_RATE, format="audio/wav")


# def show_sidebar() -> None:
#     st.set_page_config(layout="wide")
#     nav = get_nav_from_toml("resources/pages.toml")
#     pg = st.navigation(nav)
#     add_page_title(pg)
#     pg.run()
