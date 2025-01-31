import numpy as np
from src.file_management import (
    WORDS_FOLDER,
    load_examples_from_file,
    load_words_from_folder,
)
from src.wave_generation import add_pause
from src.word import InvalidWordException, NumberWord, Word
from src.my_types import floatlist

BASIC_WORDS = load_words_from_folder([WORDS_FOLDER])
ALL_WORDS = load_words_from_folder()


def get_words_from_sentence(
    sentence: str,
    existing_words: list[Word] = ALL_WORDS,
    prefer_composites: bool = False,
) -> list[Word]:
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
    prefer_composites : bool
        Flag to interpret word combination that are contractable as one unit whenever possible,
        by default False

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
        for part in parts[1:]:
            if part == "s":
                word_object = word_object.pluralize()
            elif part == "er":
                word_object = word_object.comparativize()
            elif part == "est":
                word_object = word_object.superlativize()
            elif part == "ed":
                word_object = word_object.past_tensify()
            elif part == "?":
                word_object = word_object.questionify()
            else:
                raise InvalidWordException(word_string)
        if finite_verb:
            word_object = word_object.finite_verbify()
        if direct_object:
            word_object = word_object.direct_objectify()

        word_objects.append(word_object)

    if prefer_composites:
        word_objects_with_composites: list[Word] = []
        i = 0
        while i < len(word_objects):
            first_word_of_composite = word_objects[i]
            name_of_composite = first_word_of_composite.name
            j = 1
            while i + j < len(word_objects):
                next_word = word_objects[i + j]
                new_name = f"{name_of_composite} {next_word.name}"
                if next_word.is_modified() or new_name not in word_names:
                    break
                name_of_composite = new_name
                j += 1
            word_objects_with_composites.append(
                generate_composite(
                    name_of_composite,
                    first_word_of_composite,
                    word_names,
                    existing_words,
                )
            )
            i += j

        return word_objects_with_composites

    return word_objects


def generate_composite(
    name_of_composite: str,
    first_word_of_composite: Word,
    word_names: list[str],
    existing_words: list[Word],
) -> Word:
    """Creates a `Word` object from `name_of_composite`, with the modifications of `first_word_of_composite`.

    Parameters
    ----------
    name_of_composite : str
        The name of the composite word to generate.
    first_word_of_composite : Word
        The first word in the composition, whose modifications will be copied to the composite.
    word_names : list[str]
        The names of all existing words, in the same order as `existing_words`.
    existing_words : list[Word]
        `Word` objects for all existing words, in the same order as `word_name`.

    Returns
    -------
    Word
        The composite word.
    """
    composite_object = existing_words[word_names.index(name_of_composite)]
    composite_object = composite_object.pluralize(first_word_of_composite.plural)
    composite_object = composite_object.comparativize(
        first_word_of_composite.comparative
    )
    composite_object = composite_object.superlativize(
        first_word_of_composite.superlative
    )
    composite_object = composite_object.past_tensify(first_word_of_composite.past_tense)
    composite_object = composite_object.questionify(first_word_of_composite.question)
    composite_object = composite_object.finite_verbify(
        first_word_of_composite.finite_verb
    )
    composite_object = composite_object.direct_objectify(
        first_word_of_composite.direct_object
    )
    return composite_object


def determine_prevalences(examples: list[tuple[str, str]]) -> dict[str, int]:
    """Determines the total number of times each word appears in `examples`.

    Parameters
    ----------
    examples : list[tuple[str, str]]
        The examples to look through.

    Returns
    -------
    dict[str, int]
        The number of appearances for each word.
    """
    prevalences: dict[str, int] = {w.name: 0 for w in ALL_WORDS}
    for tm, _ in examples:
        try:
            words = get_words_from_sentence(tm, BASIC_WORDS)
            for word in words:
                if isinstance(word, NumberWord):
                    continue
                name = word.name
                prevalences[name] += 1
        except InvalidWordException:
            continue
    return prevalences


EXAMPLES = load_examples_from_file()
PREVALENCES: dict[str, int] = determine_prevalences(EXAMPLES)


def get_prevalence(word: Word) -> int:
    """Gives the total number of times `word` appears in the example sentences.

    Parameters
    ----------
    word : Word
        The word to look for.

    Returns
    -------
    int
        The number of times it appears.
    """
    if isinstance(word, NumberWord) or word.name not in PREVALENCES:
        return 0
    return PREVALENCES[word.name]


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
