import streamlit as st

from clashes_checking import fill_in_phrase, find_clashes, DUMMY_WORD_NAME, find_unresolved_clashes, get_filtered_words
from wave_generation import (
    SAMPLE_RATE,
    generate_phase_continuous_wave,
    freq_timeline_from_str,
    marginify_wave,
)
from words import (
    InvalidWordException,
    Word,
    get_words_from_sentence,
)
from local_stuff import (
    get_default_word,
    load_examples_from_file,
    load_ku_pairs_from_file,
    load_unimportant_compositions_from_file,
    load_words_from_folder,
    save_examples_to_file,
    save_unimportant_compositions_to_file,
    save_words_to_folder,
)

# Load existing words
WORDS: list[Word] = load_words_from_folder()


def get_examples_with_word(word_name: str) -> list[str]:
    examples: list[str] = load_examples_from_file()
    words: list[Word] = load_words_from_folder()
    examples_with_words: list[str] = []
    for example_raw in examples:
        try:
            splat: list[str] = example_raw.split(" - ")
            toki_musi_string: str = splat[0]
            words_in_sentence = get_words_from_sentence(toki_musi_string, words)
            if word_name in [w.name for w in words_in_sentence]:
                examples_with_words.append(example_raw)
        except InvalidWordException:
            pass
    return examples_with_words


# def word_list_to_string(words: list[Word]):
#     string = " ".join([word.name for word in words])
#     composite_word_names = [w.name for w in WORDS if w.composite]
#     if string in composite_word_names:
#         string = f":green[{string}]"
#     return " ".join([word.name for word in words])


def display_clashes(clashes: list[tuple[list[Word], list[Word], str]], should_update: bool = False):
    composite_words: list[Word] = [word for word in WORDS] # if word.composite]
    composite_word_names: list[str] = [comp.name for comp in composite_words]
    unimportant_compositions: list[str] = load_unimportant_compositions_from_file()
    ku_pairs: list[tuple[list[str], str]] = load_ku_pairs_from_file()

    st.session_state["clash_description"] = st.text_input("description for new composite")
    st.write(st.session_state["clash_description"]) # type: ignore
    st.button("dummy button")
    col_p, col_pb, col_m, col_mb, col_ns, col_ucb = st.columns([2, 1, 2, 1, 2, 1])


    for i, (phrase_with_new_word, matching_phrase, notes_string) in enumerate(clashes):
        phrase_button = True
        phrase_string_clean: str = " ".join([word.name for word in phrase_with_new_word])
        phrase_string_display = phrase_string_clean
        match_button = True
        match_string_clean: str = " ".join([word.name for word in matching_phrase])
        match_string_display = match_string_clean

        if f"{match_string_clean} {notes_string}" in unimportant_compositions or f"{phrase_string_clean} {notes_string}" in unimportant_compositions:
            continue

        if DUMMY_WORD_NAME in phrase_string_clean:
            phrase_button = False
        if len(phrase_with_new_word) != 2:
            phrase_button = False

        if phrase_string_clean in composite_word_names:
            comp_index = composite_word_names.index(phrase_string_clean)
            description = composite_words[comp_index].description
            phrase_string_display = f":green[{phrase_string_clean}] {description}"
            phrase_button = False
        else:
            for pair, tail in ku_pairs:
                if " ".join(pair) == phrase_string_clean:
                    phrase_string_display = f":blue[{phrase_string_clean}] {tail}"
                    break

        if len(matching_phrase) != 2:
            match_button = False
        if match_string_clean in composite_word_names:
            comp_index = composite_word_names.index(match_string_clean)
            description = composite_words[comp_index].description
            match_string_display = f":green[{match_string_clean}] {description}"
            match_button = False
        else:
            for pair, tail in ku_pairs:
                if " ".join(pair) == match_string_clean:
                    match_string_display = f":blue[{match_string_clean}] {tail}"
                    break

        with col_p:
            with st.container(height=40, border=False):
                st.write(phrase_string_display)  # type: ignore
        with col_pb:
            if phrase_button:
                if st.button("yes", key=f"{phrase_string_clean}_{i}"):
                    if "last_clash_description" in st.session_state and st.session_state["clash_description"] == st.session_state["last_clash_description"]:
                        st.write("change description") # type: ignore
                        continue
                    w1, w2 = phrase_with_new_word
                    new_composite_word = Word.compose(w1, w2, st.session_state["clash_description"], notes_string)
                    save_words_to_folder(new_composite_word,composite= True)
                    st.session_state["last_clash_description"] = st.session_state["clash_description"]
            else:
                st.container(height=40, border=False)

        with col_m:
            with st.container(height=40, border=False):
                st.write(match_string_display)  # type: ignore
        with col_mb:
            if match_button and len(matching_phrase) == 2:
                if st.button("yes", key=f"{match_string_clean}_{i}"):
                    if "last_clash_description" in st.session_state and st.session_state["clash_description"] == st.session_state["last_clash_description"]:
                        st.write("change description") # type: ignore
                        continue
                    w1, w2 = matching_phrase
                    new_composite_word = Word.compose(w1, w2, st.session_state["clash_description"], notes_string)
                    save_words_to_folder(new_composite_word, composite=True)
                    st.session_state["last_clash_description"] = st.session_state["clash_description"]
            else:
                st.container(height=40, border=False)

        with col_ns:
            with st.container(height=40, border=False):
                st.write(notes_string)  # type: ignore
        with col_ucb:
            if phrase_button or match_button:
                if st.button("no", key=f"{phrase_string_clean}_{match_string_clean}_disregard_{i}"):
                    if phrase_button:
                        save_unimportant_compositions_to_file(f"{phrase_string_clean} {notes_string}")
                    if match_button:
                        save_unimportant_compositions_to_file(f"{match_string_clean} {notes_string}")
            else:
                st.container(height=40, border=False)


