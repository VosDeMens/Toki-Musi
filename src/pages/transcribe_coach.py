import streamlit as st
from random import choice

from src.file_management import (
    load_examples_from_file,
    load_words_from_folder,
    load_markdown_from_file,
    TRANSCRIBE_COACH_INSTRUCTIONS_FILE,
)
from src.util_streamlit import display_example, render_settings
from src.word import Word, InvalidWordException
from src.words_functions import get_words_from_sentence


def combine_examples_and_words(
    examples: list[tuple[str, str]], words: list[Word]
) -> list[tuple[str, str]]:
    combined: dict[str, list[str]] = {}
    for word in words:
        if word.name not in combined:
            combined[word.name] = []
        combined[word.name].append(word.description)

    for tm, eng in examples:
        if tm not in combined:
            combined[tm] = []
        combined[tm].append(eng)

    items = list(combined.items())
    with_joined_translations = [(tm, "\n".join(eng)) for tm, eng in items]

    return with_joined_translations


TRANSCRIBE_COACH_INSTRUCTIONS = load_markdown_from_file(
    TRANSCRIBE_COACH_INSTRUCTIONS_FILE
)

WORDS: list[Word] = load_words_from_folder()
EXAMPLES: list[tuple[str, str]] = load_examples_from_file()
COMBINED: list[tuple[str, str]] = combine_examples_and_words(EXAMPLES, WORDS)


def reset() -> None:
    st.session_state["reference_transcribe"] = choice(COMBINED)
    st.session_state["displayed_sentences_transcribe"] = set()

    if not "allow_keychanges" in st.session_state and (
        "la" in st.session_state["reference_transcribe"][0]
        or "pi" in st.session_state["reference_transcribe"][0]
    ):
        reset()

    try:
        get_words_from_sentence(st.session_state["reference_transcribe"][0], WORDS)
    except InvalidWordException:
        reset()


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

display_example(
    tm,
    en,
    "",
    WORDS,
    "displayed_sentences_transcribe",
)
