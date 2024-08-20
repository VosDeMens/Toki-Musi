from copy import deepcopy
import json
from util import generate_contractions
from wave_generation import (
    freq_timeline_from_str,
    generate_phase_continuous_wave,
    add_pause,
)
from my_types import floatlist

import os
import numpy as np
import re

WORDS_FOLDER = "words"


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
        n1 = word1.notes_string.split(":")[1:]
        n2 = word2.notes_string.split(":")[1:]
        nc = notes_string.split(":")[1:]
        assert ":".join(nc) in [":".join(c) for c in generate_contractions(
            n1, n2, min(len(n1) - 1, len(n2) - 1)
        )], "not a possible contraction"
        overlap = len(n1) + len(n2) - len(nc)
        notes_string_rep = f"{word1.notes_string}:**~~{":".join((["0"]+n2)[:overlap+1])}~~**:{":".join((["0"]+n2)[overlap+1:])}"
        etymelogies = [f"composite word from {word1.name} and {word2.name} {notes_string_rep}"]
        composite_word = cls(
            f"{word1.name} {word2.name}",
            notes_string, description,
            len(nc)+1,
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
            True
            )
            
        return composite_word
    
    def wave(self, speed: int = 10) -> floatlist:
        ft = freq_timeline_from_str(self.get_notes_string(), speed)
        return generate_phase_continuous_wave(ft)

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, Word)
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
        string = self.notes_string
        notes: list[str] = [note for note in re.split(r"[:/~^_]", string) if len(note)]
        try:
            last_note: int | None = int(notes[-1])
        except ValueError:
            last_note = None

        if self.past_tense:
            if last_note is None:
                raise ValueError("can't past tensify rest")
            string += "/" + str(last_note - 7)
        if self.comparative:
            if last_note is None:
                raise ValueError("can't comparativise rest")
            string += "~"
        if self.superlative:
            if last_note is None:
                raise ValueError("can't superlativise rest")
            string += "^"
        if self.plural:
            string += "__"
        if self.question:
            if last_note is None:
                raise ValueError("can't questionify rest")
            string += "/" + str(last_note + 7)
        if string[0] == ":":
            string = string[1:]
        if self.finite_verb:
            index = find_index_after_number(string)
            string = string[:index] + "_" + string[index:]
        if self.direct_object:
            string = "0:" + string
        if to_print:
            string = string.replace("__", "_")
        if to_print:
            string = string.replace(":-1:", ":&#8203;-1:")
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


def load_words_from_folder() -> list[Word]:
    """Load all Word objects from JSON files in the specified folder."""
    words: list[Word] = []
    if not os.path.exists(WORDS_FOLDER):
        return words

    for filename in os.listdir(WORDS_FOLDER):
        if filename == "DEFAULT.json":
            continue
        if filename.endswith(".json"):
            file_path = os.path.join(WORDS_FOLDER, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                json_str = f.read()
                word = Word.from_json(json_str)
                words.append(word)

    return words


def find_index_after_number(s: str) -> int:
    number_found = False
    for i, char in enumerate(s):
        if char.isdigit():
            number_found = True
        elif number_found:
            return i
    return -1


class InvalidWordException(Exception):
    pass


def get_sentence_wave(
        
    sentence: list[Word], pause: float = 1, speed: int = 10
) -> floatlist:
    waves_per_word = [word.wave(speed) for word in sentence]
    waves_per_word = [add_pause(wave, pause, speed) for wave in waves_per_word]
    return np.concatenate(waves_per_word)


def get_words_from_sentence(sentence: str, existing_words: list[Word]) -> list[Word]:
    word_names = [word.name for word in existing_words]
    word_objects: list[Word] = []
    sentence = sentence.replace("!", "")
    for word_string in sentence.split(" "):
        if not len(word_string):
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
