# default sample rate for recordings
SAMPLE_RATE = 44100

# default nr of samples for a fade in/out of a synthesised bit of sound
FADE_DURATION = 1000

# the amount of samples in a parselmouth pitch output
SAMPLE_RATE_PARSELMOUTH = 400

# 0 == A; 3 == C
ROOT: int = 3

# the frequency of the root set above
FREQ_ROOT: float = 440 * 2 ** (ROOT / 12)

# the max variance we expect for a segment of a note that's elongated, but doesn't contain any other augmentations
VAR_THRESHOLD_FOR_LONG_NOTE = 0.2