st.set_page_config(layout="wide")

# Streamlit App
st.title("Language Dictionary")

if "just_submitted" not in st.session_state:
    st.session_state["just_submitted"] = False

# Initialize session state for form data
if "word_data" not in st.session_state:
    st.session_state["word_data"] = get_default_word().__dict__

# Select a word to edit
selected_word_name = st.selectbox(
    "Select a word to edit", options=[None] + [word.name for word in WORDS], index=0
)

# Clear form data when a new word is selected
if selected_word_name and not st.session_state["just_submitted"]:
    for word in WORDS:
        if word.name == selected_word_name:
            st.session_state["word_data"] = word.__dict__
            break
else:
    st.session_state["word_data"] = get_default_word().__dict__
    st.session_state["just_submitted"] = False

# st.session_state["last_selected_word_name"] = selected_word_name

# Form for adding or editing a word
st.header("Add or Edit Word")
with st.form(key="word_form"):
    name = st.text_input("Name", value=st.session_state["word_data"]["name"])
    notes_string = st.text_input(
        "Generating Code", value=st.session_state["word_data"]["notes_string"]
    )
    if st.session_state["word_data"]["notes_string"]:
        wave = generate_phase_continuous_wave(
            freq_timeline_from_str(st.session_state["word_data"]["notes_string"])
        )
        st.audio(marginify_wave(wave), sample_rate=SAMPLE_RATE, format="audio/wav")
    description = st.text_input(
        "Description", value=st.session_state["word_data"]["description"]
    )
    nr_of_notes = st.number_input(
        "Number of Notes",
        min_value=1,
        step=1,
        value=st.session_state["word_data"]["nr_of_notes"],
    )
    examples = st.text_area(
        "Examples (double return-separated)",
        value="\n\n".join(
            get_examples_with_word(st.session_state["word_data"]["name"])
        ),
    )
    etymelogies = st.text_area(
        "Etymelogies (double return-separated)",
        value="\n\n".join(st.session_state["word_data"]["etymelogies"]),
    )
    toki_pona = st.checkbox(
        "Toki Pona", value=st.session_state["word_data"]["toki_pona"]
    )
    particle = st.checkbox("Particle", value=st.session_state["word_data"]["particle"])
    content_word = st.checkbox(
        "Content Word", value=st.session_state["word_data"]["content_word"]
    )
    preposition = st.checkbox(
        "Preposition", value=st.session_state["word_data"]["preposition"]
    )
    interjection = st.checkbox(
        "Interjection", value=st.session_state["word_data"]["interjection"]
    )
    pluralizable = st.checkbox(
        "Pluralizable", value=st.session_state["word_data"]["pluralizable"]
    )
    past_tensifiable = st.checkbox(
        "Past Tensifiable", value=st.session_state["word_data"]["past_tensifiable"]
    )
    comparativizable = st.checkbox(
        "Comparativizable", value=st.session_state["word_data"]["comparativizable"]
    )
    questionifiable = st.checkbox(
        "Questionifiable", value=st.session_state["word_data"]["questionifiable"]
    )
    colour = st.checkbox("Colour", value=st.session_state["word_data"]["colour"])
    composite = st.checkbox(
        "Composite", value=st.session_state["word_data"]["composite"]
    )

    submitted = st.form_submit_button("Submit")
    if submitted:
        # Update session state with current form values
        st.session_state["word_data"] = {
            "name": name,
            "notes_string": notes_string,
            "description": description,
            "nr_of_notes": nr_of_notes,
            "etymelogies": etymelogies.split("\n\n"),
            "toki_pona": toki_pona,
            "particle": particle,
            "content_word": content_word,
            "preposition": preposition,
            "interjection": interjection,
            "pluralizable": pluralizable,
            "past_tensifiable": past_tensifiable,
            "comparativizable": comparativizable,
            "questionifiable": questionifiable,
            "colour": colour,
            "composite": composite,
        }
        save_words_to_folder(Word(**st.session_state["word_data"]))
        save_examples_to_file(*examples.split("\n\n"))
        selected_word_name = None
        st.session_state["just_submitted"] = True
        st.rerun()

