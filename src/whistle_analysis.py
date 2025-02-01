from math import log
import re
import numpy as np
from itertools import pairwise, product
import parselmouth

from src.augmentation import Augmentation
from src.constants import (
    FREQ_ROOT,
    VAR_THRESHOLD_FOR_LONG_NOTE,
)
from src.my_types import floatlist, segbounds
from src.note import Note
from src.file_management import load_words_from_folder
from src.util import split_numeric_part
from src.wave_generation import marginify_wave
from src.word import (
    InvalidWordException,
    NumberWord,
    Word,
    is_number_notes_string,
    notes_string_to_number,
)
from src.words_functions import get_prevalence

WORDS = load_words_from_folder()


def analyse_recording_to_notes(
    recording: floatlist,
    sample_rate_recording: int,
    f_min: float = 300,
    f_max: float = 4000,
) -> tuple[list[Note], segbounds, list[bool], float, int]:
    """Extracts from a recording: the notes, when the notes occur, and the offset of the root from C.

    This analysis relies on the Parselmouth package. It uses `parselmouth.Sound` and `snd.to_pitch_ac`.
    This output is then processed further, to the format described below.

    Parameters
    ----------
    recording : floatlist
        A `np.array` representing a sound wave of a monophonic recording (whistle or otherwise).
    sample_rate_recording : int
        The sample rate of the recording.
    f_min : float
        The lowest frequency to detect in the recording.
    f_max : float
        The highest frequency to detect in the recording.

    Returns
    -------
    tuple[list[Note], segbounds, list[bool], float, int]
        A `tuple`, with the following information:
        - The notes in the recording, represented by a `list` of `Note` objects.
        - The bounds of these notes, represented by a `list` of `tuples`, each with two `int`s,
            representing the start and end of each note, in terms of indices of the samples
            of the output of the pitch analysis (approx 400 samples per second).
        - A list of flags indicating which notes are the first of a word.
        - The distance of the determined root of the recording from C in semitones.
            If the sentence is in D, this value will be 2.
        - The sample rate in the pitch analysis.
    """
    snd = parselmouth.Sound(recording, sampling_frequency=sample_rate_recording)  # type: ignore
    parselmouth_output = snd.to_pitch_ac(  # type: ignore
        pitch_floor=f_min,
        pitch_ceiling=f_max,
        silence_threshold=0.1,
    )
    freqs: floatlist = np.array(parselmouth_output.selected_array["frequency"])  # type: ignore
    segment_bounds_raw = find_segment_bounds_parselmouth(freqs)

    print(f"{segment_bounds_raw = }")

    segment_bounds = process_segments(segment_bounds_raw)

    print(f"{segment_bounds = }")

    float_pitches = freqs_to_float_pitches(freqs)

    regular_length = determine_regular_note_length(segment_bounds)
    _, long_note_threshold = determine_note_thresholds(segment_bounds)

    float_notes_and_augmentations: list[tuple[float, list[Augmentation]]] = [
        determine_float_note_and_augmentations_of_segment(
            float_pitches[lower_bound:upper_bound], regular_length, long_note_threshold
        )
        for lower_bound, upper_bound in segment_bounds
    ]

    print(f"{float_notes_and_augmentations = }")

    float_notes: list[float] = [
        float_note for float_note, _ in float_notes_and_augmentations
    ]
    augmentations: list[list[Augmentation]] = [
        augmentation_per_note
        for _, augmentation_per_note in float_notes_and_augmentations
    ]
    normalised_float_notes, offset = normalise_float_notes(float_notes)

    lengths = [upper_bound - lower_bound for lower_bound, upper_bound in segment_bounds]

    _, long_pause_threshold = determine_pause_thresholds(segment_bounds)
    pauses = determine_pause_lengths(segment_bounds)
    new_word_flags = [True] + [pause > long_pause_threshold for pause in pauses]

    for i in range(1, len(new_word_flags)):
        if new_word_flags[i]:
            unexpected_one_note_word = (
                i == len(new_word_flags) - 1 or new_word_flags[i + 1]
            ) and (normalised_float_notes[i] < -2.5 or normalised_float_notes[i] > 2.5)
            if unexpected_one_note_word:
                new_word_flags[i] = False

    notes: list[Note] = [
        Note(pitch, length, augmentation_list, new_word)
        for pitch, length, augmentation_list, new_word in zip(
            normalised_float_notes, lengths, augmentations, new_word_flags
        )
    ]

    return (
        notes,
        segment_bounds,
        new_word_flags,
        offset,
        sample_rate_recording * len(freqs) // (len(recording)),
    )


def find_segment_bounds_parselmouth(freqs: floatlist) -> segbounds:
    """Finds the beginnings and ends of notes in the output of Parselmouth.

    Parameters
    ----------
    freqs : floatlist
        A `np.array` of `float`s representing the dominant frequencies,
        or 0 for parts of the audio that are below the amplitude threshold value.

    Returns
    -------
    segbounds
        The bounds of the notes, represented by a `list` of `tuples`, each with two `int`s,
        representing the start and end of each note, in terms of indices of the samples
        of the output of the pitch analysis (approx 400 samples per second).
    """
    assert len(freqs) >= 1, "amps has to be non-empty"

    segment_bounds: segbounds = []

    active_lower_bound: int = -1
    for i in range(len(freqs)):
        if freqs[i] != 0 and active_lower_bound == -1:
            active_lower_bound = i
        elif freqs[i] == 0 and active_lower_bound != -1:
            segment_bounds.append((active_lower_bound, i))
            active_lower_bound = -1
    if active_lower_bound != -1:
        segment_bounds.append((active_lower_bound, len(freqs)))

    return segment_bounds


