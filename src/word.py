from copy import deepcopy
import json

from src.augmentation import Augmentation
from src.util import generate_contractions
from src.wave_generation import (
    pcw_from_string,
)
from src.my_types import floatlist


class Word:
    def __init__(
        self,
        name: str,
        notes_string: str,
        description: str,
        nr_of_notes: int,
        etymelogies: list[str],
        toki_pona: bool = False,
        particle: bool = False,
        content_word: bool = False,
        preposition: bool = False,
        interjection: bool = False,
        pluralizable: bool = False,
        past_tensifiable: bool = False,
        comparativizable: bool = False,
        questionifiable: bool = False,
        colour: bool = False,
        composite: bool = False,
        plural: bool = False,
        past_tense: bool = False,
        comparative: bool = False,
        superlative: bool = False,
        question: bool = False,
        finite_verb: bool = False,
        direct_object: bool = False,
    ):
        self.name = name
        self.notes_string = notes_string
        self.description = description
        self.nr_of_notes = nr_of_notes
        self.etymelogies = etymelogies
        self.toki_pona = toki_pona
        self.particle = particle
        self.content_word = content_word
        self.preposition = preposition
        self.interjection = interjection
        self.pluralizable = pluralizable
        self.past_tensifiable = past_tensifiable
        self.comparativizable = comparativizable
        self.questionifiable = questionifiable
        self.colour = colour
        self.composite = composite
        self.plural = plural
        self.past_tense = past_tense
        self.comparative = comparative
        self.superlative = superlative
        self.question = question
        self.finite_verb = finite_verb
        self.direct_object = direct_object

    def copy(self) -> "Word":
        return deepcopy(self)

    def to_json(self) -> str:
        return json.dumps(self.__dict__, indent=4)

    @classmethod
    def from_json(cls, json_str: str) -> "Word":
        data = json.loads(json_str)
        return cls(**data)

    @classmethod
    def compose(
        cls, word1: "Word", word2: "Word", description: str, notes_string: str
    ) -> "Word":
        """Creates a composition of two existing words, with notes based on the components' notes.

        The new word will automatically have its etymelogy filled in, showing how its notes
        are derived from `word1` and `word2`.
        Other properties are mostly based on the first word.

        Parameters
        ----------
        word1 : Word
            The first word in the composition.
        word2 : Word
            The second word in the composition.
        description : str
            The description for the new word.
        notes_string : str
            The notes string for the new word.

        Returns
        -------
        Word
            Composite word.
        """
        n1 = word1.notes_string.split(":")[1:]
        n2 = word2.notes_string.split(":")[1:]
        nc = notes_string.split(":")[1:]
        assert ":".join(nc) in [
            ":".join(c)
            for c in generate_contractions(n1, n2, min(len(n1) - 1, len(n2) - 1))
        ], "not a possible contraction"
        overlap = len(n1) + len(n2) - len(nc)
        notes_string_rep = f"{word1.notes_string}:**~~{':'.join((['0']+n2)[:overlap+1])}~~**:{':'.join((['0']+n2)[overlap+1:])}"
        etymelogies = [
            f"composite word from {word1.name} and {word2.name} {notes_string_rep}"
        ]
        composite_word = cls(
            f"{word1.name} {word2.name}",
            notes_string,
            description,
            len(nc) + 1,
            etymelogies,
            False,
            word1.particle,
            word1.content_word,
            word1.preposition,
            word1.interjection,
            word1.pluralizable,
            word1.past_tensifiable,
            word1.comparativizable,
            word1.questionifiable,
            word1.colour,
            True,
        )

        return composite_word

    def wave(self, speed: float = 10, offset: float = 0) -> floatlist | None:
        """Synthesises a sound wave for this word.

        Parameters
        ----------
        speed : int, optional
            Speed of the sound, which can be altered by the user, by default 10
        offset : float, optional
            Semitones to transpose by, where `0` corresponds to C, by default 0

        Returns
        -------
        floatlist
            A well-behaved sound wave, matching the provided frequencies at every point in time.
        """
        if self.nr_of_notes == 0:
            return None
        return pcw_from_string(self.get_notes_string(), speed, offset)

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, type(self))
            and self.name == value.name
            and self.plural == value.plural
            and self.comparative == value.comparative
            and self.superlative == value.superlative
            and self.past_tense == value.past_tense
            and self.question == value.question
            and self.finite_verb == value.finite_verb
            and self.direct_object == value.direct_object
        )

    def __str__(self):
        return f'{self.name}{" (past tense)" if self.past_tense else ""}{" (comparative)" if self.comparative else ""}{" (superlative)" if self.superlative else ""}{" (plural)" if self.plural else ""}{" (question)" if self.question else ""}{" (finite verb)" if self.finite_verb else ""}{" (direct object)" if self.direct_object else ""}'

    def __repr__(self):
        return str(self)

    def get_notes_string(self, to_print: bool = False):
        assert not (
            self.comparative and self.superlative
        ), "can't have word that's both comparative and superlative"
        assert not (
            self.finite_verb and self.direct_object
        ), "can't have word that's both finite verb and direct object"

        string = self.notes_string
        if self.plural:
            string += Augmentation.LONG.value
        if self.comparative:
            string += Augmentation.TRILL_DOWN.value
        if self.superlative:
            string += Augmentation.TRILL_UP.value
        if self.past_tense:
            string += Augmentation.SLIDE_DOWN.value
        if self.question:
            string += Augmentation.SLIDE_UP.value
        if string[0] == ":":
            string = string[1:]
        if self.finite_verb:
            index = find_index_after_number(string)
            string = string[:index] + "_" + string[index:]
        if self.direct_object:
            string = "0:" + string
        if to_print:
            string = make_printable(string)
        return string

    def pluralize(self, value: bool = True):
        copy = self.copy()
        copy.plural = value
        return copy

    def comparativize(self, value: bool = True):
        copy = self.copy()
        copy.comparative = value
        if value:
            copy.superlative = False
        return copy

    def superlativize(self, value: bool = True):
        copy = self.copy()
        if value:
            copy.comparative = False
        copy.superlative = value
        return copy

    def past_tensify(self, value: bool = True):
        copy = self.copy()
        copy.past_tense = value
        return copy

    def questionify(self, value: bool = True):
        copy = self.copy()
        copy.question = value
        return copy

    def finite_verbify(self, value: bool = True):
        copy = self.copy()
        copy.finite_verb = value
        return copy

    def direct_objectify(self, value: bool = True):
        copy = self.copy()
        copy.direct_object = value
        return copy

    def is_modified(self) -> bool:
        """Whether this word has any modification at all.

        Returns
        -------
        bool
            ...
        """
        return (
            self.plural
            or self.comparative
            or self.superlative
            or self.past_tense
            or self.question
            or self.finite_verb
            or self.direct_object
        )


