import numpy as np
import streamlit as st
import re
from typing import Iterator

from src.constants import SAMPLE_RATE
from src.my_types import floatlist
from src.util import audio_to_html
from src.wave_generation import add_pause, marginify_wave, pcw_from_notes_string
from src.whistle_analysis import pitch_string_by
from src.word import Word
from src.words_functions import get_sentence_wave, get_words_from_sentence


TM_WORDS = get_words_from_sentence("toki musi")
TM_AUDIO = get_sentence_wave(TM_WORDS)
TM_HTML = audio_to_html(TM_AUDIO)


def st_audio(wave: floatlist, sample_rate: int = SAMPLE_RATE) -> None:
    st.audio(marginify_wave(wave), sample_rate=sample_rate, format="audio/wav")  # type: ignore


def render_enriched_markdown(md: str) -> None:
    if "try" not in st.session_state:
        st.session_state["try"] = (
            "0:2:4:r:7:r:7__:9:7^:r:4*:r:0__:2/4:-5:0:4:2:-5:0:-5:2____\\"
        )
    expander_header: str | None = None
    content: list[str] = []

    for line in md.split("\n"):
        if len(line) >= 4 and line[:4] == "<!--" and line[-3:] == "-->":
            continue
        if len(line) >= 3 and line[:3] == "## ":
            if expander_header:
                render_section(expander_header, content)
            expander_header = line
            content = []
        else:
            content.append(line)

    if expander_header:
        render_section(expander_header, content)


def render_section(header: str, content: list[str]) -> None:
    for i in range(len(content)):
        line = content[i]
        if line in [n * "\\$" for n in [2, 3, 4]]:
            continue
        else:
            content[i] = enrich_text(line)

    with st.expander(header):
        for line in content:
            if line == 2 * "\\$":
                render_try_yourself()
            elif line == 3 * "\\$":
                render_image()
            elif line == 4 * "\\$":
                render_nose_whistle_cover()
            else:
                # formatted_text = re.sub(r"`([^`]+)`", r"<tt>\1</tt>", line)
                st.markdown(line, unsafe_allow_html=True)


def enrich_text(raw: str) -> str:
    def replacement(match: re.Match[str], include_notes_string: bool) -> str:
        match_string = match.group(0)[1:-3]
        without_parentheses = match_string.replace("(", "").replace(")", "")
        notes_strings = without_parentheses.split(" ")
        for i in range(len(notes_strings)):
            if notes_strings[i] == "+":
                for j in range(i + 1, len(notes_strings)):
                    notes_strings[j] = pitch_string_by(notes_strings[j], 2)
            if notes_strings[i] == "-":
                for j in range(i + 1, len(notes_strings)):
                    notes_strings[j] = pitch_string_by(notes_strings[j], -2)
        pcws = [pcw_from_notes_string(notes_string) for notes_string in notes_strings]
        with_pauses = [add_pause(pcw) for pcw in pcws]
        full_wave: floatlist = np.concatenate(with_pauses)
        html = audio_to_html(full_wave)
        if include_notes_string:
            return f"`{match_string}` {html}"
        else:
            return html

    notes_string_dollar = r"`([^`]+)`\\\$"
    notes_string_amp = r"`([^`]+)`\\\&"
    toki_musi = r"TM"

    patterns = [
        (notes_string_dollar, "$"),
        (notes_string_amp, "&"),
        (toki_musi, "TM"),
    ]

    result_parts: list[str] = []
    last_end = 0
    match_iters = [(re.finditer(pattern, raw), flag) for pattern, flag in patterns]
    active_matches: list[tuple[re.Match[str], Iterator[re.Match[str]], str]] = []
    for match_iter, flag in match_iters:
        first_match = next(match_iter, None)
        if first_match:
            active_matches.append((first_match, match_iter, flag))

    while active_matches:
        next_match = min(active_matches, key=lambda x: x[0].start())
        match, match_iter, flag = next_match
        result_parts.append(raw[last_end : match.start()])
        if flag == "$":
            result_parts.append(replacement(match, True))
        elif flag == "&":
            result_parts.append(replacement(match, False))
        elif flag == "TM":
            result_parts.append(TM_HTML)

        last_end = match.end()
        next_match = next(match_iter, None)
        if next_match:
            active_matches.append((next_match, match_iter, flag))
        active_matches.remove((match, match_iter, flag))

    result_parts.append(raw[last_end:])
    return "".join(result_parts)


