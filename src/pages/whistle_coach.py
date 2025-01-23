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
from src.note import turn_into_notes_strings
from src.util_streamlit import st_audio
from src.wave_generation import marginify_wave
from src.whistle_analysis import (
    analyse_recording_to_notes,
    cut_notes_sentence_into_notes_per_word,
    extract_individual_words_from_recording,
    find_closest_words_for_notes_string,
    freqs_to_float_pitches,
    get_synthesised_versions_of_words,
    merge_into_one_wave,
    pitch_string_by,
)
from src.words import (
    InvalidWordException,
    Word,
    get_sentence_wave,
    get_words_from_sentence,
    make_printable,
)
from src.my_types import floatlist
from src.file_management import (
    WORDS_FOLDER,
    load_examples_from_file,
    load_markdown_from_file,
    WHISTLE_COACH_INSTRUCTIONS_FILE,
    load_words_from_folder,
)

INTRUCTIONS = load_markdown_from_file(WHISTLE_COACH_INSTRUCTIONS_FILE)

WORDS_WITHOUT_SLIDES = [
    w
    for w in load_words_from_folder([WORDS_FOLDER])
    if "/" not in w.notes_string and "\\" not in w.notes_string
]


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


EXAMPLES_DICT = get_dict_from_examples_with_words(WORDS_WITHOUT_SLIDES)


def plot_with_target(
    recording: floatlist, synthesised_version: floatlist, offset: float
):
    snd_recording = parselmouth.Sound(recording, sampling_frequency=SAMPLE_RATE)  # type: ignore
    # TODO: use f_min an f_max
    pm_recording = snd_recording.to_pitch_ac(pitch_floor=st.session_state["f_min"], pitch_ceiling=st.session_state["f_max"], silence_threshold=0.1)  # type: ignore
    frequencies_recording = np.array(pm_recording.selected_array["frequency"], dtype=float)  # type: ignore
    pitch_recording = freqs_to_float_pitches(frequencies_recording) - offset

    snd_synth = parselmouth.Sound(synthesised_version, sampling_frequency=SAMPLE_RATE)  # type: ignore
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
    st.pyplot(plt)  # type: ignore


def analyse_and_show_analysis():
    audio_bytes = st.session_state.my_recorder_output["bytes"]

    audio_buffer = io.BytesIO(audio_bytes)
    sample_rate, audio_data = wavfile.read(audio_buffer)  # type: ignore
    sample_rate = cast(int, sample_rate)
    audio_data = cast(floatlist, audio_data)

    st.audio(audio_bytes)

    notes_from_recording, segment_bounds, offset, sample_rate_pm = (
        analyse_recording_to_notes(
            audio_data, st.session_state["f_min"], st.session_state["f_max"]
        )
    )

    strings_from_recording = turn_into_notes_strings(notes_from_recording)

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
            if len(target_words) == len(strings_from_recording):
                usable_reference = True
            else:
                st.write(  # type: ignore
                    "Different number of words detected from reference sentence, whistle interpreted freely."
                )

        except InvalidWordException:
            st.write("Reference sentence invalid, whistle interpreted freely.")  # type: ignore

    if not usable_reference:
        target_words = []
        i = 0
        while i < len(strings_from_recording):
            s = strings_from_recording[i]
            try:
                if (result := find_closest_words_for_notes_string(s)) is None:
                    target_words.append(None)
                else:
                    closest_words, d_offset = result
                    target_words += closest_words
                    for mod in closest_words[:-1]:
                        strings_from_recording.insert(i, mod.get_notes_string(True))
                        i += 1
                    for j in range(i, len(strings_from_recording)):
                        strings_from_recording[j] = pitch_string_by(
                            strings_from_recording[j], d_offset
                        )
            except:
                raise Exception
            i += 1
        for i, word in enumerate(target_words):
            if word is not None and word.nr_of_notes == 0:
                strings_from_recording.insert(i, word.get_notes_string())

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

    paired = zip(
        strings_to_print,
        [f"({str(word)})" if word is not None else "(???)" for word in target_words],
    )

    notes_per_word = cut_notes_sentence_into_notes_per_word(
        notes_from_recording, target_words
    )

    individual_words_from_recording = extract_individual_words_from_recording(
        audio_data, notes_per_word, segment_bounds, sample_rate_pm
    )

    synthesised_versions_of_words = get_synthesised_versions_of_words(
        target_words,
        notes_per_word,
        segment_bounds,
        offset + st.session_state["octave"] * 12,
        sample_rate_pm,
    )

    full_wave = merge_into_one_wave(
        synthesised_versions_of_words,
        notes_per_word,
        len(audio_data),
        segment_bounds,
        sample_rate_pm,
    )

    st.divider()
    st.header("Whistle Coach's interpretation:")
    for pair in paired:
        st.write(pair[0], pair[1])  # type: ignore

    st.header("Deviations:")
    plot_with_target(audio_data, full_wave, offset)

    st.header("Word by word feedback:")
    for word, recording_word, synthesised_word in zip(
        target_words,
        individual_words_from_recording,
        synthesised_versions_of_words,
    ):
        if word is not None:
            st.header(str(word))
        else:
            st.header("???")
        st.write("Your audio:")  # type: ignore
        st_audio(recording_word)
        if synthesised_word is not None:
            st.write("Corrected version:")  # type: ignore
            st_audio(synthesised_word)
        else:
            st.write("No correction available")  # type: ignore


def callback():
    if "my_recorder_output" not in st.session_state:
        st.write("Recording failed. This never happened in testing so I have no clue, maybe something with your mic?")  # type: ignore
        return


if "speed" not in st.session_state:
    st.session_state["speed"] = 10
if "f_min" not in st.session_state:
    st.session_state["f_min"] = 300
if "f_max" not in st.session_state:
    st.session_state["f_max"] = 4000
if "octave" not in st.session_state:
    st.session_state["octave"] = -1
if "reference" not in st.session_state:
    st.session_state["reference"] = ""


st.title("Whistle Coach")

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
            st.session_state["reference"], WORDS_WITHOUT_SLIDES
        )
        if st.session_state["reference"] in EXAMPLES_DICT:
            st.write(f'Meaning: {EXAMPLES_DICT[st.session_state["reference"]]}')  # type: ignore
        st.write(  # type: ignore
            f"Notes string:&nbsp;&nbsp;&nbsp;{'&nbsp;&nbsp;&nbsp;'.join(w.get_notes_string(True) for w in words_in_sentence)}"
        )
        st_audio(marginify_wave(get_sentence_wave(words_in_sentence)))
except InvalidWordException:
    st.write("Invalid sentence")  # type: ignore


st.button(
    "Randomise",
    on_click=lambda: setattr(
        st.session_state, "reference", choice(list(EXAMPLES_DICT.keys()))
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
    try:
        analyse_and_show_analysis()
    except:
        st.divider()
        st.write("Something went wrong, but do try again!!!")  # type: ignore