def determine_regular_note_length(segments: segbounds) -> float:
    """Determines what we should expect as the length of a regular note.

    Parameters
    ----------
    segments : segbounds
        The bounds of these notes, represented by a `list` of `tuples`, each with two `int`s,
        representing the start and end of each note, in terms of indices of the samples
        of the output of the pitch analysis (approx 400 samples per second).

    Returns
    -------
    float
        The regular note length
    """
    lengths = [upper_bound - lower_bound for lower_bound, upper_bound in segments]
    if len(lengths) == 0:
        return 0
    if len(lengths) == 1:
        return lengths[0]
    lengths_sorted = sorted(lengths)
    shortest_part = lengths_sorted[: len(lengths_sorted) * 2 // 3]
    regular_segment_length = int(np.median(shortest_part))
    return regular_segment_length


def determine_regular_pause_length(segment_bounds: segbounds) -> float:
    """Determines what we should expect as the length of a regular pause.

    Parameters
    ----------
    segments : segbounds
        The bounds of these notes, represented by a `list` of `tuples`, each with two `int`s,
        representing the start and end of each note, in terms of indices of the samples
        of the output of the pitch analysis (approx 400 samples per second).

    Returns
    -------
    float
        The regular pause length
    """
    lengths = determine_pause_lengths(segment_bounds)
    if len(lengths) == 0:
        return 0
    if len(lengths) == 1:
        return lengths[0]
    lengths_sorted = sorted(lengths)
    shortest_part = lengths_sorted[: len(lengths_sorted) * 2 // 3]
    regular_pause_length = int(np.median(shortest_part))
    return regular_pause_length


def process_segments(segment_bounds: segbounds) -> segbounds:
    """Merges segments that probably represent the same note, and removes probably faulty segments.

    If segments are really close together, probably some part of a note
    dipped below the amplitude threshold value, so we can merge them.
    If segments that haven't been merged in this way are really short, they're probably
    artefacts in the recording that we shouldn't consider intentional.

    Parameters
    ----------
    segment_bounds : segbounds
        The bounds of the notes, represented by a `list` of `tuples`, each with two `int`s,
        representing the start and end of each note, in terms of indices of the samples
        of the output of the pitch analysis (approx 400 samples per second).

    Returns
    -------
    segbounds
        The (hopefully) corrected bounds of the notes, in the same format.
    """
    short_pause_threshold, _ = determine_pause_thresholds(segment_bounds)
    segment_bounds_merged = merge_segment_bounds_with_distance(
        segment_bounds, short_pause_threshold
    )

    short_note_threshold, _ = determine_note_thresholds(segment_bounds_merged)
    segment_bounds_filtered = filter_segment_bounds_below_min_length(
        segment_bounds_merged, short_note_threshold
    )

    return segment_bounds_filtered


def determine_pause_thresholds(
    segment_bounds: segbounds, short_factor: float = 0.4, long_factor: float = 1.7
) -> tuple[float, float]:
    """Determines the thresholds for a regular silence between notes of the same word.

    This is done by finding the average length of a silence, and choosing thresholds proportionally.

    Parameters
    ----------
    segment_bounds : segbounds
        The bounds of the notes, represented by a `list` of `tuples`, each with two `int`s,
        representing the start and end of each note, in terms of indices of the samples
        of the output of the pitch analysis (approx 400 samples per second).
    short_factor : float, optional
        The proportion to the average pause length below which pauses
        are considered unintentional, by default 0.4
    long_factor : float, optional
        The proportion to the average pause length above which pauses
        are considered to be indicative of a new word, by default 1.5

    Returns
    -------
    tuple[float, float]
        The lower and upper bounds of a regular pause length, respectively.
    """
    regular_length = determine_regular_pause_length(segment_bounds)
    print(f"{regular_length = }")
    short_pause_threshold = regular_length * short_factor
    long_pause_threshold_guess = regular_length * long_factor
    all_lengths = determine_pause_lengths(segment_bounds)
    print(f"{all_lengths = }")
    relevant_lengths = [
        length
        for length in all_lengths
        if length >= regular_length and length < long_pause_threshold_guess
    ]
    print(f"{relevant_lengths = }")
    higher_lengths = [
        length for length in all_lengths if length >= long_pause_threshold_guess
    ]
    print(f"{higher_lengths = }")
    if higher_lengths:
        relevant_lengths.append(min(higher_lengths))
    sorted_relevant_lengths = list(sorted(relevant_lengths))
    print(f"{sorted_relevant_lengths = }")
    if len(sorted_relevant_lengths) == 0:
        return (0, 0)
    if len(sorted_relevant_lengths) == 1:
        return (sorted_relevant_lengths[0] - 1, sorted_relevant_lengths[0] + 1)
    if len(all_lengths) == 2 and all_lengths[1] < 2 * all_lengths[0]:
        return (all_lengths[0] - 1, all_lengths[1] + 1)
    index_of_last_short_pause = np.argmax(np.diff(sorted_relevant_lengths))
    if sorted_relevant_lengths[-1] < long_pause_threshold_guess:
        long_pause_threshold = long_pause_threshold_guess
    else:
        long_pause_threshold = (
            sorted_relevant_lengths[index_of_last_short_pause]
            + sorted_relevant_lengths[index_of_last_short_pause + 1]
        ) / 2
    return (short_pause_threshold, long_pause_threshold)


def determine_pause_lengths(segment_bounds: segbounds) -> list[float]:
    """Finds the lengths of pauses between the notes.

    Parameters
    ----------
    segment_bounds : segbounds
        The bounds of the notes, represented by a `list` of `tuples`, each with two `int`s,
        representing the start and end of each note, in terms of indices of the samples
        of the output of the pitch analysis (approx 400 samples per second).

    Returns
    -------
    list[float]
        The pauses between the notes (so the length of this `list` will be 1 less than input).
    """
    return [
        lower_bound2 - upper_bound1
        for (_, upper_bound1), (lower_bound2, _) in pairwise(segment_bounds)
    ]


def determine_note_thresholds(
    segment_bounds: segbounds, short_factor: float = 0.3, long_factor: float = 2
) -> tuple[float, float]:
    """Determines the thresholds for a regular note length.

    This is done by finding the average length of a note, and choosing thresholds proportionally.

    Parameters
    ----------
    segment_bounds : segbounds
        The bounds of the notes, represented by a `list` of `tuples`, each with two `int`s,
        representing the start and end of each note, in terms of indices of the samples
        of the output of the pitch analysis (approx 400 samples per second).
    short_factor : float, optional
        The proportion to the average note length below which notes
        are considered unintentional, by default 0.3
    long_factor : float, optional
        The proportion to the average note length above which notes
        are considered intentionally elongated, by default 2

    Returns
    -------
    tuple[float, float]
        The lower and upper bounds of a regular note length, respectively.
    """
    regular_length = determine_regular_note_length(segment_bounds)
    short_note_threshold = regular_length * short_factor
    long_note_threshold_max = regular_length * long_factor
    all_lengths = [u - l for l, u in segment_bounds]
    relevant_lengths = [
        length
        for length in all_lengths
        if length >= regular_length and length < long_note_threshold_max
    ]
    higher_lengths = [
        length for length in all_lengths if length >= long_note_threshold_max
    ]
    if higher_lengths:
        relevant_lengths.append(min(higher_lengths))
    sorted_relevant_lengths = list(sorted(relevant_lengths))
    if len(sorted_relevant_lengths) == 0:
        return (0, 0)
    if len(sorted_relevant_lengths) == 1:
        return (sorted_relevant_lengths[0] - 1, sorted_relevant_lengths[0] + 1)
    index_of_last_short_note = np.argmax(np.diff(sorted_relevant_lengths))
    if sorted_relevant_lengths[-1] < long_note_threshold_max:
        long_note_threshold = long_note_threshold_max
    else:
        long_note_threshold = (
            sorted_relevant_lengths[index_of_last_short_note]
            + sorted_relevant_lengths[index_of_last_short_note + 1]
        ) / 2

    return (short_note_threshold, long_note_threshold)


def merge_segment_bounds_with_distance(
    segment_bounds: segbounds, distance: float = 3
) -> segbounds:
    """Merges segment bounds of notes that are at most `distance` apart (inclusive).

    Parameters
    ----------
    segment_bounds : segbounds
        The bounds of the notes, represented by a `list` of `tuples`, each with two `int`s,
        representing the start and end of each note, in terms of indices of the samples
        of the output of the pitch analysis (approx 400 samples per second).
    distance : float, optional
        The distance up to and including which to merge for, by default 3

    Returns
    -------
    segbounds
        The merged segment bounds, in the same format as the input.
    """
    merged: segbounds = []
    i = 0
    while i < len(segment_bounds):
        j = i
        while (
            j < len(segment_bounds) - 1
            and segment_bounds[j + 1][0] - segment_bounds[j][1] <= distance
        ):
            j += 1
        merged.append((segment_bounds[i][0], segment_bounds[j][1]))
        i = j + 1
    return merged


def filter_segment_bounds_below_min_length(
    segment_bounds: segbounds, min_length: float = 2
) -> segbounds:
    """Removes segment bounds of notes that are strictly shorter than `min_lentgh`.

    Parameters
    ----------
    segment_bounds : segbounds
        The bounds of the notes, represented by a `list` of `tuples`, each with two `int`s,
        representing the start and end of each note, in terms of indices of the samples
        of the output of the pitch analysis (approx 400 samples per second).
    min_length : float, optional
        The note length below which to remove notes, by default 2

    Returns
    -------
    segbounds
        The merged segment bounds, in the same format as the input.
    """
    filtered: segbounds = [
        (lower_bound, upper_bound)
        for lower_bound, upper_bound in segment_bounds
        if upper_bound - lower_bound >= min_length
    ]
    return filtered


def freqs_to_float_pitches(freqs: floatlist, freq_root: float = FREQ_ROOT) -> floatlist:
    """Converts frequency values to pitch values, relative to the provided root frequency.

    Parameters
    ----------
    freqs : floatlist
        The frequencies to convert to pitches.
    freq_root : float, optional
        The frequency to consider to be the root, by default FREQ_ROOT (C)

    Returns
    -------
    floatlist
        Pitch values, `0` for `freq_root`, and for example `2` for a frequency
        a whole tone above `freq_root`
    """
    freqs_normalised_to_root: floatlist = freqs / freq_root
    pitches: list[float] = [
        log(freq, 2) * 12 if freq > 0 else np.nan for freq in freqs_normalised_to_root
    ]
    pitches_floatlist: floatlist = np.array(pitches)
    return pitches_floatlist


def determine_float_note_and_augmentations_of_segment(
    float_pitches: floatlist,
    regular_length: float,
    long_note_threshold: float,
    diff_threshold: float = 0.5,
    var_threshold: float = VAR_THRESHOLD_FOR_LONG_NOTE,
) -> tuple[float, list[Augmentation]]:
    """Determines the pitch value (not rounded) and augmentations for a single note.

    Parameters
    ----------
    float_pitches : floatlist
        The pitch values for every individual sample of a single note.
    regular_length : float
        The length we expect a note to be on average.
    long_note_threshold : float
        The threshold above which we consider a note intentionally enlongated.
    diff_threshold : float, optional
        The amount we expect a note to go up and back down for an intentional trill,
        expressed in semitones, by default 0.5
    var_threshold : float, optional
        The max variance we expect the first part for a note that's elongated,
        by default VAR_THRESHOLD_FOR_LONG_NOTE := 0.2

    Returns
    -------
    tuple[float, list[Augmentation]]
        - A single pith value for the (start of the) note.
        - A `list` of augmentations (see augmentation.py).
    """
    # If the segment is deliberatly augmented, it is expected to be longer than the threshold value
    if len(float_pitches) < long_note_threshold:
        start_pitch = float(np.nanmedian(float_pitches))
        return (start_pitch, [])

    start_pitch = float(np.nanmedian(float_pitches[:regular_length]))

    augmentations: list[Augmentation] = []

    # Assess for long notes
    length_to_check_for_long_note: int = min(
        len(float_pitches),
        round(3.3 * regular_length),  # 3.3 is picked from experimentation
    )
    var_of_start = np.var(float_pitches[:length_to_check_for_long_note])
    if var_of_start < var_threshold:
        augmentations.append(Augmentation.LONG)
        float_pitches_rest = float_pitches[length_to_check_for_long_note:]
    else:
        float_pitches_rest = float_pitches[regular_length:]

    # Assess for trills
    max_diff: float = 0
    max_diff_index: int = 0
    trill_mag: float = 0
    for i, pitch in enumerate(tuple(float_pitches_rest)):
        diff = pitch - start_pitch
        if (
            abs(max_diff) > diff_threshold  # if we've deviated significantly
            and abs(max_diff - diff) > diff_threshold  # and gone back significantly
            and abs(diff) < 2 * diff_threshold  # and we've come back far enough
            and i - max_diff_index
            > regular_length / 2  # and it's taken enough time not to be a random blip
        ):
            trill_mag = max(trill_mag, max_diff, key=abs)

        if abs(diff) > abs(max_diff):
            max_diff = diff
            max_diff_index = i

    if trill_mag > 0:
        augmentations.append(Augmentation.TRILL_UP)
    if trill_mag < 0:
        augmentations.append(Augmentation.TRILL_DOWN)

    # Assess for slides
    if float_pitches[-1] - start_pitch > 2:
        augmentations.append(Augmentation.SLIDE_UP)
    if float_pitches[-1] - start_pitch < -2:
        augmentations.append(Augmentation.SLIDE_DOWN)

    return (start_pitch, augmentations)


def normalise_float_notes(float_notes: list[float]) -> tuple[list[float], float]:
    """Determines the most likely intended root, and subtracts this from all pitch values.

    We don't assume perfect pitch, so a sentence could be in any key. We change what `0` means
    based on the provided recording. In doing this, we take into account that the first note could be off,
    so we see what other notes are close enough to it, to probably be intended `0`s, and we take the average.

    Parameters
    ----------
    float_notes : list[float]
        The raw pitch values, which could start anywhere, but should start approximately at `0`.

    Returns
    -------
    tuple[list[float], float]
        The transposed values, and the terms by which they were transposed (substractively).
    """
    assert len(float_notes) >= 1, "have to have at least one note"

    first_notes: list[float] = [float_notes[0]]
    for float_note in float_notes[1:]:
        difference: float = float(abs(float_note - np.mean(first_notes)))
        if difference < 0.75:
            first_notes.append(float_note)

    correction: float = float(np.mean(first_notes))

    float_notes_normalised = np.array(float_notes) - correction

    return (list(float_notes_normalised), correction)


def get_word_by_name(name: str) -> Word:
    """Literally just finds a word by its text representation.

    Parameters
    ----------
    name : str
        Text representation of the word we want to find.

    Returns
    -------
    Word
        The `Word` object.

    Raises
    ------
    InvalidWordException
        If the word does not exist.
    """
    matches = [word for word in WORDS if word.name == name]
    if not matches:
        raise InvalidWordException(f"No word with name {name}")
    return matches[0]


PI: Word = get_word_by_name("pi")
UNPI: Word = get_word_by_name("unpi")
LA: Word = get_word_by_name("la")


def get_stem_and_modifiers_of_notes_string(
    s: str,
) -> tuple[str, bool, bool, bool, bool, bool, bool, bool]:
    """Extracts the stem from the notes string of a word, and detects potential modifications.

    If we want to find the meaning of a notes string, we need to tell apart the stem from any
    modifications that might be added. This function does not check that the word stem corresponds
    to an existing word.

    Parameters
    ----------
    s : str
        Notes string, possibly modified.

    Returns
    -------
    tuple[str, bool, bool, bool, bool, bool, bool, bool]
        - The stem of the notes string, still in notes string format.
        - Flag indicating plural.
        - Flag indicating comparative.
        - Flag indicating superlative.
        - Flag indicating past_tense.
        - Flag indicating question.
        - Flag indicating finite_verb.
        - Flag indicating direct_object.

    Raises
    ------
    InvalidWordException
        If the string contains no other digits than 0, it's either representing
        a NumberWord, which doesn't have a stem, or an invalid string.

    Examples
    --------
    >>> get_stem_and_modifiers_of_notes_string("0:0:7_")
    ('0:7', True, False, False, False, False, True, False)
    """
    assert s[0] == "0", "Has to start with 0"

    if not any(c.isdigit() and int(c) > 0 for c in s):
        raise InvalidWordException
    (
        plural,
        comparative,
        superlative,
        past_tense,
        question,
        finite_verb,
        direct_object,
    ) = (False, False, False, False, False, False, False)

    # If the second digit is 0 (the first one is by default), we have a direct object, and we cut off a 0
    if s[2] == "0":
        assert s[3] == ":", "second zero can't be augmented"
        direct_object = True
        s = s[2:]

    # If the first 0 is elongated, we have a finite verb, and we remove the elongation
    elif s[1] == "0":
        finite_verb = True
        s = s[0] + s[2:]

    # Find the start of the suffix, and process the characters
    matches = list(re.finditer(r"\d", s))
    start_suffix = matches[-1].end()
    suffix = s[start_suffix:]
    for c in suffix:
        if c == "_":
            plural = True
        if c == "*":
            comparative = True
        if c == "^":
            superlative = True
        if c == "\\":
            past_tense = True
        if c == "/":
            question = True

    return (
        s[:start_suffix],
        plural,
        comparative,
        superlative,
        past_tense,
        question,
        finite_verb,
        direct_object,
    )


def find_exact_word_for_notes_string(s: str) -> Word | None:
    """Tries to find a `Word` object for a notes string, including modifications.

    Parameters
    ----------
    s : str
        Notes string.

    Returns
    -------
    Word | None
        A `Word` object corresponding to the notes string, or `None`, for invalid strings,
        or strings that have valid form, but simply don't exist in the vocabulary.
    """
    if is_number_notes_string(s):
        if s == "0_":
            return NumberWord(0)
        n = notes_string_to_number(s)
        return NumberWord(n)

    try:
        (
            root,
            plural,
            comparative,
            superlative,
            past_tense,
            question,
            finite_verb,
            direct_object,
        ) = get_stem_and_modifiers_of_notes_string(s)
    except InvalidWordException:
        return None

    for word in WORDS:
        if root == word.notes_string:
            if plural:
                word = word.pluralize()
            if comparative:
                word = word.comparativize()
            if superlative:
                word = word.superlativize()
            if past_tense:
                word = word.past_tensify()
            if question:
                word = word.questionify()
            if finite_verb:
                word = word.finite_verbify()
            if direct_object:
                word = word.direct_objectify()
            return word

    return None


def get_notes_from_string(s: str) -> tuple[list[int], list[str]]:
    """_summary_

    Parameters
    ----------
    s : str
        _description_

    Returns
    -------
    tuple[list[int], list[str]]
        _description_
    """
    note_strings: list[str] = [ns for ns in s.split(":") if len(ns) > 0]
    splats = [split_numeric_part(c) for c in note_strings]
    note_values = [splat[0] for splat in splats]
    note_augmentations = [splat[1] for splat in splats]
    return (note_values, note_augmentations)


def generate_neighbours(
    pitch_values: list[int], augmentations_per_note: list[str], max_dev: int = 2
) -> list[tuple[str, int]]:
    """Finds all sequences of notes that are within some deviation from the input.

    Changing a pitch value of some note by 1 is considered 1 deviation.
    Changing the presence of some augmentation for some note is considered 1 deviation.

    Parameters
    ----------
    pitch_values : list[int]
        The pitch values per note.
    augmentations_per_note : list[str]
        The augmentations per note.
    max_dev : int, optional
        The maximum amount of deviations, by default 2

    Returns
    -------
    list[tuple[str, int]]
        A `list` of all notes strings that are within the deviation range of the input,
        with their corresponding deviation.

    Examples
    --------
    >>> generate_neighbours([0, 5, 7], ["_", "", ""], 1)
    [('0_:5:7', 0), ('0_:4:7', 1), ('0_:5:6', 1), ('0_:5:7_', 1), ('0_:5:8', 1), ('0_:6:7', 1)]
    """
    note_deviations: list[list[int]] = generate_pitch_deviations(
        len(pitch_values), max_dev
    )
    aug_alternatives: list[tuple[list[str], int]] = (
        generate_scored_augmentation_alternatives(augmentations_per_note, max_dev)
    )
    combinations: list[tuple[list[int], list[str], int]] = [
        (note_d, aug_a, np.sum(np.square(note_d)) + aug_score)
        for note_d in note_deviations
        for aug_a, aug_score in aug_alternatives
        if np.sum(np.square(note_d)) + aug_score <= max_dev
    ]
    sorted_combinations = list(sorted(combinations, key=lambda c: c[2]))

    actual_note_strings_lists_scored: list[tuple[list[str], int]] = [
        ([str(v + d) + aug for v, d, aug in zip(pitch_values, devs, augs)], score)
        for devs, augs, score in sorted_combinations
    ]
    as_single_strings_scored: list[tuple[str, int]] = [
        (":".join(note_strings), score)
        for note_strings, score in actual_note_strings_lists_scored
    ]
    return as_single_strings_scored


def generate_pitch_deviations(n: int, max_dev: int = 2) -> list[list[int]]:
    """Generates the possible ways to deviate pitch values for `n` notes.

    The first note is never deviated from, so the first entry of the output
    of this function is always 0.

    Parameters
    ----------
    n : int
        The length of the note sequence to create deviations for.
    max_dev : int, optional
        The max number of deviations, by default 2

    Returns
    -------
    list[list[int]]
        A list of deviations (each of them either -1, 0, or 1).

    Examples
    --------
    >>> generate_pitch_deviations(3, 2)
    [[0, -1, -1], [0, -1, 0], [0, -1, 1], [0, 0, -1], [0, 0, 0], [0, 0, 1], [0, 1, -1], [0, 1, 0], [0, 1, 1]]
    """
    options = list([0] + list(devs) for devs in product([-1, 0, 1], repeat=n - 1))
    return [option for option in options if np.sum(np.square(option)) <= max_dev]


def generate_scored_augmentation_alternatives(
    augs: list[str], max_dev: int = 2
) -> list[tuple[list[str], int]]:
    """Generates the possible ways to deviate from the provided augmentations.

    Adding or removing one augmentation is considered one change.
    Does not change the first note.

    Parameters
    ----------
    augs : list[str]
        A string of augmentation characters per note.
    max_dev : int, optional
        The max number of changes to make to the augmentations, by default 2

    Returns
    -------
    list[tuple[list[str], int]]
        A `list` of augmentation values per note, that are within the provided deviation range,
        with a number indicating the amount of deviations for that `list`.

    Examples
    -------
    >>> generate_scored_augmentation_alternatives(["_", "", ""], 2)
    [(['_', '', ''], 0), (['_', '', '_'], 1), (['_', '_', ''], 1), (['_', '_', '_'], 2)]
    """
    result: list[tuple[list[str], int]] = [(augs[:1], 0)]
    for aug in augs[1:]:
        new_result: list[tuple[list[str], int]] = []
        for current, dev_score in result:
            if dev_score >= max_dev:
                continue
            new_result.append((current + [aug], dev_score))
            if "_" in aug:
                new_result.append((current + [aug.replace("_", "")], dev_score + 1))
            else:
                new_result.append((current + ["_" + aug], dev_score + 1))
        result = new_result
    return result


def pitch_string_by(notes_string: str, n: int) -> str:
    """Increases all pitch values in `notes_string` by `n`, keeping augmentations identical.

    Parameters
    ----------
    notes_string : str
        Original notes string.
    n : int
        Nr of semitones to pitch by.

    Returns
    -------
    str
        Pitched notes string.
    """
    note_values, note_augmentations = get_notes_from_string(notes_string)
    pitched_string = ":".join(
        str(v + n) + aug for v, aug in zip(note_values, note_augmentations)
    )
    return pitched_string


def replace_la_with_unpi_if_appropriate(words: list[Word]) -> list[Word]:
    """If a `pi` is followed by a `la`, the `la` is changed to `unpi`.

    `unpi` and `la` are both represented by a key change down, and whether it should be
    interpreted as one or the other depends on whether it was preceded by a `pi` we could pair
    it with.

    Parameters
    ----------
    words : list[Word]
        A `list` of `Word` objects, possibly containing `la`s that should be changed to `unpi`s.

    Returns
    -------
    list[Word]
        A `list` where `la`s could be replaced by `unpi`s, if appropriate.
    """
    words_copy = words.copy()
    pi_count = 0
    for i in range(len(words)):
        word = words[i]
        if word.name == "pi":
            pi_count += 1
        if word.name == "la" and pi_count > 0:
            words_copy[i] = UNPI
            pi_count -= 1
    return words_copy


def find_closest_words_for_notes_string(
    notes_string: str, max_dev: int = 2
) -> tuple[list[Word], int] | None:
    """Finds the best match(es) in Toki Musi for a provided `notes_string`.

    Sometimes a notes string has a perfect match in the language, and otherwise we'll look
    for the closest matches.

    Parameters
    ----------
    notes_string : str
        Notes string to match for.
    max_dev : int, optional
        Max amount of changes we allow when searching for a match, by default 2

    Returns
    -------
    tuple[list[Word], int] | None
        The best match, possibly preceeded by a word indicating key change,
        and the amount by which this match deviates from the input,
        or `None`, if no matches are found.
    """
    if notes_string[0] == "2":
        pitched_string = pitch_string_by(notes_string, -2)
        result = find_closest_words_for_notes_string(pitched_string, max_dev)
        if result is not None:
            result_words, result_offset = result
            return ([PI] + result_words, -2 + result_offset)

    if notes_string[:2] == "-2":
        pitched_string = pitch_string_by(notes_string, 2)
        result = find_closest_words_for_notes_string(pitched_string, max_dev)
        if result is not None:
            result_words, result_offset = result
            return ([LA] + result_words, 2 + result_offset)

    if not (
        notes_string[0] == "0" or notes_string[0] == "1" or notes_string[:2] == "-1"
    ):
        return None

    if notes_string[0] == "1":
        notes_string = "0" + notes_string[1:]

    if notes_string[:2] == "-1":
        notes_string = "0" + notes_string[2:]

    exact = find_exact_word_for_notes_string(notes_string)
    if exact is not None:
        return ([exact], 0)

    note_values, note_augmentations = get_notes_from_string(notes_string)

    nr_of_notes = len(note_values)
    if nr_of_notes > 8:
        return None

    neighbours = generate_neighbours(note_values, note_augmentations, max_dev)

    candidates: list[Word] = []
    min_score: int | None = None
    for neighbour, score in neighbours:
        if min_score is not None and score > min_score:
            break

        candidate = find_exact_word_for_notes_string(neighbour)
        if candidate is not None:
            candidates.append(candidate)
            min_score = score

    if len(candidates) == 0:
        return None

    best_candidate = max(candidates, key=get_prevalence)

    return ([best_candidate], 0)


def determine_deviances_from_target(
    notes_from_recording: list[Note], target_notes_string: str
) -> list[tuple[float, list[str], list[str]]] | None:
    """Determines how far off the notes from a recording are from the target notes string

    Parameters
    ----------
    notes_from_recording : list[Note]
        The notes that were extracted from a recording.
    target_notes_string : str
        The notes_string of a word that was attempted.

    Returns
    -------
    list[tuple[float, list[str], list[str]]] | None
        For each note:
        - The pitch offset (not rounded).
        - `in_note_and_not_target`: Characters representing the augmentations
            that were found in the recording but should NOT have been.
        - `in_target_and_not_note`: Characters representing the augmentations
            that were NOT found in the recording but should have been.
        Or `None` if the inputs are not of equal length.
    """
    target_list = target_notes_string.split(":")
    if len(target_list) != len(notes_from_recording):
        return None

    values_t, augmentations_t = get_notes_from_string(target_notes_string)

    deviances: list[tuple[float, list[str], list[str]]] = []
    for note, val_t, aug_string_t in zip(
        notes_from_recording, values_t, augmentations_t
    ):
        d_pitch: float = note.pitch - val_t
        in_note_and_not_target: list[str] = []
        in_target_and_not_note: list[str] = []
        for a in Augmentation:
            if a in note.augmentations and a.value not in aug_string_t:
                in_note_and_not_target.append(a.value)
            if a.value in aug_string_t and a not in note.augmentations:
                in_target_and_not_note.append(a.value)
        deviances.append((d_pitch, in_note_and_not_target, in_target_and_not_note))

    return deviances


def cut_notes_sentence_into_notes_per_word(
    notes_sentence: list[Note],
    target_words: list[Word | None],
) -> list[list[Note]]:
    """Cuts a `list` of notes into a `list` of `list`s of notes, on for each detected word.

    Parameters
    ----------
    notes_sentence : list[Note]
        All notes in the sentence.
    target_words : list[Word | None]
        The words to match.

    Returns
    -------
    list[list[Note]]
        The notes per word.
    """
    notes_per_word: list[list[Note]] = []
    for note in notes_sentence:
        if note.first_of_word:
            notes_per_word.append([])
        notes_per_word[-1].append(note)

    for i, word in enumerate(target_words):
        if word is None or word.nr_of_notes == 0:
            notes_per_word.insert(i, [])

    return notes_per_word


def determine_deviances_from_target_for_sentence(
    notes_from_recording: list[Note], target_words: list[Word | None]
) -> list[tuple[float, list[str], list[str]]] | None:
    """Determines how far off the notes from a recording are from the target sentence.

    Parameters
    ----------
    notes_from_recording : list[Note]
        The notes that were extracted from a recording.
    target_words : list[Word | None]
        The words to match.

    Returns
    -------
    list[tuple[float, list[str], list[str]]] | None
        For each note:
        - The pitch offset (not rounded).
        - `in_note_and_not_target`: Characters representing the augmentations
            that were found in the recording but should NOT have been.
        - `in_target_and_not_note`: Characters representing the augmentations
            that were NOT found in the recording but should have been.
        Or `None` if one of the target words is `None`,
        or if one of the words can't be matched due to length inconsistency.
    """
    notes_per_word = cut_notes_sentence_into_notes_per_word(
        notes_from_recording, target_words
    )
    total_deviances: list[tuple[float, list[str], list[str]]] = []
    for notes_for_word, word in zip(notes_per_word, target_words):
        if word is None:
            return None
        deviances = determine_deviances_from_target(
            notes_for_word, word.get_notes_string()
        )
        if deviances is None:
            return None
        total_deviances += deviances

    return total_deviances


def get_synthesised_versions_of_words(
    sentence: list[Word | None],
    notes_per_word: list[list[Note]],
    segment_bounds: segbounds,
    offset: float,
    sample_rate_recording: int,
    sample_rate_pm: int,
) -> list[floatlist | None]:
    """Creates synthesised versions of what the words should sound like.

    This function matches the speed of each individual word, and the key of the sentence as a whole,
    such that the synthesised versions will sound as close to the recording as possible.

    Parameters
    ----------
    sentence : list[Word | None]
        The words in the sentence, `None` for bits of the recording that weren't identified.
    notes : list[Note]
        The notes in the recording.
    segment_bounds : segbounds
        The onsets and ends of the recorded notes.
    offset : float
        The nr of semitones by which to transpose.
    sample_rate_recording : int
        The sample rate of the recording.
    sample_rate_pm : int
        The sample rate used in the pitch analysis.

    Returns
    -------
    list[floatlist | None]
        A wave for every successfully identified word.
    """
    nr_of_notes_per_word = [len(notes_for_word) for notes_for_word in notes_per_word]

    # determine speed per word
    speed_per_word: list[float | None] = []
    d_offsets: list[int] = []
    i_sb = 0
    for word, nr_of_notes in zip(sentence, nr_of_notes_per_word):
        if word is None:
            speed_per_word.append(None)
            d_offsets.append(0)
        elif (
            wave_for_word := word.wave(10, 0, sample_rate_recording)
        ) is None or word.name == "rest":
            speed_per_word.append(None)
            if word.name == "pi":
                d_offsets.append(2)
            if word.name in ["la", "unpi"]:
                d_offsets.append(-2)
        else:
            lower, _ = segment_bounds[i_sb]
            _, upper = segment_bounds[i_sb + nr_of_notes - 1]
            expected_nr_of_samples_from_segment_bounds = (
                (upper - lower) / sample_rate_pm * sample_rate_recording
            )
            nr_of_samples_for_synthesised_version = len(wave_for_word)
            speed_for_word = (
                10
                * nr_of_samples_for_synthesised_version
                / expected_nr_of_samples_from_segment_bounds
            )
            speed_per_word.append(speed_for_word)
            d_offsets.append(0)

        i_sb += nr_of_notes

    # create waves
    cum_offsets = np.cumsum(d_offsets)
    word_waves = [
        (
            word.wave(speed, offset + cum_offset, sample_rate_recording)
            if word is not None and speed is not None
            else None
        )
        for word, speed, cum_offset in zip(sentence, speed_per_word, cum_offsets)
    ]

    return word_waves


def merge_into_one_wave(
    wave_per_word: list[floatlist | None],
    len_recording: int,
    segment_bounds: segbounds,
    new_word_flags: list[bool],
    sample_rate_recording: int,
    sample_rate_pm: int,
) -> floatlist:
    """Turns synthesised waves, emulating a recording, into one big wave.

    Parameters
    ----------
    wave_per_word : list[floatlist | None]
        A wave for each word we want to merge, `None` for unindentified words.
    len_recording : int
        The length of the full original recording.
    segment_bounds : segbounds
        The onsets and ends of the recorded notes.
    new_word_flags : list[bool]
        A list of flags indicating which notes are the first of a word.
    sample_rate_recording : int
        The sample rate of the recording.
    sample_rate_pm : int
        The sample rate used in the pitch analysis.

    Returns
    -------
    floatlist
        The merged wave
    """
    full_wave = np.zeros(len_recording)
    word_bounds_in_recording = determine_bounds_for_words_in_recording(
        segment_bounds, new_word_flags, sample_rate_recording, sample_rate_pm
    )
    onsets = [onset for onset, _ in word_bounds_in_recording]
    wave_per_word_real: list[floatlist] = [
        wave for wave in wave_per_word if wave is not None
    ]

    for word_wave, onset in zip(wave_per_word_real, onsets):
        print(f"{onset = }")
        if word_wave is not None:
            print(f"{len(word_wave) = }")
            full_wave[onset : onset + len(word_wave)] = word_wave

    return full_wave


def determine_bounds_for_words_in_recording(
    segment_bounds: segbounds,
    new_word_flags: list[bool],
    sample_rate_recording: int,
    sample_rate_pm: int,
) -> segbounds:
    """Determines the start and end points of the words in a recording, in terms of samples.

    Parameters
    ----------
    segment_bounds : segbounds
        The segment bounds of the notes in the recorded sentence.
    new_word_flags : list[bool]
        A list of flags indicating which notes are the first of a word.
    sample_rate_recording : int
        The sample rate of the recording.
    sample_rate_pm : int
        The sample rate used in the pitch analysis.

    Returns
    -------
    list[tuple[int, int]]
        A `tuple` for every word, with the start and end index in terms of samples in the recording.
    """
    assert len(segment_bounds) == len(new_word_flags), "should be the same size"
    last_note_flags = new_word_flags[1:] + [True]
    onsets = [
        onset
        for (onset, _), new_word in zip(segment_bounds, new_word_flags)
        if new_word
    ]
    endings = [
        ending
        for (_, ending), last_note in zip(segment_bounds, last_note_flags)
        if last_note
    ]
    bounds_recording = [
        (
            (onset * sample_rate_recording) // sample_rate_pm,
            (ending * sample_rate_recording) // sample_rate_pm,
        )
        for onset, ending in zip(onsets, endings)
    ]
    return bounds_recording


def extract_recording_per_word(
    recording: floatlist,
    new_word_flags: list[bool],
    segment_bounds: segbounds,
    target_words: list[Word | None],
    sample_rate_recording: int,
    sample_rate_pm: int,
) -> list[floatlist | None]:
    """Processes a recording into segments for each individual word.

    Parameters
    ----------
    recording : floatlist
        The original recording.
    new_word_flags : list[bool]
        A list of flags indicating which notes are the first of a word.
    segment_bounds : segbounds
        The beginnings and ends of the words in terms of samples in the pitch analysis.
    target_words : list[Word]
        The words to match.
    sample_rate_recording : int
        The sample rate of the recording.
    sample_rate_pm : int
        The sample rate used in the pitch analysis.

    Returns
    -------
    list[floatlist|None]
        Waves for the individual words, or `None` as a placeholder for silent words.
    """
    segment_bounds_samples = determine_bounds_for_words_in_recording(
        segment_bounds, new_word_flags, sample_rate_recording, sample_rate_pm
    )
    recording_per_word: list[floatlist | None] = [
        marginify_wave(recording[onset - 4500 : end + 4500])
        for onset, end in segment_bounds_samples
    ]
    for i, word in enumerate(target_words):
        if word is None or word.nr_of_notes == 0 or word.name == "rest":
            recording_per_word.insert(i, None)

    return recording_per_word
