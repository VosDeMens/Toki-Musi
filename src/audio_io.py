import IPython.display as ipd
import sounddevice as sd  # type: ignore
from typing import cast

from src.my_types import floatlist
from src.constants import SAMPLE_RATE
from src.wave_generation import fade_in_fade_out


def play(signal: floatlist, sample_rate: int = SAMPLE_RATE) -> ipd.Audio:
    """Creates a playable object in a Jupyter Notebook. (Not suitable for Streamlit.)

    Parameters
    ----------
    signal : floatlist
        The audio to play, represented as a wave.
    sample_rate : int, optional
        The sample rate, by default SAMPLE_RATE := 44100

    Returns
    -------
    ipd.Audio
        The playable object.
    """
    return ipd.Audio(signal, rate=sample_rate)


def record(nr_of_seconds: int = 8) -> floatlist:
    """Records audio, fit for Jupyter Notebook, not for Streamlit.

    Parameters
    ----------
    nr_of_seconds : int, optional
        Duration to record for, by default 8

    Returns
    -------
    floatlist
        Audio, as a wave.
    """
    recording = sd.rec(  # type: ignore
        (nr_of_seconds * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float64",
    )
    print("Recording...")
    sd.wait()
    print("Recording complete.")
    recording = cast(floatlist, recording)
    recording = recording.reshape((recording.shape[0]))
    recording = fade_in_fade_out(recording)
    return recording
