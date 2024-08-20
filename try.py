import pymupdf  # type: ignore # PyMuPDF

from local_stuff import load_strings_from_file

ALL_TOKI_PONA_WORDS = load_strings_from_file("toki_pona_words.txt")

DOC = pymupdf.open("ku.pdf")


def get_toki_pona_components(word: str) -> list[str] | None:
    for to_remove in ".,?!:_":
        word = word.replace(to_remove, "")
    if word in ALL_TOKI_PONA_WORDS:
        return [word]
    for i in range(1, len(word)):
        if word[:i] in ALL_TOKI_PONA_WORDS and word[i:] in ALL_TOKI_PONA_WORDS:
            return [word[:i], word[i:]]
    return None


def get_toki_pona_words_in_line(
    words_in_line: list[str], desired_len: int
) -> tuple[list[str], str] | None:
    toki_pona_words_in_line: list[str] = []
    for idx, word in enumerate(words_in_line):
        toki_pona_components = get_toki_pona_components(word)
        if toki_pona_components is None:
            break
        toki_pona_words_in_line += toki_pona_components
    if len(toki_pona_words_in_line) == desired_len:
        tail = " ".join(words_in_line[idx:])
        return toki_pona_words_in_line, tail


def get_pairs_from_page(
    page_nr: int, desired_len: int = 2
) -> list[tuple[list[str], str]]:
    toki_pona_pairs: list[tuple[list[str], str]] = []

    page = DOC.load_page(page_nr)
    text = page.get_text("dict")  # type: ignore # Get text as a dictionary with formatting

    for block in text["blocks"]:  # type: ignore
        if "lines" not in block:
            continue
        for line in block["lines"]:  # type: ignore
            words_in_line: list[str] = [
                word
                for span in line["spans"]
                for word in span["text"].split(" ")
                if len(word)
            ]
            toki_pona_words_in_line: tuple[list[str], str] | None = (
                get_toki_pona_words_in_line(words_in_line, desired_len)
            )
            if toki_pona_words_in_line is None:
                continue
            toki_pona_pairs.append(toki_pona_words_in_line)

    return toki_pona_pairs


if __name__ == "__main__":
    import json

    toki_pona_pairs = [
        pair for page_nr in range(99, 196) for pair in get_pairs_from_page(page_nr)
    ]

    for p in toki_pona_pairs:
        print(p)
    with open("ku_pairs.json", "w") as f:
        json.dump(toki_pona_pairs, f)
