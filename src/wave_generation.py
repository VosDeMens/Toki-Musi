import numpy as np

from src.augmentation import Augmentation
from src.constants import FADE_DURATION
from src.my_types import floatlist
from src.util import pitch_to_freq

# import sounddevice as sd  # type: ignore

# 1 to 10
SAMPLE_RATE: int = 44100
DURATION: int = 441 * 20

NOTES_PER_SEC_BASE: int = SAMPLE_RATE // DURATION

# 0 == A
ROOT: int = 3


def generate_phase_continuous_wave(frequency_segments: list[floatlist]) -> floatlist:
    """Generates a sound wave from the frequency values over time, taking into account phase.

    Parameters
    ----------
    frequency_segments : list[floatlist]
        For every note, this should contain a `np.array` of frequency values over time,
        one value per audio sample to be generated.

    Returns
    -------
    floatlist
        A well-behaved sound wave, matching the provided frequencies at every point in time.
    """
    if len(frequency_segments) == 0:
        return np.array([])
    frequencies = np.concatenate(frequency_segments)
    amplitude_segments = [
        get_amplitutude_segment(len(f_s)) for f_s in frequency_segments
    ]
    amplitudes = np.concatenate(amplitude_segments)
    dt = 1 / SAMPLE_RATE
    phases = np.cumsum(2 * np.pi * frequencies * dt)
    wave = 0.5 * np.sin(phases) * amplitudes
    return wave


