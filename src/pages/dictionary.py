import streamlit as st

from src.util_streamlit import st_audio
from src.word import (
    InvalidWordException,
    Word,
)
from src.words_functions import (
    get_prevalence,
    get_words_from_sentence,
    get_sentence_wave,
)
from src.file_management import (
    load_examples_from_file,
    load_words_from_folder,
)


WORDS = load_words_from_folder()
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


def update_filters() -> None:
    """Filters out words that we don't want to display, and updates `st.session_state`."""
    setattr(st.session_state, "nr_of_notes", st.session_state["nr_of_notes_input"])
    setattr(st.session_state, "toki_pona", st.session_state["toki_pona_input"])
    setattr(st.session_state, "particle", st.session_state["particle_input"])
    setattr(st.session_state, "content_word", st.session_state["content_word_input"])
    setattr(st.session_state, "preposition", st.session_state["preposition_input"])
    setattr(st.session_state, "interjection", st.session_state["interjection_input"])
    setattr(st.session_state, "colour", st.session_state["colour_input"])
    setattr(st.session_state, "atomic", st.session_state["atomic_input"])
    st.session_state["words"] = filter_words(WORDS)


def filter_words(words: list[Word]) -> list[Word]:
    """Filters out words that we don't want to display, and returns the rest.

    Parameters
    ----------
    words : list[Word]
        A `list` of words to filter.

    Returns
    -------
    list[Word]
        A filtered `list` of words.
    """
    filtered = words.copy()
    if st.session_state["nr_of_notes"]:
        filtered = filter(lambda w: w.nr_of_notes == st.session_state["nr_of_notes"], filtered)  # type: ignore
    if st.session_state["toki_pona"]:
        filtered = filter(lambda w: w.toki_pona, filtered)  # type: ignore
    if st.session_state["particle"]:
        filtered = filter(lambda w: w.particle, filtered)  # type: ignore
    if st.session_state["content_word"]:
        filtered = filter(lambda w: w.content_word, filtered)  # type: ignore
    if st.session_state["preposition"]:
        filtered = filter(lambda w: w.preposition, filtered)  # type: ignore
    if st.session_state["interjection"]:
        filtered = filter(lambda w: w.interjection, filtered)  # type: ignore
    if st.session_state["colour"]:
        filtered = filter(lambda w: w.colour, filtered)  # type: ignore
    return list(filtered)  # type: ignore


# Building the page

if "words" not in st.session_state:
    st.session_state["words"] = WORDS
if "clicked_buttons" not in st.session_state:
    st.session_state["clicked_buttons"] = set()
if "loaded_examples" not in st.session_state:
    st.session_state["loaded_examples"] = {}
if "displayed_sentences" not in st.session_state:
    st.session_state["displayed_sentences"] = set()
if "nr_of_notes" not in st.session_state:
    st.session_state["nr_of_notes"] = 0
if "toki_pona" not in st.session_state:
    st.session_state["toki_pona"] = False
if "particle" not in st.session_state:
    st.session_state["particle"] = False
if "content_word" not in st.session_state:
    st.session_state["content_word"] = False
if "preposition" not in st.session_state:
    st.session_state["preposition"] = False
if "interjection" not in st.session_state:
    st.session_state["interjection"] = False
if "colour" not in st.session_state:
    st.session_state["colour"] = False
if "atomic" not in st.session_state:
    st.session_state["atomic"] = True

with st.expander("Filters"):
    st.number_input(
        "Number of Notes (gliding counts as one note, set to 0 to disable filter)",
        min_value=0,
        step=1,
        value=st.session_state["nr_of_notes"],
        key="nr_of_notes_input",
        on_change=update_filters,
    )
    st.checkbox(
        "Taken from Toki Pona (slight changes apply)",
        value=st.session_state["toki_pona"],
        key="toki_pona_input",
        on_change=update_filters,
    )
    st.checkbox(
        "Is a particle",
        value=st.session_state["particle"],
        key="particle_input",
        on_change=update_filters,
    )
    st.checkbox(
        "Is a content word",
        value=st.session_state["content_word"],
        key="content_word_input",
        on_change=update_filters,
    )
    st.checkbox(
        "Is a preposition",
        value=st.session_state["preposition"],
        key="preposition_input",
        on_change=update_filters,
    )
    st.checkbox(
        "Is a interjection",
        value=st.session_state["interjection"],
        key="interjection_input",
        on_change=update_filters,
    )
    st.checkbox(
        "Is a colour",
        value=st.session_state["colour"],
        key="colour_input",
        on_change=update_filters,
    )
    st.checkbox(
        "Is atomic (not a combination of other words put together)",
        value=st.session_state["atomic"],
        key="atomic_input",
        on_change=update_filters,
    )

st.header("The Words")

for word in sorted(st.session_state["words"], key=get_prevalence, reverse=True):
    if not word.composite:
        display_word(word)
