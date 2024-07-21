from words import (
    words,
    grammar_indicators,
    pronouns,
    hard_to_classify,
    colors,
    other_two_note_words,
    other_three_note_words,
    other_four_note_words,
    other_nonstandard_words,
)

print(len(words))
for w in words:
    if (
        w
        not in grammar_indicators
        + pronouns
        + hard_to_classify
        + colors
        + other_two_note_words
        + other_three_note_words
        + other_four_note_words
        + other_nonstandard_words
    ):
        print(w)

print(
    len(
        grammar_indicators
        + pronouns
        + hard_to_classify
        + colors
        + other_two_note_words
        + other_three_note_words
        + other_four_note_words
        + other_nonstandard_words
    )
)