class NumberWord(Word):
    """A word representing a number.

    A number `n` can be whistled as a sequence of `n` short notes, or as a binary string,
    such that a long note represents a 1 and a short note represents a 0.
    """

    def __init__(self, n: int, binary_representation: bool | None = None):
        if binary_representation is not None:
            self.binary_representation = binary_representation
        else:
            # a sequence of notes longer than 8 is hard to distinguish
            self.binary_representation: bool = n > 8

        notes_string: str = convert_number_to_notes_string(
            n, self.binary_representation
        )

        super().__init__(
            str(n),
            notes_string,
            f"the number {n}",
            notes_string.count(":") + 1,
            [
                "Numbers are represented in one of two ways:\n1. By repeated short notes\n2. In binary form, where a long note represents a 1 and a short note represents a 0\nSo 5 could be represented like 0:0:0:0:0 or like 0_:0:0_."
            ],
        )


def convert_number_to_notes_string(n: int, binary: bool) -> str:
    """Generates the notes string for a number `n`.

    See the doc for the NumberWord class.

    Parameters
    ----------
    n : int
        Number to convert to a notes string.
    binary : bool
        Flag indicating whether to represent the number as a binary string.

    Returns
    -------
    str
        The appropriate notes string.
    """
    if binary:
        return binary_notes_string(n)
    return ":".join(n * "0")


def binary_number_str(n: int) -> str:
    """See Examples below.

    Examples
    --------
    >>> binary_number_str(5)
    '101'
    """
    return str(bin(n))[2:]


def binary_notes_string(n: int) -> str:
    """See Examples below.

    Examples
    --------
    >>> binary_number_str(5)
    '0_:0:0_'
    """
    binary: str = binary_number_str(n)
    binary_separated_by_colons: str = ":".join(binary)
    notes_string = binary_separated_by_colons.replace("1", "0_")
    return notes_string


def is_number_notes_string(s: str) -> bool:
    """Tells you whether `s` represents a number, assuming `s` is a valid notes string.

    Parameters
    ----------
    s : str
        Notes string

    Returns
    -------
    bool
        ...
    """
    return all(c in ("0", ":", "_") for c in s)


def notes_string_to_number(s: str) -> int:
    """Converts `s` to a number.

    Parameters
    ----------
    s : str
        Notes string.

    Returns
    -------
    int
        ...
    """
    assert is_number_notes_string(s), "invalid number notes string"
    if not "_" in s:
        return s.count("0")
    s = s.replace("0_", "1")
    s = s.replace(":", "")
    return int(s, 2)


def make_printable(notes_string: str) -> str:
    """Turns a notes string into one that can be printed neatly.

    Parameters
    ----------
    notes_string : str
        Notes string to print.

    Returns
    -------
    str
        Formatted notes string.
    """
    # printable_string = replace_slash_if_needed(notes_string)
    printable_string = notes_string.replace("__", "_")
    printable_string = printable_string.replace(":-1:", ":&#8203;-1:")
    printable_string = printable_string.replace("\\", "\\\\")
    if printable_string == "+":
        return "[key change +2]"
    if printable_string == "-":
        return "[key change -2]"
    return printable_string


def find_index_after_number(s: str) -> int:
    """Finds the index after the first number in `s`.

    Parameters
    ----------
    s : str
        Notes string.

    Returns
    -------
    int
        Index after the first number in `s`.
    """
    number_found = False
    for i, char in enumerate(s):
        if char.isdigit():
            number_found = True
        elif number_found:
            return i
    return -1


class InvalidWordException(Exception):
    pass


class MessingWithNumberException(Exception):
    pass
