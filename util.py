from itertools import product
from typing import Any


def remove_sublist(main_list: list[Any], sub_list: list[Any]) -> list[Any] | None:
    """
    Returns a version of `main_list` without the first occurence of `sub_list`, if it's contained, otherwise returns None

    Parameters:
    -----------
    main_list : list[Any]
        The list to look for `sub_list` in.

    sub_list : list[Any]
        Should be clear.

    Returns:
    --------
    list[Any] | None
        `main_list` without the first occurence of `sub_list`
    """
    n, m = len(main_list), len(sub_list)
    for i in range(n - m + 1):
        if main_list[i : i + m] == sub_list:
            return main_list[:i] + main_list[i + m :]
    return None


def generate_contractions(
    list1: list[str], list2: list[str], max_overlap: int
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

    # for every potential size, we check the equality of the overlapping parts
    # we already included the trivial case, which has overlap 0, so now we start at 1
    for overlap in range(1, effective_max_overlap + 1):
        end_of_list1 = list1[-overlap:]
        start_of_list2 = list2[:overlap]

        # We create simplified versions, removing the underscores, to check for a match up to underscores
        end_of_list1_simplified = [note.replace("_", "") for note in end_of_list1]
        start_of_list2_simplified = [note.replace("_", "") for note in start_of_list2]

        if end_of_list1_simplified == start_of_list2_simplified:
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

    # Pair elements from both lists at each index
    pairs = zip(list1, list2)

    # Generate all possible combinations
    combinations = list(product(*pairs))

    # Remove duplicates by converting the list of combinations to a set
    combinations = list(set(combinations))

    # Convert each tuple in the list back to a list
    combinations = [list(comb) for comb in combinations]
    return combinations
