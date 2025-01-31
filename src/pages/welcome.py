import streamlit as st

from src.file_management import HOME_TEXT_FILE, load_markdown_from_file

HOME_TEXT = load_markdown_from_file(HOME_TEXT_FILE)

st.write(HOME_TEXT)  # type: ignore
