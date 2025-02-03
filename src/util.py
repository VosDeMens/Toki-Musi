import io
import soundfile as sf  # type: ignore
import base64
from itertools import product
import re
from typing import Any

from src.constants import ROOT, SAMPLE_RATE
from src.my_types import floatlist


def remove_sublist(main_list: list[Any], sub_list: list[Any]) -> list[Any] | None:
    """
    Returns a version of `main_list` without the first occurence of `sub_list`,
    if it's contained, otherwise returns None.

    Parameters:
    -----------
    main_list : list[Any]
        The list to look for `sub_list` in.

    sub_list : list[Any]
        ...

    Returns:
    --------
    list[Any] | None
        `main_list` without the first occurence of `sub_list`.
    """
    n, m = len(main_list), len(sub_list)
    for i in range(n - m + 1):
        if main_list[i : i + m] == sub_list:
            return main_list[:i] + main_list[i + m :]
    return None


def generate_contractions(
    list1: list[str],
    list2: list[str],
    max_overlap: int,
    well_formed: bool = False,
) -> list[list[str]]:
    """
    Generate all possible contractions of two notes lists based on their overlap.

    This function takes two lists of notes, and generates all possible
    contracted lists by finding overlaps between the end of the first list
    and the start of the second list, such that there will always be at least
    some evidence of both lists in the contraction, up to underscores.

    Parameters:
    -----------
    list1 : list[str]
        The first list of notes.
    list2 : list[str]
        The second list of notes.
    max_overlap : int
        The maximum number of overlapping elements to consider.

    Returns:
    --------
    list[list[str]]
        A list of lists, where each inner list is a possible contraction of `list1` and `list2`.

    Example:
    --------
    >>> list1 = ['0', '5', '7_', '5']
    >>> list2 = ['7', '5_', '9']
    >>> generate_contractions(list1, list2, 3)
    [['0', '5', '7_', '5', '7', '5_', '9'],
     ['0', '5', '7', '5', '9'],
     ['0', '5', '7', '5_', '9'],
     ['0', '5', '7_', '5', '9'],
     ['0', '5', '7_', '5_', '9']]
    """

    # There's always this trivial contraction
    valid_contractions: list[list[str]] = [list1 + list2]

    # Subtract 1 from both lengths bc otherwise the lists could fully get absorbed
    effective_max_overlap = min(max_overlap, len(list1) - 1, len(list2) - 1)

    # For every potential size, we check the equality of the overlapping parts.
    # We already included the trivial case, which has overlap 0, so now we start at 1
    for overlap in range(1, effective_max_overlap + 1):
        end_of_list1 = list1[-overlap:]
        start_of_list2 = list2[:overlap]

        # We create simplified versions, removing the underscores, to check for a match up to underscores
        end_of_list1_simplified = [note.replace("_", "") for note in end_of_list1]
        start_of_list2_simplified = [note.replace("_", "") for note in start_of_list2]

        if end_of_list1_simplified == start_of_list2_simplified:
            if well_formed:
                # The nicest contractions imo are the ones where the overlap between the words is possible
                # including underscores, except the last note of the left word, idc about that note lol
                all_underscore_combinations_of_overlap = (
                    [start_of_list2] if end_of_list1[:-1] == start_of_list2[:-1] else []
                )
            else:
                # Get all possibile choices for underscores in the overlap
                # Often will match exactly, and this will be a list of one element
                all_underscore_combinations_of_overlap = get_all_combinations(
                    end_of_list1, start_of_list2
                )

            # Here we add all possible choices in between the rest of the original lists
            rest_of_list1 = list1[:-overlap]
            rest_of_list2 = list2[overlap:]
            all_valid_contractions_using_overlaps = [
                [*rest_of_list1, *overlapping_bit, *rest_of_list2]
                for overlapping_bit in all_underscore_combinations_of_overlap
            ]

            # Add the new results to the list
            valid_contractions += all_valid_contractions_using_overlaps

    return valid_contractions


def get_all_combinations(list1: list[str], list2: list[str]) -> list[list[str]]:
    """
    Generates all possible combinations of elements from two lists

    This is done such that each combination is formed by selecting
    one element from the corresponding index of either list,
    by my limited biology knowledge, like genetic reproduction.

    Parameters:
    -----------
    list1 : list[str]
        The first list of strings.
    list2 : list[str]
        The second list of strings.

    Returns:
    --------
    list[list[str]]
        A list of unique combinations, where each combination is represented as a list of strings.

    Example:
    --------
    >>> list1 = ["3", "4_", "5"]
    >>> list2 = ["3", "4", "5_"]
    >>> get_all_combinations(list1, list2)
    [['3', '4', '5'], ['3', '4', '5_'], ['3', '4_', '5'], ['3', '4_', '5_']]
    """
    assert len(list1) == len(list2), "The two lists must be of equal length."
    pairs = zip(list1, list2)
    combinations = list(product(*pairs))
    combinations = list(set(combinations))
    combinations = [list(comb) for comb in combinations]
    return combinations


# def replace_nones(values: list[float | None], replacement: float = 0) -> list[float]:
#     return [x if x is not None else replacement for x in values]


def find_all_indices(s: str, sub_s: str) -> list[int]:
    """Finds the indices for all occurences of `sub_s` in `s`.

    Parameters
    ----------
    s : str
        String to search in.
    ss : str
        String to search for.

    Returns
    -------
    list[int]
        Indices of occurences.
    """
    return [match.start() for match in re.finditer(re.escape(sub_s), s)]


def split_numeric_part(s: str) -> tuple[int, str]:
    """Separates the numeric part from the non-numeric part following it.

    This function assumes a string that starts out numerically, and as soon as it finds
    any non-numeric character, makes the split right there without checking for more numbers later.

    Parameters
    ----------
    s : str
        A string containing a numeric part followed by a non-numeric part.

    Returns
    -------
    tuple[int, str]
        The numeric part, represented as an integer, and then the rest of the input string.
    """
    for i, c in enumerate(s):
        if not (i == 0 and c == "-" or c in "0123456789"):
            return (int(s[:i]), s[i:])
    return (int(s), "")


def pitch_to_freq(pitch: float, root: float = ROOT) -> float:
    """Turns a pitch value into the corresponding frequency.

    Parameters
    ----------
    note : float
        Pitch value to convert, where `0` corresponds to C.

    Returns
    -------
    float
        Frequency for provided pitch value.
    """
    return 440 * 2 ** ((pitch + root) / 12)


def audio_to_html(audio_array: floatlist, sample_rate: int = SAMPLE_RATE) -> str:
    """Turns a sound wave into a small inline playable HTML button.

    Parameters
    ----------
    audio_array : floatlist
        Sound wave.
    sample_rate : int
        Sample rate, by default SAMPLE_RATE := 44100

    Returns
    -------
    str
        Playable HTML object.
    """
    buffer = io.BytesIO()
    sf.write(buffer, audio_array, sample_rate, format="OGG")  # type: ignore
    buffer.seek(0)

    audio_base64 = base64.b64encode(buffer.read()).decode("utf-8")
    audio_base64_url = f"data:audio/ogg;base64,{audio_base64}"
    audio_html = f"""<audio controls style="vertical-align: middle; height: 1.5rem; width: 3rem">
        <source src="{audio_base64_url}" type="audio/ogg">
        Your browser does not support the audio element.
    </audio>
    """
    return audio_html