def replace_TM_with_audio(text: str) -> str:
    return text.replace("TM", TM_HTML)


def render_try_yourself() -> None:
    st.text_input(
        " ",
        value=st.session_state["try"],
        key="try_input",
        on_change=lambda: setattr(
            st.session_state,
            "try",
            st.session_state["try_input"],
        ),
    )
    pcw = pcw_from_notes_string(st.session_state["try"])
    st_audio(pcw)


def render_image() -> None:
    _, col2, _ = st.columns((1, 2, 1))
    with col2:
        st.image("https://i.imgur.com/59r5RGa.jpeg")


def render_nose_whistle_cover() -> None:
    _, col2, _ = st.columns((1, 2, 1))
    with col2:
        st.video("https://youtu.be/oDHs8Z-F--o")


def display_example(
    tm: str,
    en: str,
    name: str,
    words: list[Word],
    displayed_sentences_key: str,
) -> None:
    """Displays a particular example for a

    Parameters
    ----------
    tm : str
        The Toki Musi sentence.
    en : str
        The English sentence.
    name : str
        Name of the word this example is loaded for, used for the key ok to leave empty unless
        loading the same example multiple times on the same page.
    """
    words_in_sentence = get_words_from_sentence(
        tm, words, st.session_state["prefer_composites"]
    )
    st_audio(get_sentence_wave(words_in_sentence, speed=st.session_state["speed"]))
    id_tm = f"{name}_{tm}"
    if id_tm not in st.session_state[displayed_sentences_key]:
        if st.button(
            "Show text version",
            key=id_tm,
            on_click=lambda s=id_tm: st.session_state[displayed_sentences_key].add(s),  # type: ignore
        ):
            pass
    else:
        st.write(tm)  # type: ignore

    id_en = f"{name}_{en}"
    if id_en not in st.session_state[displayed_sentences_key]:
        if st.button(
            "Show translation",
            key=id_en,
            on_click=lambda s=id_en: st.session_state[displayed_sentences_key].add(s),  # type: ignore
        ):
            pass
    else:
        st.write(en)  # type: ignore
    st.divider()


def render_settings(
    speed: bool = True,
    prefer_composites: bool = True,
    allow_keychanges: bool = True,
    f_min: bool = True,
    f_max: bool = True,
    octave: bool = True,
) -> None:
    if "speed" not in st.session_state or not speed:
        st.session_state["speed"] = 10
    if "prefer_composites" not in st.session_state or not prefer_composites:
        st.session_state["prefer_composites"] = False
    if "allow_keychanges" not in st.session_state or not allow_keychanges:
        st.session_state["allow_keychanges"] = False
    if "f_min" not in st.session_state or not f_min:
        st.session_state["f_min"] = 300
    if "f_max" not in st.session_state or not f_max:
        st.session_state["f_max"] = 4000
    if "octave" not in st.session_state or not octave:
        st.session_state["octave"] = -1

    with st.expander("Settings"):
        if speed:
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
        if prefer_composites:
            st.subheader("Prefer composites")
            st.markdown(  # type: ignore
                'If two words belong together, you can turn their melodies into one melody. Check the <a href="./guide" style="color:#FF0000;">guide</a> for more information on how that works. If you select this option, established combinations of words will be played as composite words by the synthesiser.',
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
        if allow_keychanges:
            st.subheader("Allow key changes")
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
        if f_min:
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
        if f_max:
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
        if octave:
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
