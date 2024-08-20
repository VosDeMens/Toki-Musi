import unittest

from clashes_checking import (
    generate_contractions_for_phrase,
    get_all_clashes_matching_exactly,
    find_clashes,
    clash_is_redundant,
    DUMMY_WORD_NAME,
)
from util import generate_contractions, get_all_combinations, remove_sublist
from local_stuff import load_words_from_folder
from words import Word


class TestFunctions(unittest.TestCase):
    def setUp(self):
        self.test_words: dict[str, Word] = {
            word.name: word for word in load_words_from_folder(["tests/test_words"])
        }

    def test_generate_contractions_0(self):
        list1 = ["0", "7", "5_", "4"]
        list2 = ["5", "4_", "7"]
        max_overlap = 2
        expected = {
            ("0", "7", "5_", "4", "5", "4_", "7"),
            ("0", "7", "5", "4", "7"),
            ("0", "7", "5", "4_", "7"),
            ("0", "7", "5_", "4", "7"),
            ("0", "7", "5_", "4_", "7"),
        }
        result = set(
            [
                tuple(contraction)
                for contraction in generate_contractions(list1, list2, max_overlap)
            ]
        )
        self.assertEqual(result, expected)

    def test_generate_contractions_1(self):
        list1 = ["0", "7", "5_", "4"]
        list2 = ["5", "4_", "7"]
        max_overlap = 1
        expected = {("0", "7", "5_", "4", "5", "4_", "7")}
        result = set(
            [
                tuple(contraction)
                for contraction in generate_contractions(list1, list2, max_overlap)
            ]
        )
        self.assertEqual(result, expected)

    def test_generate_contractions_2(self):
        list1 = ["0", "7", "5_", "4"]
        list2 = ["5", "4_", "7"]
        max_overlap = 10
        expected = {
            ("0", "7", "5_", "4", "5", "4_", "7"),
            ("0", "7", "5", "4", "7"),
            ("0", "7", "5", "4_", "7"),
            ("0", "7", "5_", "4", "7"),
            ("0", "7", "5_", "4_", "7"),
        }
        result = set(
            [
                tuple(contraction)
                for contraction in generate_contractions(list1, list2, max_overlap)
            ]
        )
        self.assertEqual(result, expected)

    def test_get_all_combinations(self):
        list1 = ["3", "4_", "5"]
        list2 = ["3", "4", "5_"]
        expected = {
            ("3", "4", "5"),
            ("3", "4", "5_"),
            ("3", "4_", "5"),
            ("3", "4_", "5_"),
        }
        result = set(
            [tuple(combination) for combination in get_all_combinations(list1, list2)]
        )
        self.assertEqual(result, expected)

    def test_generate_contractions_for_phrase(self):
        words_to_go: list[Word] = [
            self.test_words["tawa"],
            self.test_words["tomo_"],
            self.test_words["tawa"],
        ]
        expected = {"0:4:7:7:4:4:7", "0:4:7:4:4:7", "0:4:7:7:4:7"}
        result = set(generate_contractions_for_phrase(words_to_go))
        self.assertEqual(result, expected)

    def test_get_all_clashes_matching_exactly(self):
        notes_to_match = ["0", "4", "7", "4"]
        candidates = [self.test_words["tawa"], self.test_words["tomo_"]]
        expected = [[self.test_words["tawa"], self.test_words["tomo_"]]]
        result = get_all_clashes_matching_exactly(notes_to_match, candidates, 3)
        self.assertEqual(result, expected)

    def test_find_clashes(self):
        notes_string = "0:6"
        max_extra = 1
        new_word = Word(
            DUMMY_WORD_NAME, notes_string, "", notes_string.count(":") + 1, []
        )
        expected = [
            (
                [self.test_words["pimeja"], new_word],
                [self.test_words["purple"]],
                "0:2:3:5:6",
            )
        ]
        result = find_clashes(
            notes_string, max_extra, existing_words=list(self.test_words.values())
        )
        self.assertEqual(result, expected)

    def test_remove_sublist(self):
        superlist = [1, 2, 3, 4]

        sublist = [1, 2]
        expected = [3, 4]
        result = remove_sublist(superlist, sublist)
        self.assertEqual(result, expected)

        sublist = [0, 1, 2]
        expected = None
        result = remove_sublist(superlist, sublist)
        self.assertEqual(result, expected)

        sublist = [3]
        expected = [1, 2, 4]
        result = remove_sublist(superlist, sublist)
        self.assertEqual(result, expected)

        sublist = [1, 3]
        expected = None
        result = remove_sublist(superlist, sublist)
        self.assertEqual(result, expected)

    def test_clash_is_redundant(self):
        nasa: Word = Word("nasa", "0:6", "", 2, [])
        old_phrase: list[Word] = [self.test_words["pimeja"], nasa]
        old_match: list[Word] = [self.test_words["purple"]]
        old_clashes = [(old_phrase, old_match, self.test_words["purple"].notes_string)]

        new_phrase = old_phrase + [self.test_words["tawa"]]
        new_match = old_match + [self.test_words["tawa"]]
        new_clash = (new_phrase, new_match, "")
        result = clash_is_redundant(new_clash, old_clashes)
        self.assertTrue(result)

        new_phrase = old_phrase + [self.test_words["tawa"]]
        new_match = old_match + [self.test_words["laso"]]
        new_clash = (new_phrase, new_match, "")
        expected = False
        result = clash_is_redundant(new_clash, old_clashes)
        self.assertEqual(result, expected)

        new_phrase = old_phrase + [self.test_words["tawa"]]
        new_match = [self.test_words["laso"]]
        new_clash = (new_phrase, new_match, "")
        expected = False
        result = clash_is_redundant(new_clash, old_clashes)
        self.assertEqual(result, expected)

        new_phrase = [self.test_words["laso"]] + old_phrase + [self.test_words["tawa"]]
        new_match = [self.test_words["laso"]] + old_match + [self.test_words["tawa"]]
        new_clash = (new_phrase, new_match, "")
        expected = True
        result = clash_is_redundant(new_clash, old_clashes)
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