st.divider()

def search_word_with(
    target: str, k: str = "notes_string", to_remove: list[str] = ["_"]
) -> list[Word]:
    words = load_words_from_folder()
    for r in to_remove:
        for word in words:
            word.__dict__[k] = word.__dict__[k].replace(r, "")
    return [
        load_words_from_folder()[i]
        for i, word in enumerate(words)
        if target in word.__dict__[k]
    ]


with st.form(key="word_composition_form"):
    st.header("Compose existing words")
    st.write("Compose a New Word")  # type: ignore

    # Dropdown menus to select words
    word1 = st.selectbox("Select the first word", WORDS, format_func=lambda w: w.name)
    word2 = st.selectbox("Select the second word", WORDS, format_func=lambda w: w.name)

    # Text fields for notes string and description
    notes_string = st.text_input("Enter the notes string")
    description = st.text_input("Enter the description")

    # Submit button
    submit_button = st.form_submit_button(label="Compose and Save Word")

    if submit_button:
        assert word1 is not None and word2 is not None, "choose words first"
        # Compose the new word
        new_word = Word.compose(word1, word2, description, notes_string)

        # Save the new word to the folder
        save_words_to_folder(new_word)

        st.success(f"Word '{new_word.name}' has been composed and saved.")

st.divider()

st.session_state["note_string_search"] = st.text_input("search for note string")

if st.button("search note string"):
    for word in search_word_with(st.session_state["note_string_search"]):
        st.write(word.name)  # type: ignore
        st.write(word.notes_string)  # type: ignore
    clashes = find_clashes(st.session_state["note_string_search"])
    st.header("clash report")
    display_clashes(clashes)

st.divider()

st.session_state["description_search"] = st.text_input("search for description")

if st.button("search description"):
    for word in search_word_with(
        st.session_state["description_search"], "description", []
    ):
        st.write(word.name)  # type: ignore
        st.write(word.description)  # type: ignore

st.divider()

if "unresolved_words" not in st.session_state:
    st.session_state["unresolved_words"] = [word for word in get_filtered_words() if find_unresolved_clashes(word)]

word_index = st.session_state["report_word_index"] if "report_word_index" in st.session_state else 0
st.session_state["report_word"] = st.selectbox(
    "Select word to see clash report", st.session_state["unresolved_words"], format_func=lambda w: w.name, index=word_index
)
st.session_state["report_word_index"] = st.session_state["unresolved_words"].index(st.session_state["report_word"])
if (
    "report_word" in st.session_state
    and st.session_state["report_word"] is not None
    and "/" not in st.session_state["report_word"].notes_string
):
    st.header(f"clash report {st.session_state["report_word"]} ({st.session_state["report_word"].get_notes_string(True)})")
    clashes = find_clashes(st.session_state["report_word"].notes_string)
    clashes_filled_in = [
        (fill_in_phrase(clash[0], st.session_state["report_word"]), clash[1], clash[2]) for clash in clashes
    ]
    clashes_filtered: list[tuple[list[Word], list[Word], str]] = []
    for phrase, match, string in clashes_filled_in:
        if (match, phrase, string) in clashes_filled_in:
            continue
        clashes_filtered.append((phrase, match, string))

    display_clashes(clashes_filtered, True)
