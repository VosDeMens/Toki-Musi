import numpy as np
import streamlit as st
import re

from src.constants import SAMPLE_RATE
from src.my_types import floatlist
from src.util import audio_to_html
from src.wave_generation import add_pause, marginify_wave, pcw_from_notes_string
from src.whistle_analysis import pitch_string_by


def st_audio(wave: floatlist, sample_rate: int = SAMPLE_RATE):
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
                render_expander_with_sub_expanders(expander_header, content)
            expander_header = line
            content = []
        else:
            content.append(line)

    if expander_header:
        render_expander_with_sub_expanders(expander_header, content)


def render_expander_with_sub_expanders(big_header: str, content: list[str]) -> None:
    with st.expander(big_header):
        for line in content:
            if line == "\\$\\$":
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
            else:
                enriched = replace_dollar_with_audio_html(line)
                st.markdown(enriched, unsafe_allow_html=True)


def replace_dollar_with_audio_html(text: str):
    def replacement(match: re.Match[str]) -> str:
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
        full_wave = np.concatenate(with_pauses)
        html = audio_to_html(full_wave)
        return f"`{match_string}` {html}"

    pattern = r"`([^`]+)`\\\$"
    return re.sub(pattern, replacement, text)
