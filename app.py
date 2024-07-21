import streamlit as st
from wave_generation import SAMPLE_RATE
from words import (
    Word,
    get_random_word,
    grammar_indicators,
    pronouns,
    hard_to_classify,
    colours,
    other_two_note_words,
    other_three_note_words,
    other_four_note_words,
    other_nonstandard_words,
    composite_words,
    todo,
)

speed: float = 1

st.title("Toki Musi")

col1, col2 = st.columns(2)


def display_words(words: list[Word], header: str):
    with st.expander(header, True):
        for word in words:
            display_word(word)


def display_word(word: Word):
    st.header(str(word))  # type: ignore
    st.write(word.description, unsafe_allow_html=True)  # type: ignore
    st.write(f"notes: {word.get_notes_string()}")  # type: ignore
    st.audio(word.wave(), sample_rate=SAMPLE_RATE, format="audio/wav")


with col1:
    st.title("Dictionary")

    for words, header in [
        (grammar_indicators, "Grammar indicators"),
        (pronouns, "Pronouns"),
        (hard_to_classify, "Hard to classify"),
        (colours, "Colours"),
        (other_two_note_words, "Other two note words"),
        (other_three_note_words, "Other three note words"),
        (other_four_note_words, "Other four note words"),
        (other_nonstandard_words, "Other nonstandard words"),
        (composite_words, "Composite words"),
    ]:
        display_words(words, header)

with col2:
    st.title("practise")

    if st.button("random word"):
        st.session_state["practise_word"] = get_random_word()

    if "practise_word" in st.session_state:
        st.audio(
            st.session_state["practise_word"].wave(),
            sample_rate=SAMPLE_RATE,
            format="audio/wav",
        )
        if st.button("show"):
            st.write(st.session_state["practise_word"])  # type: ignore

    st.title("to do")
    st.write(todo)  # type: ignore
