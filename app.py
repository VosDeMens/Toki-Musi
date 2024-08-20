from typing import Any
import streamlit as st
from wave_generation import SAMPLE_RATE, marginify_wave
from words import (
    InvalidWordException,
    Word,
    get_words_from_sentence,
    get_sentence_wave,
)
from local_stuff import load_examples_from_file, load_words_from_folder, WORDS_FOLDER

WORDS = load_words_from_folder([WORDS_FOLDER])
EXAMPLES = load_examples_from_file()

st.set_page_config(layout="wide")

st.title("Toki Musi")


def display_word(word: Word):
    with st.expander(str(word)):
        # st.header(str(word))  # type: ignore
        st.write(word.description, unsafe_allow_html=True)  # type: ignore
        st.write(f"notes: {word.get_notes_string(True)}")  # type: ignore
        st.audio(
            marginify_wave(word.wave()), sample_rate=SAMPLE_RATE, format="audio/wav"
        )
        if word.etymelogies:
            st.header("Etymelogy")
        for etymelogy in word.etymelogies:
            st.write(etymelogy)  # type: ignore
        if len(EXAMPLES):
            st.divider()
            st.header("Examples")
        for example_raw in EXAMPLES:
            try:
                toki_musi_string, _ = example_raw.split(" - ")
                words_in_sentence = get_words_from_sentence(toki_musi_string, WORDS)
                if word.name not in [w.name for w in words_in_sentence]:
                    continue
                st.write(example_raw)  # type: ignore
                st.audio(
                    marginify_wave(get_sentence_wave(words_in_sentence)),
                    sample_rate=SAMPLE_RATE,
                    format="audio/wav",
                )

            except InvalidWordException:
                pass


def sentences_match(sentence_input: list[Word], sentence_actual: list[Word]) -> bool:
    if len(sentence_input) != len(sentence_actual):
        return False
    for w_input, w_actual in zip(sentence_input, sentence_actual):
        if w_input != w_actual:
            return False
    return True


def apply_filters(filters: dict[str, Any]):
    st.session_state["words"] = filter_words(WORDS, filters)


def filter_words(words: list[Word], filters: dict[str, str | int]) -> list[Word]:
    filtered = words.copy()
    if filters["nr_of_notes"]:
        filtered = filter(lambda w: w.nr_of_notes == filters["nr_of_notes"], filtered)
    if filters["toki_pona"]:
        filtered = filter(lambda w: w.toki_pona, filtered)
    if filters["particle"]:
        filtered = filter(lambda w: w.particle, filtered)
    if filters["content_word"]:
        filtered = filter(lambda w: w.content_word, filtered)
    if filters["preposition"]:
        filtered = filter(lambda w: w.preposition, filtered)
    if filters["interjection"]:
        filtered = filter(lambda w: w.interjection, filtered)
    if filters["colour"]:
        filtered = filter(lambda w: w.colour, filtered)
    return list(filtered)


st.session_state["words"] = WORDS

st.title("Dictionary")

with st.expander("Filter words"):
    filters: dict[str, Any] = {
        "nr_of_notes": 0,
        "toki_pona": False,
        "particle": False,
        "content_word": False,
        "preposition": False,
        "interjection": False,
        "colour": False,
    }
    filters["nr_of_notes"] = st.number_input(
        "Number of Notes (gliding counts as one note, set to 0 to disable filter)",
        min_value=0,
        step=1,
        key="filter_nr_of_notes",
        on_change=apply_filters(filters),
    )
    filters["toki_pona"] = st.checkbox(
        "Taken from Toki Pona (slight changes apply)",
        key="filter_toki_pona",
        on_change=apply_filters(filters),
    )
    filters["particle"] = st.checkbox(
        "Is a particle", key="filter_particle", on_change=apply_filters(filters)
    )
    filters["content_word"] = st.checkbox(
        "Is a content word",
        key="filter_content_word",
        on_change=apply_filters(filters),
    )
    filters["preposition"] = st.checkbox(
        "Is a preposition",
        key="filter_preposition",
        on_change=apply_filters(filters),
    )
    filters["interjection"] = st.checkbox(
        "Is an interjection",
        key="filter_interjection",
        on_change=apply_filters(filters),
    )
    filters["colour"] = st.checkbox(
        "Is a colour", key="filter_colour", on_change=lambda: apply_filters(filters)
    )

st.header("the words")

for word in st.session_state["words"]:
    display_word(word)
