from copy import deepcopy
import json
import numpy as np

from src.augmentation import Augmentation
from src.util import generate_contractions
from src.wave_generation import (
    add_pause,
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

    def past_tensify(self):
        copy = self.copy()
        copy.past_tense = True
        return copy

    def comparativize(self):
        copy = self.copy()
        copy.comparative = True
        copy.superlative = False
        return copy

    def superlativize(self):
        copy = self.copy()
        copy.comparative = False
        copy.superlative = True
        return copy

    def pluralize(self):
        copy = self.copy()
        copy.plural = True
        return copy

    def questionify(self):
        copy = self.copy()
        copy.question = True
        return copy

    def finite_verbify(self):
        copy = self.copy()
        copy.finite_verb = True
        return copy

    def direct_objectify(self):
        copy = self.copy()
        copy.direct_object = True
        return copy


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


# def replace_slash_if_needed(s: str):
#     pattern = r"(\d+)/(\d+)"

#     def replacer(match: re.Match[str]):
#         left_num = int(match.group(1))
#         right_num = int(match.group(2))
#         if left_num > right_num:
#             return f"{left_num}\\{right_num}"
#         return match.group(0)

#     return re.sub(pattern, replacer, s)


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


def get_sentence_wave(
    sentence: list[Word], pause: float = 1, speed: float = 10, offset: float = 0
) -> floatlist:
    """Turns a `list` of words into a sound wave.

    Parameters
    ----------
    sentence : list[Word]
        The `list` of `Word` objects to turn into a sound wave.
    pause : float, optional
        The lengths of a pause, in proportion to a regular note, by default 1
    speed : int, optional
        The speed of the sound, which can be altered by the user, by default 10
    offset : float, optional
        The nr of semitones by which to transpose, by default 0

    Returns
    -------
    floatlist
        The sound wave associated with the sentence.
    """
    waves_per_word: list[floatlist] = []

    for word in sentence:
        if word.get_notes_string() == "+":
            offset += 2
            continue
        if word.get_notes_string() == "-":
            offset -= 2
            continue
        wave = word.wave(speed, offset)
        if wave is None:
            continue
        with_pause = add_pause(wave, pause, speed)
        waves_per_word.append(with_pause)

    return np.concatenate(waves_per_word)


def get_words_from_sentence(sentence: str, existing_words: list[Word]) -> list[Word]:
    """Converts a sentence (of text) to a `list` of `Word` objects.

    The words in the sentence have a couple of rules they should conform to.
    They have to be existing words in the language, with these modifications:
    - A word is allowed to start with a `"."`, indicating a direct object.
    - A word is allowed to start with a `"_"`, indicating a finite verb.
    - A word is allowed to have a `"-ed"` suffix, indicating past tense.
    - A word is allowed to have a `"-s"` suffix, indicating plural.
    - A word is allowed to have a `"-er"` suffix, indicating comparative.
    - A word is allowed to have a `"-est"` suffix, indicating superlative.
    - A word is allowed to have a `"-?"` suffix, indicating question.

    A word can have any number of suffices, but not both be comparative and superlative.
    A word can't both be a direct object and a finite verb.

    Parameters
    ----------
    sentence : str
        The sentence in text.
    existing_words : list[Word]
        The vocabulary of words, that the words in the sentence have to be based on.

    Returns
    -------
    list[Word]
        A `list` of `Word` objects, representing the sentence.

    Raises
    ------
    InvalidWordException
        If a word is not in the vocabulary.
    InvalidWordException
        If a word has an invalid suffix.
    """
    word_names = [word.name for word in existing_words]
    word_objects: list[Word] = []
    sentence = sentence.replace("!", "")
    for word_string in sentence.split(" "):
        if not len(word_string):
            continue
        if word_string.isnumeric():
            word_objects.append(NumberWord(int(word_string)))
            continue
        if word_string[0] == "_":
            finite_verb = True
            word_string = word_string[1:]
        else:
            finite_verb = False
        if word_string[0] == ".":
            direct_object = True
            word_string = word_string[1:]
        else:
            direct_object = False
        parts = word_string.split("-")
        if parts[0] not in word_names:
            raise InvalidWordException(parts[0])
        word_object = existing_words[word_names.index(parts[0])]
        if finite_verb:
            word_object = word_object.finite_verbify()
        if direct_object:
            word_object = word_object.direct_objectify()
        for part in parts[1:]:
            if part == "ed":
                word_object = word_object.past_tensify()
            elif part == "s":
                word_object = word_object.pluralize()
            elif part == "er":
                word_object = word_object.comparativize()
            elif part == "est":
                word_object = word_object.superlativize()
            elif part == "?":
                word_object = word_object.questionify()
            else:
                raise InvalidWordException(word_string)
        word_objects.append(word_object)
    return word_objects


# TODO: make
def get_prevalence(word: Word) -> int:
    return 0


todo = [
    "nimi (name, word)",
    "kepeken (to use)",
    "ijo (thing)",
    "ilo (tool)",
    "kin (also)",
    "ante (other)",
    "kalama (sound, to make noise, to play (instrument))",
    "sin (to add, new thing, addition, new, another)",
    "lipu (book, page, flat bendable thing, document, file)",
    "pakala (accident, mistake, damage, to hurt, to break, FUCK)",
    "kanker (kanker)",
    "soweli (animal, esp land animal)",
    "nasin (way, manner, road, path, system)",
]
