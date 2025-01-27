import streamlit as st

from typing import Any

from src.util_streamlit import st_audio
from src.words import (
    InvalidWordException,
    Word,
    get_words_from_sentence,
    get_sentence_wave,
)
from src.file_management import (
    load_examples_from_file,
    load_words_from_folder,
    WORDS_FOLDER,
)


WORDS = load_words_from_folder([WORDS_FOLDER])
EXAMPLES = load_examples_from_file()


def display_word(word: Word) -> None:
    """Creates an `st.expander` object for `word`, displaying its information.

    Parameters
    ----------
    word : Word
        The word to create an `st.expander` object for.
    """
    with st.expander(str(word)):
        st.write(word.description, unsafe_allow_html=True)  # type: ignore
        st.write(f"notes: {word.get_notes_string(True)}")  # type: ignore
        wave = word.wave()
        if wave is not None:
            st_audio(wave)
        if word.etymelogies:
            st.header("Etymelogy")
        for etymelogy in word.etymelogies:
            st.write(etymelogy)  # type: ignore
        st.divider()
        st.header("Examples")
        if word.name not in st.session_state["loaded_examples"]:
            if st.button(
                f"Load examples for {word}",
                key=f"load_button_{word}",
                on_click=lambda w=word: load_examples_for_word(w),  # type: ignore
            ):
                pass
        else:
            st.write(  # type: ignore
                "These are modified versions of examples taken from https://mun.la, https://sona.pona.la, or conjured up by myself."
            )
            st.write(  # type: ignore
                "You can use this to practise your understanding, but keep in mind that all provided translations should be interpreted as suggestions. Toki Musi, like Toki Pona, is a highly contextual language, so if you thought of a different translation than the one provided, that doesn't mean yours is wrong."
            )
            for tm, en in st.session_state["loaded_examples"][word.name]:
                display_example(tm, en, word.name)


def load_examples_for_word(word: Word) -> None:
    """Stores the relevant examples for `word` in `st.session_state["loaded_examples"]`

    Parameters
    ----------
    word : Word
        The word to load examples for.
    """
    st.session_state["loaded_examples"][word.name] = []
    for tm, en in EXAMPLES:
        try:
            words_in_sentence = get_words_from_sentence(tm, WORDS)
            if word.name not in [w.name for w in words_in_sentence]:
                continue
            st.session_state["loaded_examples"][word.name].append((tm, en))
        except InvalidWordException:
            pass


def display_example(tm: str, en: str, name: str):
    """Displays a particular example for a

    Parameters
    ----------
    tm : str
        The Toki Musi sentence.
    en : str
        The English sentence.
    """
    words_in_sentence = get_words_from_sentence(tm, WORDS)
    st_audio(get_sentence_wave(words_in_sentence))
    id_tm = f"{name}_{tm}"
    if id_tm not in st.session_state["displayed_sentences"]:
        if st.button(
            "Show text version",
            key=id_tm,
            on_click=lambda s=id_tm: st.session_state["displayed_sentences"].add(s),  # type: ignore
        ):
            pass
    else:
        st.write(tm)  # type: ignore

    id_en = f"{name}_{en}"
    if id_en not in st.session_state["displayed_sentences"]:
        if st.button(
            "Show translation",
            key=id_en,
            on_click=lambda s=id_en: st.session_state["displayed_sentences"].add(s),  # type: ignore
        ):
            pass
    else:
        st.write(en)  # type: ignore
    st.divider()


def sentences_match(sentence_input: list[Word], sentence_actual: list[Word]) -> bool:
    """Determines whether two sentences contain the same words, including checks for modifications.

    Parameters
    ----------
    sentence_input : list[Word]
        The input sentence, provided by the user.
    sentence_actual : list[Word]
        The sentence they tried to find.

    Returns
    -------
    bool
        Equality.
    """
    if len(sentence_input) != len(sentence_actual):
        return False
    for w_input, w_actual in zip(sentence_input, sentence_actual):
        if w_input != w_actual:
            return False
    return True


def apply_filters(filters: dict[str, str | int]) -> None:
    """Filters out words that we don't want to display, and updates `st.session_state`.

    Parameters
    ----------
    filters : dict[str, Any]
        The filters to apply.
    """
    st.session_state["words"] = filter_words(WORDS, filters)


def filter_words(words: list[Word], filters: dict[str, str | int]) -> list[Word]:
    """Filters out words that we don't want to display, and returns the rest.

    Parameters
    ----------
    words : list[Word]
        A `list` of words to filter.
    filters : dict[str, str | int]
        The filters to use, represented by the names of the filter, and the values to filter for.

    Returns
    -------
    list[Word]
        A filtered `list` of words.
    """
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


if __name__ == "__main__":
    st.set_page_config(page_title="Dictionary", page_icon="📖", layout="wide")
    if "words" not in st.session_state:
        st.session_state["words"] = WORDS
    if "clicked_buttons" not in st.session_state:
        st.session_state["clicked_buttons"] = set()
    if "loaded_examples" not in st.session_state:
        st.session_state["loaded_examples"] = {}
    if "displayed_sentences" not in st.session_state:
        st.session_state["displayed_sentences"] = set()

    st.title("Toki Musi")

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

    for word in WORDS:
        display_word(word)
