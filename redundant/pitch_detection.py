# from typing import Any
# import io
# import numpy as np
# from scipy.io import wavfile  # type: ignore
# from scipy import signal  # type: ignore

# from src.my_types import floatlist

# def stft_from_bytes(
#     audio_bytes: bytes,
#     stft_segs_per_sec: int = STFT_SEGS_PER_SEC,
#     stft_overlap_quotient: int = STFT_OVERLAP_QUOTIENT,
#     stft_padding_factor_or_some_shit: int = STFT_PADDING_FACTOR_OR_SOME_SHIT,
# ) -> tuple[Any, floatlist, floatlist]:
#     audio_buffer = io.BytesIO(audio_bytes)
#     sample_rate, audio_data = wavfile.read(audio_buffer)  # type: ignore

#     nperseg = int(sample_rate / stft_segs_per_sec)
#     noverlap = nperseg // stft_overlap_quotient
#     nfft = nperseg * stft_padding_factor_or_some_shit

#     return signal.stft(  # type: ignore
#         audio_data,
#         fs=sample_rate,
#         nperseg=nperseg,
#         noverlap=noverlap,
#         nfft=nfft,
#     )


# freqs_bins: (n_bins)
# mags: (n_bins)
# def detect_pitch(freqs_bins: floatlist, mags: floatlist, radius: int = 5) -> float:
#     # print(f"{mags = }")
#     i_peak = np.nanargmax(mags, axis=0)
#     if i_peak < radius:
#         print(f"peak not good: {i_peak},    {radius = }")
#         i_peak = radius
#     freqs_range = freqs_bins[i_peak - radius : i_peak + radius + 1]
#     mags_range = mags[i_peak - radius : i_peak + radius + 1]
#     geometric_mean = np.prod(np.power(freqs_range, mags_range)) ** (
#         1 / np.sum(mags_range)
#     )
#     return float(geometric_mean)
