import json
import os

from src.words import Word

BASE_PATH = os.path.dirname(os.path.abspath(__file__))


def create_path(p: str, base: str = BASE_PATH) -> str:
    return os.path.join(base, p)


WORDS_FOLDER = create_path("../resources/words")
COMPOSITE_WORDS_FOLDER = create_path("../resources/generated_composites")
EXAMPLES_FILE = create_path("../resources/examples.txt")
UNIMPORTANT_COMPOSITIONS_FILE = create_path("../resources/unimportant_compositions.txt")
KU_PAIRS_FILE = create_path("../resources/ku_pairs.json")
COMPOUNDS_FILE = create_path("../resources/compounds.txt")
TOKI_PONA_WORDS_FILE = create_path("../resources/toki_pona_words.txt")
WHISTLE_COACH_INSTRUCTIONS_FILE = create_path(
    "../resources/whistle_coach_instructions.md"
)
TRANSCRIBE_COACH_INSTRUCTIONS_FILE = create_path(
    "../resources/transcribe_coach_instructions.md"
)


def save_words_to_folder(*words: Word, composite: bool = False) -> None:
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


def load_examples_from_file() -> list[tuple[str, str]]:
    return [
        ((splat := line.split(" - "))[0], splat[1])
        for line in load_strings_from_file(EXAMPLES_FILE)
        if line
    ]


def load_unimportant_compositions_from_file() -> set[str]:
    return set(load_strings_from_file(UNIMPORTANT_COMPOSITIONS_FILE))


def load_strings_from_file(
    file_path: str, delete_empty_lines: bool = True
) -> list[str]:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        split = content.split("\n")
        if delete_empty_lines:
            split = [string for string in split if string]
        return split


def load_contents_from_file(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        contents = f.read()
        return contents


def load_markdown_from_file(file_path: str) -> str:
    assert file_path[-3:] == ".md", "not a .md file"
    return load_contents_from_file(file_path)


def load_js_from_file(file_path: str) -> str:
    assert file_path[-3:] == ".js", "not a .js file"
    return load_contents_from_file(file_path)


def load_ku_pairs_from_file() -> list[tuple[tuple[str, str], str]]:
    with open(KU_PAIRS_FILE, "r") as f:
        from_json = json.load(f)
        return [(tuple(pair), translation) for pair, translation in from_json]


def load_popular_ku_pairs_from_file() -> list[tuple[tuple[str, str], str]]:
    # the content of the file starts after a disclaimer
    strings: list[str] = load_strings_from_file(COMPOUNDS_FILE)[14:]

    # left of the colon is the toki pona, right are the translations
    split_by_colon: list[list[str]] = [string.split(":") for string in strings]

    # except sometimes there's a colon in the translation
    merged: list[tuple[str, str]] = [
        (toki_pona, ":".join(translation_split))
        for toki_pona, *translation_split in split_by_colon
    ]

    # we then turn the left side into tuples of individual toki pona words
    compounds: list[tuple[tuple[str, ...], str]] = [
        (tuple(toki_pona.split(" ")), translations)
        for toki_pona, translations in merged
    ]

    # then only select those that have exactly 2 words
    pairs: list[tuple[tuple[str, str], str]] = [
        (toki_pona, translations)
        for toki_pona, translations in compounds
        if len(toki_pona) == 2
    ]
    return pairs


def load_to_do() -> list[str]:
    toki_pona_words = load_strings_from_file(TOKI_PONA_WORDS_FILE)
    present_words = [word.name for word in load_words_from_folder()]
    undone = [word for word in toki_pona_words if word not in present_words]
    irrelevant_words = ["ali", "e", "li", "pu", "meli", "mije", "oko"]
    todo = [word for word in undone if word not in irrelevant_words]
    return todo


def get_default_word() -> Word:
    file_path = os.path.join(WORDS_FOLDER, "DEFAULT.json")
    with open(file_path, "r", encoding="utf-8") as f:
        json_str = f.read()
        word = Word.from_json(json_str)
    return word
