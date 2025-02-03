import streamlit as st
from random import choice

from src.file_management import (
    load_examples_from_file,
    load_words_from_folder,
    load_markdown_from_file,
    TRANSCRIBE_COACH_INSTRUCTIONS_FILE,
)
from src.util_streamlit import display_example, render_settings

WORDS = load_words_from_folder()
EXAMPLES = load_examples_from_file()
TRANSCRIBE_COACH_INSTRUCTIONS = load_markdown_from_file(
    TRANSCRIBE_COACH_INSTRUCTIONS_FILE
)


def reset() -> None:
    st.session_state["reference_transcribe"] = choice(EXAMPLES)
    st.session_state["displayed_sentences_transcribe"] = set()


if (
    "reference_transcribe" not in st.session_state
    or "displayed_sentences_transcribe" not in st.session_state
):
    reset()

with st.expander("Who is Transcribe Coach??"):
    st.write(TRANSCRIBE_COACH_INSTRUCTIONS)  # type: ignore

render_settings(True, True, True, False, False, False)

st.divider()

st.button(
    "Load new example",
    on_click=reset,
)
tm, en = st.session_state["reference_transcribe"]
display_example(tm, en, "", WORDS, "displayed_sentences_transcribe")
