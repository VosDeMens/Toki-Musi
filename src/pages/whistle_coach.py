import io
from typing import cast
import parselmouth
import matplotlib.pyplot as plt
import streamlit as st
import numpy as np
from random import choice
from streamlit_mic_recorder import mic_recorder  # type: ignore
from scipy.io import wavfile  # type: ignore


from src.constants import SAMPLE_RATE
from src.note import Note, turn_into_notes_strings
from src.util_streamlit import st_audio
from src.wave_generation import marginify_wave
from src.whistle_analysis import (
    analyse_recording_to_notes,
    cut_notes_sentence_into_notes_per_word,
    extract_recording_per_word,
    find_closest_words_for_notes_string,
    freqs_to_float_pitches,
    get_synthesised_versions_of_words,
    merge_into_one_wave,
    pitch_string_by,
)
from src.word import (
    InvalidWordException,
    Word,
    make_printable,
)
from src.words_functions import get_sentence_wave, get_words_from_sentence
from src.my_types import floatlist
from src.file_management import (
    load_examples_from_file,
    load_markdown_from_file,
    WHISTLE_COACH_INSTRUCTIONS_FILE,
    load_words_from_folder,
)

INTRUCTIONS = load_markdown_from_file(WHISTLE_COACH_INSTRUCTIONS_FILE)

WORDS_WITHOUT_SLIDES = [
    w
    for w in load_words_from_folder()
    if "/" not in w.notes_string
    and "\\" not in w.notes_string
    and "^" not in w.notes_string
    and "*" not in w.notes_string
]


def get_examples_with_words(
    words: list[Word], include_words: bool = True
) -> list[tuple[str, str]]:
    all_examples = load_examples_from_file()
    filtered_examples = all_examples[:]
    for example in all_examples:
        tm, _ = example
        try:
            words_sentence = get_words_from_sentence(tm, words)
            for w in words_sentence:
                if w.past_tense and w.question:
                    filtered_examples.remove(example)
        except InvalidWordException:
            filtered_examples.remove(example)
    if include_words:
        tms = [tm for tm, _ in filtered_examples]
        for word in words:
            if word.name not in tms and word.nr_of_notes >= 2:
                filtered_examples.append((word.name, word.description))
    return filtered_examples


EXAMPLES = get_examples_with_words(WORDS_WITHOUT_SLIDES)


def plot_with_target(
    recording: floatlist, synthesised_version: floatlist, offset: float
):
    """Displays a plot of the pitch of a recording, against the pitch of a corrected version.

    Parameters
    ----------
    recording : floatlist
        The recording to plot the pitch of.
    synthesised_version : floatlist
        The corrected version to plot the pitch of.
    offset : float
        The pitch to consider 0, expressed in semitones from the standard key.
    """
    snd_recording = parselmouth.Sound(  # type: ignore
        recording, sampling_frequency=st.session_state["sample_rate"]
    )
    pm_recording = snd_recording.to_pitch_ac(pitch_floor=st.session_state["f_min"], pitch_ceiling=st.session_state["f_max"], silence_threshold=0.1)  # type: ignore
    frequencies_recording = np.array(pm_recording.selected_array["frequency"], dtype=float)  # type: ignore
    pitch_recording = freqs_to_float_pitches(frequencies_recording) - offset

    snd_synth = parselmouth.Sound(  # type: ignore
        synthesised_version, sampling_frequency=st.session_state["sample_rate"]
    )
    pm_synth = snd_synth.to_pitch_ac(pitch_floor=st.session_state["f_min"], pitch_ceiling=st.session_state["f_max"], silence_threshold=0.1)  # type: ignore
    frequencies_synth = np.array(pm_synth.selected_array["frequency"], dtype=float)  # type: ignore
    pitch_synth = (
        freqs_to_float_pitches(frequencies_synth)
        - 12 * st.session_state["octave"]
        - offset
    )

    # Plot pitch
    plt.plot(pm_recording.xs(), pitch_recording, label="Recording")  # type: ignore
    plt.plot(pm_recording.xs(), pitch_synth, label="Target")  # type: ignore
    plt.xlabel("Time (s)")  # type: ignore
    plt.ylabel("Pitch (semitones)")  # type: ignore
    plt.title("Whistle Pitch Analysis")  # type: ignore
    plt.legend(loc="upper left")  # type: ignore
    ax = plt.gca()
    y_min = float(min(-5, np.nanmin(pitch_recording), np.nanmin(pitch_synth)) - 1)
    y_max = float(max(9, np.nanmax(pitch_recording), np.nanmax(pitch_synth)) + 1)
    ax.set_ylim(y_min, y_max)
    st.pyplot(plt)  # type: ignore


