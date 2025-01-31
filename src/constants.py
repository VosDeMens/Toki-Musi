# default sample rate for recordings
SAMPLE_RATE = 44100

# how many notes in a second by default (speed := 10)
NOTES_PER_SEC = 5

# default nr of samples for a fade in/out of a synthesised bit of sound
NOTE_FADE_DURATION_SEC = 0.025

# default nr of samples for a fade in/out of a recording / audio
AUDIO_FADE_DURATION_SEC = 0.25

# 0 == A; 3 == C
ROOT: int = 3

# the frequency of the root set above
FREQ_ROOT: float = 440 * 2 ** (ROOT / 12)

# the max variance we expect for a segment of a note that's elongated, but doesn't contain any other augmentations
VAR_THRESHOLD_FOR_LONG_NOTE = 0.2
