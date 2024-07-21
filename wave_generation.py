from typing import Any

import numpy as np
import numpy.typing as npt

# import sounddevice as sd  # type: ignore

floatlist = npt.NDArray[np.floating[Any]]

# 1 to 10
speed = 9
SAMPLE_RATE = 44100
DURATION: int = 441 * 20


def generate_phase_continuous_wave(frequency_segments: list[floatlist]) -> floatlist:
    frequencies = np.concatenate(frequency_segments)
    amplitude_segments = [
        get_amplitutude_segment(len(f_s)) for f_s in frequency_segments
    ]
    amplitudes = np.concatenate(amplitude_segments)
    dt = 1 / SAMPLE_RATE
    phases = np.cumsum(2 * np.pi * frequencies * dt)
    wave = 0.5 * np.sin(phases) * amplitudes
    return wave


def get_amplitutude_segment(length: int, fade_duration: int = 200) -> list[float]:
    amplitutude_segment = [
        *np.linspace(0, 1, fade_duration),
        *np.linspace(1, 1, length - 2 * fade_duration),
        *np.linspace(1, 0, fade_duration),
    ]
    return amplitutude_segment


# def fade_in(wave: floatlist, duration: float) -> floatlist:
#     fade_length = int(duration * SAMPLE_RATE)
#     fade = np.linspace(0, 1, fade_length)
#     wave[:fade_length] *= fade
#     return wave


# def fade_out(wave: floatlist, duration: float) -> floatlist:
#     fade_length = int(duration * SAMPLE_RATE)
#     fade = np.linspace(1, 0, fade_length)
#     wave[-fade_length:] *= fade
#     return wave


# def concatenate_waves(
#     waves: list[floatlist], fade_duration: float = 0.4, sample_rate: int = 44100
# ) -> floatlist:
#     faded_waves: list[floatlist] = []
#     for wave in waves:
#         wave = fade_in(wave, fade_duration)
#         wave = fade_out(wave, fade_duration)
#         faded_waves.append(wave)
#     return np.concatenate(faded_waves)


# def get_melody(notes: list[int]) -> floatlist:
#     freqs = map(find_frequency, notes)
#     waves = map(generate_sine_wave, freqs)
#     total = concatenate_waves(list(waves))
#     return total


# def play_str(s: str) -> None:
#     ftl = freq_timeline_from_str(s)
#     pcw = generate_phase_continuous_wave(ftl)
#     sd.play(pcw)  # type: ignore


def find_frequency(note: float) -> float:
    return 440 * 2 ** ((note + 4) / 12)


# def set_speed(s: float) -> None:
#     global speed
#     speed = s


def freq_timeline_from_str(s: str) -> list[floatlist]:
    freq_timeline_segments: list[floatlist] = []
    i = 0
    while i < len(s):
        c = ""
        while i < len(s) and s[i] in "0123456789-":
            c += s[i]
            i += 1
        if c:
            n = int(c)
            freq = find_frequency(n)
            vanilla_segment: floatlist = generate_frequency_journey([freq, freq], [1])

            if i < len(s) and s[i] == "_":
                freq_timeline_segments.append(apply_lengthen(vanilla_segment))

            elif i < len(s) and s[i] == "*":
                freq_timeline_segments.append(apply_trill(vanilla_segment, 2))

            elif i < len(s) and s[i] == "~":
                freq_timeline_segments.append(apply_trill(vanilla_segment, -2))

            else:
                freq_timeline_segments.append(vanilla_segment)

        elif s[i] == "v":
            last_segment = freq_timeline_segments[-1]
            del freq_timeline_segments[-1]
            freq_timeline_segments.append(apply_post_shwoop(last_segment, -7))

        i += 1

    return freq_timeline_segments


def generate_frequency_journey(
    frequencies: list[float], duration_scalars: list[float] | None = None
) -> floatlist:
    if duration_scalars is None:
        duration_scalars = [1 for _ in range(len(frequencies) - 1)]
    freq_segments: list[floatlist] = []
    for i in range(len(frequencies) - 1):
        start_freq = frequencies[i]
        end_freq = frequencies[i + 1]
        duration_scalar = duration_scalars[i]
        freq_segment = np.linspace(
            start_freq, end_freq, int(duration_scalar * DURATION)
        )
        freq_segments.append(freq_segment)
    return np.concatenate(freq_segments)


def apply_lengthen(frequency_segment: floatlist, factor: int = 3) -> floatlist:
    return np.array([f for f in frequency_segment for _ in range(factor)])


def apply_trill(frequency_segment: floatlist, reach: int = 2) -> floatlist:
    trilled_segments: list[floatlist] = [frequency_segment]
    last_frequency = frequency_segment[-1]
    goal_frequency: float = last_frequency * 2 ** (reach / 12)
    trilled_segments.append(
        generate_frequency_journey(
            [
                last_frequency,
                last_frequency,
                last_frequency,
                goal_frequency,
                goal_frequency,
                goal_frequency,
                last_frequency,
                last_frequency,
                last_frequency,
            ],
            [1 / 9 for _ in range(9)],
        )
    )
    trilled_segments[0] = trilled_segments[0][: -len(trilled_segments[1])]
    return np.concatenate(trilled_segments)


def apply_post_shwoop(frequency_segment: floatlist, reach: int = 7) -> floatlist:
    shwooped_segments: list[floatlist] = [frequency_segment]
    last_frequency = frequency_segment[-1]
    shwooped_segments.append(
        generate_frequency_journey([last_frequency, last_frequency * 2 ** (reach / 12)])
    )
    return np.concatenate(shwooped_segments)
