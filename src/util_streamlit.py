import streamlit as st

# from st_pages import get_nav_from_toml, add_page_title

from src.my_types import floatlist
from src.wave_generation import SAMPLE_RATE, marginify_wave


def st_audio(wave: floatlist, sample_rate: int = SAMPLE_RATE):
    st.audio(marginify_wave(wave), sample_rate=sample_rate, format="audio/wav")
