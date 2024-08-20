import numpy as np

from my_types import floatlist

# import sounddevice as sd  # type: ignore

# 1 to 10
SAMPLE_RATE = 44100
DURATION: int = 441 * 20


def generate_phase_continuous_wave(frequency_segments: list[floatlist]) -> floatlist:
    frequencies = np.concatenate(frequency_segments)
    amplitude_segments = [
        get_amplitutude_segment(len(f_s), f_s[0]) for f_s in frequency_segments
    ]
    amplitudes = np.concatenate(amplitude_segments)
    dt = 1 / SAMPLE_RATE
    phases = np.cumsum(2 * np.pi * frequencies * dt)
    wave = 0.5 * np.sin(phases) * amplitudes
    return wave


def get_amplitutude_segment(
    length: int, v: float, fade_duration: int = 300
) -> list[float]:
    if v == -1:
        return [*np.linspace(0, 0, length)]
    amplitutude_segment = [
        *np.linspace(0, 1, fade_duration),
        *np.linspace(1, 1, length - 2 * fade_duration),
        *np.linspace(1, 0, fade_duration),
    ]
    return amplitutude_segment


def add_pause(wave_segment: floatlist, pause: float = 1, speed: int = 10) -> floatlist:
    return np.concatenate(
        [wave_segment, np.linspace(0, 0, int(DURATION * pause * 10 / speed))]
    )


def find_frequency(note: float) -> float:
    return 440 * 2 ** ((note + 4) / 12)


def freq_timeline_from_str(s: str, speed: int = 10) -> list[floatlist]:
    freq_timeline_segments: list[floatlist] = []
    i = 0
    while i < len(s):
        if s[i] == ":":
            i += 1
            continue
        if s[i] == "_":
            freq_timeline_segments[-1] = apply_lengthen(freq_timeline_segments[-1], 1)  # type: ignore
            i += 1
            continue
        if s[i] == "^":
            freq_timeline_segments[-1] = apply_trill(freq_timeline_segments[-1], 2)  # type: ignore
            i += 1
            continue
        if s[i] == "~":
            freq_timeline_segments[-1] = apply_trill(freq_timeline_segments[-1], -2)  # type: ignore
            i += 1
            continue
        if s[i] == "/":
            start: float = freq_timeline_segments[-1][-1]  # type: ignore
            dest_str = ""
            i += 1
            while i < len(s) and s[i] in "0123456789-":
                dest_str += s[i]
                i += 1
            dest: float = find_frequency(int(dest_str))
            freq_timeline_segments[-1] = np.concatenate(
                [
                    freq_timeline_segments[-1],
                    generate_frequency_journey([start, dest], [1], speed),  # type: ignore
                ]
            )  # type: ignore
            continue
        if s[i] == "r":
            freq = -1
            i += 1
        else:
            c = ""
            while i < len(s) and s[i] in "0123456789-":
                c += s[i]
                i += 1
            if len(c):
                n = int(c)
                freq = find_frequency(n)
            else:
                raise ValueError("what")
        vanilla_segment: floatlist = generate_frequency_journey(
            [freq, freq], [1], speed
        )
        freq_timeline_segments.append(vanilla_segment)

    return freq_timeline_segments


def generate_frequency_journey(
    frequencies: list[float],
    duration_scalars: list[float] | None = None,
    speed: int = 10,
) -> floatlist:
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
    frequency_segment: floatlist, duration_scalar: int = 2, speed: int = 10
) -> floatlist:
    tail = [
        frequency_segment[-1]
        for _ in range(int(duration_scalar * DURATION * 10 / speed))
    ]
    return np.concatenate([frequency_segment, tail])


def apply_trill(
    frequency_segment: floatlist, reach: int = 2, speed: int = 10
) -> floatlist:
    last_frequency = frequency_segment[-1]
    if last_frequency == -1:
        raise ValueError("can't trill silence")
    trilled_segments: list[floatlist] = [frequency_segment]
    goal_frequency: float = last_frequency * 2 ** (reach / 12)
    trilled_segments.append(
        generate_frequency_journey(
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
    margin = np.linspace(0, 0, SAMPLE_RATE // 4)
    return np.concatenate([margin, raw, margin])


# def apply_post_shwoop(frequency_segment: floatlist, reach: int = 7) -> floatlist:
#     shwooped_segments: list[floatlist] = [frequency_segment]
#     last_frequency = frequency_segment[-1]
#     shwooped_segments.append(
#         generate_frequency_journey([last_frequency, last_frequency * 2 ** (reach / 12)])
#     )
#     return np.concatenate(shwooped_segments)
