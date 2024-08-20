import json
import os
from words import Word

WORDS_FOLDER = "words"
COMPOSITE_WORDS_FOLDER = "generated_composites"
EXAMPLES_FILE = "examples.txt"
UNIMPORTANT_COMPOSITIONS_FILE = "unimportant_compositions.txt"
KU_PAIRS_FILE = "ku_pairs.json"


def save_words_to_folder(*words: Word, composite: bool = False) -> None:
    """Save each Word object as a JSON file in the specified folder."""
    if not os.path.exists(WORDS_FOLDER):
        os.makedirs(WORDS_FOLDER)
    if not os.path.exists(COMPOSITE_WORDS_FOLDER):
        os.makedirs(COMPOSITE_WORDS_FOLDER)

    words_folder = COMPOSITE_WORDS_FOLDER if composite else WORDS_FOLDER
    for word in words:
        file_path = os.path.join(words_folder, f"{word.name}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(word.to_json())


def load_words_from_folder(
    paths: list[str] = [WORDS_FOLDER, COMPOSITE_WORDS_FOLDER]
) -> list[Word]:
    """Load all Word objects from JSON files in the specified folder."""
    words: list[Word] = []
    for path in paths:
        if not os.path.exists(path):
            continue

        for filename in os.listdir(path):
            if filename == "DEFAULT.json":
                continue
            if filename.endswith(".json"):
                file_path = os.path.join(path, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    json_str = f.read()
                    word = Word.from_json(json_str)
                    words.append(word)

    return words


def save_examples_to_file(*examples: str) -> None:
    save_strings_to_file(examples, EXAMPLES_FILE)


def save_unimportant_compositions_to_file(*unimportant_compositions: str) -> None:
    save_strings_to_file(unimportant_compositions, UNIMPORTANT_COMPOSITIONS_FILE)


def save_strings_to_file(strings: tuple[str, ...], file_path: str) -> None:
    existing = load_strings_from_file(file_path)
    for string in strings:
        if not len(string) or string in existing:
            continue
        with open(file_path, "a", encoding="utf-8") as f:
            f.write("\n" + string)


def load_examples_from_file() -> list[str]:
    return load_strings_from_file(EXAMPLES_FILE)


def load_unimportant_compositions_from_file() -> list[str]:
    return load_strings_from_file(UNIMPORTANT_COMPOSITIONS_FILE)


def load_strings_from_file(file_path: str) -> list[str]:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        split = content.split("\n")
        return [string for string in split if string]


def load_ku_pairs_from_file() -> list[tuple[list[str], str]]:
    with open(KU_PAIRS_FILE, "r") as f:
        from_json = json.load(f)
        return [tuple(pair) for pair in from_json]


def get_default_word() -> Word:
    file_path = os.path.join(WORDS_FOLDER, "DEFAULT.json")
    with open(file_path, "r", encoding="utf-8") as f:
        json_str = f.read()
        word = Word.from_json(json_str)
    return word
