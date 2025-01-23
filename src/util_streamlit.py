import streamlit as st

from src.my_types import floatlist
from src.wave_generation import SAMPLE_RATE, marginify_wave


def st_audio(wave: floatlist):
    st.audio(marginify_wave(wave), sample_rate=SAMPLE_RATE, format="audio/wav")
