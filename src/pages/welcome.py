import streamlit as st

from src.file_management import WELCOME_TEXT_FILE, load_markdown_from_file
from src.util_streamlit import replace_TM_with_audio

WELCOME_TEXT = load_markdown_from_file(WELCOME_TEXT_FILE)

with_audio = replace_TM_with_audio(WELCOME_TEXT)

st.write(with_audio, unsafe_allow_html=True)  # type: ignore