def get_amplitutude_segment(
    length: int, fade_duration: int = FADE_DURATION
) -> floatlist:
    """Generates amplitude values over time for a single note, with a fade in and fade out.

    Parameters
    ----------
    length : int
        Duration of the audio to be generated, in nr of samples
    fade_duration : int, optional
        Duration of the fade, by default FADE_DURATION := 1000

    Returns
    -------
    floatlist
        Amplitude values over time
    """
    actual_fade_duration = min(fade_duration, length // 2)
    amplitutude_segment: floatlist = np.array(
        [
            *get_attack(actual_fade_duration),
            *np.linspace(1, 1, length - 2 * actual_fade_duration),
            *get_release(actual_fade_duration),
        ]
    )
    return amplitutude_segment


def fade_in_fade_out(signal: floatlist) -> floatlist:
    """Applies fade in and fade out to a wave.

    Parameters
    ----------
    signal : floatlist
        Original wave.

    Returns
    -------
    floatlist
        Wave with fades.
    """
    assert len(signal.shape) == 1, "signal has to be 1D"
    amplitutude_segment = get_amplitutude_segment(len(signal))
    return signal * amplitutude_segment


def get_attack(attack_duration: int = FADE_DURATION) -> floatlist:
    """Creates a smooth fade in envelope, based on cosine.

    Parameters
    ----------
    attack_duration : int, optional
        Duration in samples, by default FADE_DURATION := 1000

    Returns
    -------
    floatlist
        Amplitude values
    """
    cos_input = np.linspace(-np.pi, 0, attack_duration)
    cos_output = np.cos(cos_input)
    moved_up = cos_output + 1
    scaled_down = moved_up / 2
    return scaled_down


def get_release(release_furation: int = FADE_DURATION) -> floatlist:
    """Creates a smooth fade out envelope, based on cosine.

    Parameters
    ----------
    attack_duration : int, optional
        Duration in samples, by default FADE_DURATION := 1000

    Returns
    -------
    floatlist
        Amplitude values
    """
    cos_input = np.linspace(0, np.pi, release_furation)
    cos_output = np.cos(cos_input)
    moved_up = cos_output + 1
    scaled_down = moved_up / 2
    return scaled_down


def add_pause(
    wave_segment: floatlist, pause: float = 1, speed: float = 10
) -> floatlist:
    """Adds silence at the end of a sound wave.

    Parameters
    ----------
    wave_segment : floatlist
        Sound wave to extend with silence.
    pause : float, optional
        Length of the pause, where `1` corresponds to the length of a regular note, by default 1
    speed : int, optional
        The speed of the generated audio, which can be altered by the user, by default 10

    Returns
    -------
    floatlist
        The input, extended with silence.
    """
    return np.concatenate(
        [wave_segment, np.linspace(0, 0, int(DURATION * pause * 10 / speed))]
    )


def freq_timeline_from_str(
    s: str, speed: float = 10, offset: float = 0
) -> list[floatlist]:
    """Converts a notes string of a word into a frequency timeline.

    Parameters
    ----------
    s : str
        Notes string to convert.
    speed : int, optional
        Speed of the eventual sound, which can be altered by the user, by default 10
    offset : float, optional
        Semitones to transpose by, where `0` corresponds to C, by default 0

    Returns
    -------
    list[floatlist]
        A `list` of frequency values per note.

    Raises
    ------
    ValueError
        If the input string contains characters it shouldn't contain, we raise an exception.
        We don't catch this anywhere bc we assume proper inputs in production,
        and this exception is just for debugging purposes.
    """
    # Some words don't have notes, but indicate a key change. We return an empty list for these words.
    if s == "+" or s == "-":
        return []

    freq_timeline_segments: list[floatlist] = []
    i = 0
    while i < len(s):
        # Colons are just delimiters.
        if s[i] == ":":
            i += 1
            continue

        # If we encounter symbols representing augmentations, we alter the note we just added accordingly.
        if s[i] == Augmentation.LONG.value:
            freq_timeline_segments[-1] = apply_lengthen(freq_timeline_segments[-1], 1)  # type: ignore
            i += 1
            continue
        if s[i] == Augmentation.TRILL_UP.value:
            freq_timeline_segments[-1] = apply_trill(freq_timeline_segments[-1], 2)  # type: ignore
            i += 1
            continue
        if s[i] == Augmentation.TRILL_DOWN.value:
            freq_timeline_segments[-1] = apply_trill(freq_timeline_segments[-1], -2)  # type: ignore
            i += 1
            continue
        # This one is slightly more complicated bc it can indicate a slide between notes
        if (
            symbol := s[i]
        ) == Augmentation.SLIDE_UP.value or symbol == Augmentation.SLIDE_DOWN.value:
            start: float = freq_timeline_segments[-1][-1]  # type: ignore
            i += 1

            if i == len(s):
                if symbol == Augmentation.SLIDE_UP.value:
                    dest: float = start * 2 ** (7 / 12)
                else:
                    dest = start * 2 ** (-7 / 12)
            else:
                dest_str = ""
                while i < len(s) and s[i] in "0123456789-":
                    dest_str += s[i]
                    i += 1
                dest: float = pitch_to_freq(int(dest_str))

            freq_timeline_segments[-1] = np.concatenate(
                [
                    freq_timeline_segments[-1],
                    generate_frequency_timeline([start, dest], [1], speed),  # type: ignore
                ]
            )  # type: ignore
            continue
        # Indicating a rest between notes
        if s[i] == "r":
            freq = -1
            i += 1

        # Otherwise we only expect to see numbers
        else:
            c = ""
            while i < len(s) and (s[i] in "0123456789" or c == "" and s[i] == "-"):
                c += s[i]
                i += 1
            if len(c):
                n = int(c) + offset
                freq = pitch_to_freq(n)
            else:
                raise ValueError(f"what?? {s = }")

        # We add the segment for the number we found without augmentations, and change it later if necessary.
        vanilla_segment: floatlist = generate_frequency_timeline(
            [freq, freq], [1], speed
        )
        freq_timeline_segments.append(vanilla_segment)

    return freq_timeline_segments


def pcw_from_string(s: str, speed: float = 10, offset: float = 0) -> floatlist:
    """Generates a sound wave for a notes string.

    Parameters
    ----------
    s : str
        Notes string to convert.
    speed : int, optional
        Speed of the sound, which can be altered by the user, by default 10
    offset : float, optional
        Semitones to transpose by, where `0` corresponds to C, by default 0

    Returns
    -------
    floatlist
        A well-behaved sound wave, matching the provided frequencies at every point in time.
    """
    freq_timeline: list[floatlist] = freq_timeline_from_str(s, speed, offset)
    return generate_phase_continuous_wave(freq_timeline)


def generate_frequency_timeline(
    frequencies: list[float],
    duration_scalars: list[float] | None = None,
    speed: float = 10,
) -> floatlist:
    """Creates a "continuous" timeline of frequencies we want to synthesise sound from.

    -1 represents a silence.

    Parameters
    ----------
    frequencies : list[float]
        Waypoints for the frequency timeline.
    duration_scalars : list[float] | None, optional
        Scalars indicating the time between the waypoints, where `1` will result
        in the regular duration, by default None
    speed : int, optional
        The speed of the generated audio, which can be altered by the user, by default 10

    Returns
    -------
    floatlist
        A "continuous" timeline of frequencies we want to synthesise sound from.
    """
    if duration_scalars is None:
        duration_scalars = [1 for _ in range(len(frequencies) - 1)]
    freq_segments: list[floatlist] = []
    for i in range(len(frequencies) - 1):
        start_freq = frequencies[i]
        end_freq = frequencies[i + 1]
        duration_scalar = duration_scalars[i]
        if start_freq == -1 or end_freq == -1:
            start_freq = -1
            end_freq = -1
        freq_segment = np.linspace(
            start_freq, end_freq, int(duration_scalar * DURATION * 10 / speed)
        )
        freq_segments.append(freq_segment)
    return np.concatenate(freq_segments)


def apply_lengthen(
    frequency_segment: floatlist, duration_scalar: int = 2, speed: float = 10
) -> floatlist:
    """Extends a frequency timeline into a timeline with a tail.

    Parameters
    ----------
    frequency_segment : floatlist
        The frequency timeline to extend.
    duration_scalars : list[float] | None, optional
        Scalars indicating the time between the waypoints, where `1` will result
        in the regular duration, by default None
    speed : int, optional
        The speed of the generated audio, which can be altered by the user, by default 10

    Returns
    -------
    floatlist
        Augmented frequency timeline
    """
    tail = [
        frequency_segment[-1]
        for _ in range(int(duration_scalar * DURATION * 10 / speed))
    ]
    return np.concatenate([frequency_segment, tail])


def apply_trill(
    frequency_segment: floatlist, reach: int = 2, speed: float = 10
) -> floatlist:
    """Turns a frequency timeline into a timeline with a trill in the middle.

    Parameters
    ----------
    frequency_segment : floatlist
        The frequency timeline to augment.
    reach : int, optional
        The intensity of the trill (in semitones), defaults to 2
    speed : int, optional
        The speed of the generated audio, which can be altered by the user, by default 10

    Returns
    -------
    floatlist
        Augmented frequency timeline
    """
    last_frequency = frequency_segment[-1]
    if last_frequency == -1:
        raise ValueError("can't trill silence")
    trilled_segments: list[floatlist] = [frequency_segment]
    goal_frequency: float = last_frequency * 2 ** (reach / 12)
    trilled_segments.append(
        generate_frequency_timeline(
            [
                last_frequency,
                last_frequency,
                last_frequency,
                last_frequency,
                last_frequency,
                goal_frequency,
                goal_frequency,
                goal_frequency,
                last_frequency,
                last_frequency,
                last_frequency,
                last_frequency,
                last_frequency,
            ],
            [1 / 9 for _ in range(13)],
            speed,
        )
    )
    trilled_segments[0] = trilled_segments[0][: -len(trilled_segments[1])]
    return np.concatenate(trilled_segments)


def marginify_wave(raw: floatlist) -> floatlist:
    """Adds silence around the provided wave.

    Parameters
    ----------
    raw : floatlist
        The wave to add silence around.

    Returns
    -------
    floatlist
        Wave with silence.
    """
    margin = np.linspace(0, 0, SAMPLE_RATE // 4)
    return np.concatenate([margin, raw, margin])