def analyse_and_show_analysis():
    audio_bytes = st.session_state.my_recorder_output["bytes"]

    audio_buffer = io.BytesIO(audio_bytes)
    sample_rate, audio_data = wavfile.read(audio_buffer)  # type: ignore
    st.session_state["sample_rate"] = cast(int, sample_rate)
    audio_data = cast(floatlist, audio_data)

    st_audio(audio_data, sample_rate)

    notes_from_recording, segment_bounds, new_word_flags, offset, sample_rate_pm = (
        analyse_recording_to_notes(
            audio_data,
            st.session_state["sample_rate"],
            st.session_state["f_min"],
            st.session_state["f_max"],
        )
    )

    strings_from_recording: list[str] = turn_into_notes_strings(notes_from_recording)
    print(f"{strings_from_recording = }")
    target_words: list[Word | None] = []
    usable_reference = False

    if st.session_state["reference"] != "":
        try:
            target_words = cast(
                list[Word | None],
                get_words_from_sentence(
                    st.session_state["reference"], WORDS_WITHOUT_SLIDES
                ),
            )
            nr_of_sounded_target_words = len(
                [
                    w
                    for w in target_words
                    if w is not None and w.nr_of_notes != 0 and w.name != "rest"
                ]
            )
            if nr_of_sounded_target_words == len(strings_from_recording):
                usable_reference = True
            else:
                st.write(  # type: ignore
                    "Different number of words detected from reference sentence, whistle interpreted freely."
                )

        except InvalidWordException:
            st.write("Reference sentence invalid, whistle interpreted freely.")  # type: ignore

    if not usable_reference:
        for i in range(len(strings_from_recording)):
            s = strings_from_recording[i]
            # try:
            print(f"{s = }")
            if (result := find_closest_words_for_notes_string(s)) is None:
                target_words.append(None)
            else:
                best_match, d_offset = result
                target_words += best_match
                for j in range(i, len(strings_from_recording)):
                    strings_from_recording[j] = pitch_string_by(
                        strings_from_recording[j], d_offset
                    )
            # except:
            #     raise Exception

    for i, word in enumerate(target_words):
        if word is None or word.nr_of_notes == 0 or word.name == "rest":
            strings_from_recording.insert(i, "")

    print(f"{strings_from_recording = }")
    print(f"{target_words = }")

    strings_to_print = [
        (
            target_word.get_notes_string(True)
            if target_word is not None
            else make_printable(string_from_recording)
        )
        for target_word, string_from_recording in zip(
            target_words, strings_from_recording
        )
    ]
    print(f"{strings_to_print = }")

    word_names = [
        f"({str(word)})" if word is not None else "(???)" for word in target_words
    ]
    print(f"{word_names = }")

    notes_per_word: list[list[Note]] = cut_notes_sentence_into_notes_per_word(
        notes_from_recording, target_words
    )

    for notes_for_word in notes_per_word:
        print(f"{len(notes_for_word) = }")

    recording_per_word: list[floatlist | None] = extract_recording_per_word(
        audio_data,
        new_word_flags,
        segment_bounds,
        target_words,
        st.session_state["sample_rate"],
        sample_rate_pm,
    )

    synthesised_versions_of_words: list[floatlist | None] = (
        get_synthesised_versions_of_words(
            target_words,
            notes_per_word,
            segment_bounds,
            offset + st.session_state["octave"] * 12,
            st.session_state["sample_rate"],
            sample_rate_pm,
        )
    )
    print(f"{len(synthesised_versions_of_words) = }")

    full_wave: floatlist = merge_into_one_wave(
        synthesised_versions_of_words,
        len(audio_data),
        segment_bounds,
        new_word_flags,
        st.session_state["sample_rate"],
        sample_rate_pm,
    )

    st.divider()
    st.header("Whistle Coach's interpretation:")

    for string, name in zip(strings_to_print, word_names):
        st.write(string, name)  # type: ignore

    st.header("Deviations:")
    plot_with_target(audio_data, full_wave, offset)

    st.header("Word by word feedback:")

    print("AAAAA")
    print(f"{target_words = }")
    print(f"{recording_per_word = }")
    print(f"{synthesised_versions_of_words = }")

    for word, recording_word, synthesised_word in zip(
        target_words,
        recording_per_word,
        synthesised_versions_of_words,
    ):
        if word is not None:
            st.header(str(word))
        else:
            st.header("???")

        if word is not None and word.name == "pi":
            st.write("This word is represented by a key change up by 2 semitones")  # type: ignore
        elif word is not None and word.name in ["la", "unpi"]:
            st.write("This word is represented by a key change down by 2 semitones")  # type: ignore
        elif recording_word is None:
            st.write("This really shouldn't happen")  # type: ignore
        else:
            st.write("Your audio:")  # type: ignore
            st_audio(recording_word, st.session_state["sample_rate"])
            if synthesised_word is not None:
                st.write("Corrected version:")  # type: ignore
                st_audio(synthesised_word, st.session_state["sample_rate"])
            else:
                st.write("No correction available")  # type: ignore


def callback():
    if "my_recorder_output" not in st.session_state:
        st.write("Recording failed. This never happened in testing so I have no clue, maybe something with your mic?")  # type: ignore
        return


# Build the page

if "speed" not in st.session_state:
    st.session_state["speed"] = 10
if "prefer_composites" not in st.session_state:
    st.session_state["prefer_composites"] = False
if "allow_keychanges" not in st.session_state:
    st.session_state["allow_keychanges"] = False
