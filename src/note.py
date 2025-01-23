from dataclasses import dataclass

from src.augmentation import Augmentation


@dataclass
class Note:
    """Represents a note in a sentence."""

    # average pitch of the note
    pitch: float
    # lengths of the note
    length: int
    # augmentations of the note (see augmentation.py)
    augmentations: list[Augmentation]
    # whether this note is the first of a word, determined by the length of the silence before it
    first_of_word: bool = False


def turn_into_notes_strings(notes: list[Note]) -> list[str]:
    """Converts a `list` of `Note` objects to a `list` of notes strings, one for each word.

    Parameters
    ----------
    notes : list[Note]
        The notes in a sentence, which can span multiple words.

    Returns
    -------
    list[str]
        A notes string for each word in the sentence.
    """
    if len(notes) == 0:
        return []
    words: list[list[str]] = []
    for note in notes:
        if note.first_of_word:
            words.append([])
        string_for_note = get_str_rep_for_note(round(note.pitch), note.augmentations)
        words[-1].append(string_for_note)

    words_strings: list[str] = [":".join(word) for word in words]
    return words_strings


def get_str_rep_for_note(note: int, augmentations: list[Augmentation]) -> str:
    """Converts the information for a single note into a string, in the format of a notes string.

    Parameters
    ----------
    note : int
        The rounded pitch value of this note.
    augmentations : list[Augmentation]
        A `list` of augmentations for this note.

    Returns
    -------
    str
        The string representation, in the format of a notes string, without colon.
    """
    str_rep = str(note)
    for a in Augmentation:
        if a in augmentations:
            str_rep += a.value

    return str_rep
