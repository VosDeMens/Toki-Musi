import streamlit as st

from src.file_management import WELCOME_TEXT_FILE, load_markdown_from_file

WELCOME_TEXT = load_markdown_from_file(WELCOME_TEXT_FILE)

st.write(WELCOME_TEXT, unsafe_allow_html=True)  # type: ignore