if "f_min" not in st.session_state:
    st.session_state["f_min"] = 300
if "f_max" not in st.session_state:
    st.session_state["f_max"] = 4000
if "octave" not in st.session_state:
    st.session_state["octave"] = -1
if "reference" not in st.session_state:
    st.session_state["reference"] = ""
if "sample_rate" not in st.session_state:
    st.session_state["sample_rate"] = SAMPLE_RATE


with st.expander("Who is Whistle Coach??"):
    st.subheader("Hello I am Whistle Coach.")
    st.write(INTRUCTIONS)  # type: ignore

with st.expander("Settings"):
    st.subheader("Speed")
    st.write(  # type: ignore
        "The playback speed of the example sentence. You don't need to match this in your recording."
    )
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
    st.divider()
    st.subheader("Prefer composites")
    st.markdown(  # type: ignore
        'If two words belong together, you can turn their melodies into one melody. Check the <a href="./guide" style="color:#FF0000;">guide</a> for more information on how that works. If you select this option, established combinations of words will be turned into composite words.',
        unsafe_allow_html=True,
    )
    st.checkbox(
        " ",
        value=st.session_state["prefer_composites"],
        key="prefer_composites_input",
        on_change=lambda: setattr(
            st.session_state,
            "prefer_composites",
            st.session_state["prefer_composites_input"],
        ),
    )
    st.divider()
    st.subheader("Allow keychanges")
    st.write(  # type: ignore
        "When loading a random reference sentence, allow sentences with key changes (more difficult)."
    )
    st.checkbox(
        " ",
        value=st.session_state["allow_keychanges"],
        key="allow_keychanges_input",
        on_change=lambda: setattr(
            st.session_state,
            "allow_keychanges",
            st.session_state["allow_keychanges_input"],
        ),
    )
    st.divider()
    st.subheader("Min frequency")
    st.write(  # type: ignore
        "The lowest frequency in your range. For whistling, you can leave this alone."
    )
    st.text_input(
        " ",
        value=str(st.session_state["f_min"]),
        key="f_min_input",
        on_change=lambda: setattr(
            st.session_state, "f_min", int(st.session_state["f_min_input"])
        ),
    )
    st.divider()
    st.subheader("Max frequency")
    st.write(  # type: ignore
        "The highest frequency in your range. For whistling, you can leave this alone."
    )
    st.text_input(
        " ",
        value=str(st.session_state["f_max"]),
        key="f_max_input",
        on_change=lambda: setattr(
            st.session_state, "f_max", int(st.session_state["f_max_input"])
        ),
    )
    st.divider()
    st.subheader("Octave offset correction")
    st.write("Whistles are really high pitched, so by default, the synthesised sounds in the corrections are pitched down by an octave, as to not be super jarring. If you're gonna sing, you might want to set this to 0, or even 1 if you have a low voice.")  # type: ignore
    st.slider(
        " ",
        -1,
        1,
        value=st.session_state["octave"],
        step=1,
        key="octave_input",
        on_change=lambda: setattr(
            st.session_state, "octave", st.session_state["octave_input"]
        ),
    )

st.divider()
st.subheader("Reference sentence")

st.text_input(
    " ",
    value=st.session_state["reference"],
    key="reference_input",
    on_change=lambda: setattr(
        st.session_state, "reference", st.session_state["reference_input"]
    ),
)

try:
    if st.session_state["reference"]:
        words_in_sentence = get_words_from_sentence(
            st.session_state["reference"],
            WORDS_WITHOUT_SLIDES,
            st.session_state["prefer_composites"],
        )
        if st.session_state["reference"] in (
            dictionary := {tm: en for tm, en in EXAMPLES}
        ):
            st.write(f'Meaning: {dictionary[st.session_state["reference"]]}')  # type: ignore
        st.write(  # type: ignore
            f"Notes string:&nbsp;&nbsp;&nbsp;{'&nbsp;&nbsp;&nbsp;'.join(w.get_notes_string(True) for w in words_in_sentence)}"
        )
        st_audio(
            marginify_wave(
                get_sentence_wave(
                    words_in_sentence,
                    speed=st.session_state["speed"],
                    sample_rate=st.session_state["sample_rate"],
                )
            ),
            st.session_state["sample_rate"],
        )
except InvalidWordException:
    st.write("Invalid sentence")  # type: ignore


st.button(
    "Randomise",
    on_click=lambda: setattr(
        st.session_state,
        "reference",
        choice(
            [
                tm
                for tm, _ in EXAMPLES
                if st.session_state["allow_keychanges"]
                or (" la " not in tm and " pi " not in tm)
            ]
        ),
    ),
)

st.divider()
mic_recorder(
    stop_prompt="Recording! Click to end.",
    key="my_recorder",
    callback=callback,
    format="wav",
)

if (
    "my_recorder_output" in st.session_state
    and st.session_state["my_recorder_output"] is not None
):
    # try:
    analyse_and_show_analysis()
    # except:
    #     st.divider()
    #     st.write("Something went wrong, but do try again!!!")  # type: ignore
