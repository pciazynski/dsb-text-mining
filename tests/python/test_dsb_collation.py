import pytest

from dsb_collation import dsb_sortkey

# The current Lower Sorbian alphabet, in order.
ALPHABET = [
    "a",
    "b",
    "c",
    "č",
    "ć",
    "d",
    "e",
    "ě",
    "f",
    "g",
    "h",
    "i",
    "j",
    "k",
    "ł",
    "l",
    "m",
    "n",
    "ń",
    "o",
    "ó",
    "p",
    "r",
    "ŕ",
    "s",
    "š",
    "ś",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",
    "ž",
    "ź",
]


def test_full_alphabet_order():
    keys = [dsb_sortkey(ch) for ch in ALPHABET]
    assert keys == sorted(keys)
    assert len(set(keys)) == len(keys)


@pytest.mark.parametrize(
    ("earlier", "later"),
    [
        ("c", "č"),  # č after c
        ("č", "ć"),  # ć after č
        ("ł", "l"),  # ł before l
        ("ž", "ź"),  # ź is the last letter
        ("k", "ł"),
        ("n", "ń"),
        ("s", "š"),
        ("š", "ś"),
    ],
)
def test_pairwise_letter_order(earlier, later):
    assert dsb_sortkey(earlier) < dsb_sortkey(later)


def test_sorting_words_follows_dsb_order():
    words = ["cas", "łas", "las", "źeń", "čas", "abc", "zeń", "žeń"]
    expected = ["abc", "cas", "čas", "łas", "las", "zeń", "žeń", "źeń"]
    assert sorted(words, key=dsb_sortkey) == expected


def test_case_insensitive():
    assert dsb_sortkey("Čas") == dsb_sortkey("čas")
    assert dsb_sortkey("ŁUKA") == dsb_sortkey("łuka")


def test_known_letters_fixed_width():
    # Every known letter contributes exactly two digits.
    for word in ("a", "ab", "jabłuko"):
        assert len(dsb_sortkey(word)) == 2 * len(word)


def test_shorter_word_is_prefix_of_extension():
    # Byte comparison must place "wód" before "wóda".
    assert dsb_sortkey("wóda").startswith(dsb_sortkey("wód"))
    assert dsb_sortkey("wód") < dsb_sortkey("wóda")


def test_unknown_chars_sort_after_all_known_letters():
    # ź is the greatest known letter; punctuation/digits must come after it.
    for ch in ("-", "'", "0", "9", "?"):
        assert dsb_sortkey(ch) > dsb_sortkey("ź")


def test_unknown_chars_ordered_by_codepoint():
    assert dsb_sortkey("'") < dsb_sortkey("-")  # ord("'") < ord("-")
