import streamlit as st
from src.file_management import (
    load_words_from_folder,
    load_examples_from_file,
    load_markdown_from_file,
    TRANSCRIBE_COACH_INSTRUCTIONS_FILE,
)
from src.util_streamlit import st_audio
from words import InvalidWordException, Word, get_sentence_wave, get_words_from_sentence
from random import choice

WORDS = load_words_from_folder()
INSTRUCTIONS = load_markdown_from_file(TRANSCRIBE_COACH_INSTRUCTIONS_FILE)


def get_dict_from_examples_with_words(words: list[Word]) -> dict[str, str]:
    all_examples = load_examples_from_file()
    all_examples_splat = [example.split(" - ") for example in all_examples]
    filtered_examples_splat = all_examples_splat[:]
    for example in all_examples_splat:
        tm, _ = example
        try:
            get_words_from_sentence(tm, words)
        except InvalidWordException:
            filtered_examples_splat.remove(example)
    filtered_examples_dict = {key: value for key, value in filtered_examples_splat}
    return filtered_examples_dict


EXAMPLES_DICT = get_dict_from_examples_with_words(WORDS)


def get_lingo_sentence(
    words_in_input: list[Word], words_in_sentence: list[Word]
) -> str:
    lingo_baby: list[str] = []
    for w_input, w_sentence in zip(words_in_input, words_in_sentence):
        if w_input == w_sentence:
            lingo_baby.append("green")
        elif w_input.name == w_sentence.name:
            lingo_baby.append("blue")
        elif w_input in words_in_sentence:
            lingo_baby.append("orange")
        elif w_input.name in [w_s.name for w_s in words_in_sentence]:
            lingo_baby.append("violet")
        else:
            lingo_baby.append("red")

    sentence = " ".join(
        [f":{colour}[{w_input}]" for w_input, colour in zip(words_in_input, lingo_baby)]
    )
    return sentence


if "sentence" not in st.session_state:
    st.session_state["sentence"] = None

st.title("Transcribe Coach")

with st.expander("Who is Transcribe Coach??"):
    st.subheader("Hello I am Transcribe Coach.")
    st.write(INTRUCTIONS)  # type: ignore

with st.expander("Settings"):
    st.subheader("Speed")
    st.write("The playback speed of the sentence.")  # type: ignore
    st.slider(
        " ",
        1,
        15,
        value=st.session_state["speed"],
        key="speed_input",
        on_change=lambda: setattr(
            st.session_state, "speed", st.session_state["speed_input"]
        ),
    )

st.write(INSTRUCTIONS)  # type: ignore

st.button(
    "New sentence",
    on_click=lambda: setattr(
        st.session_state, "reference", choice(list(EXAMPLES_DICT.keys()))
    ),
)
# while True:
try:
    toki_musi_string, translation_string = choice(list(EXAMPLES_DICT.items()))
    words_in_sentence = get_words_from_sentence(toki_musi_string, WORDS)
    wave = get_sentence_wave(words_in_sentence)
    st_audio(wave)
    st.session_state[toki_musi_string] = st.text_input(
        "Give it a try", key=f"{toki_musi_string} input"
    )
    if st.button("Submit", key=f"{toki_musi_string} button"):
        words_in_input = get_words_from_sentence(
            st.session_state[toki_musi_string], WORDS
        )
        sentence = get_lingo_sentence(words_in_input, words_in_sentence)
        if words_in_sentence == words_in_input:
            sentence += f" - {translation_string}"
        st.write(sentence)  # type: ignore
    # break
except InvalidWordException:
    print("help")
