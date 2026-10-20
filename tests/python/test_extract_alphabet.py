import importlib
import os

import extract_alphabet

# The example from the spec: token/frequency lines, tab separated.
EXAMPLE_INPUT = """a	17307
ße	7204
jo	6987
na	5728
we	5219
To	4570
ten	3918
až	3775
do	2981
ja	2866
ſ	2843.
"""

EXAMPLE_OUTPUT = "a d e j n o ß ſ T t w ž"


def test_extract_alphabet_example_returns_unique_letters_in_dsb_order():
    assert extract_alphabet.extract_alphabet(EXAMPLE_INPUT) == EXAMPLE_OUTPUT.split(" ")


def test_extract_alphabet_omits_digits_and_punctuation():
    assert extract_alphabet.extract_alphabet("a1b2.3-c\n") == ["a", "b", "c"]


def test_extract_alphabet_sorts_special_characters_after_their_base_letter():
    assert extract_alphabet.extract_alphabet("tśsr") == ["r", "s", "ś", "t"]


def test_extract_alphabet_places_unlisted_latin_letter_in_alphabetical_position():
    # A plain Latin letter absent from the explicit DSB order (here "q") must
    # sort at its natural alphabetical position, not get dumped at the end.
    assert extract_alphabet.extract_alphabet("rqp") == ["p", "q", "r"]


def test_extract_alphabet_groups_s_variant_letters_in_the_s_region():
    # Characters that are variants of "s" (long s with diagonal stroke,
    # s with oblique stroke) must sort next to the s-group, i.e. after the
    # preceding letter and before the following one, not appended at the end.
    result = extract_alphabet.extract_alphabet("trẜsꞩp")

    assert result.index("ẜ") > result.index("r")
    assert result.index("ꞩ") > result.index("r")
    assert result.index("ẜ") < result.index("t")
    assert result.index("ꞩ") < result.index("t")


def test_extract_alphabet_keeps_combining_mark_with_its_base_letter():
    # "hußlu\u0364ſch": the "u" carries a combining small letter e (e above u).
    # That combination is one letter of the alphabet and must be listed as such,
    # not reduced to a plain "u" and a stray combining mark.
    assert extract_alphabet.extract_alphabet("hußlu\u0364ſch\t20\n") == [
        "c",
        "h",
        "l",
        "ß",
        "ſ",
        "u",
        "u\u0364",
    ]


def test_extract_alphabet_sorts_combined_letter_next_to_its_base_letter():
    assert extract_alphabet.extract_alphabet("wu\u0364a") == ["a", "u\u0364", "w"]


def test_extract_alphabet_keeps_case_with_uppercase_before_lowercase():
    assert extract_alphabet.extract_alphabet("tTsS") == ["S", "s", "T", "t"]


def test_extract_alphabet_sorts_ligatures_next_to_their_first_base_letter():
    # "æ" is an a-like letter and "œ" an o-like letter; they must sort in the
    # a- and o-groups respectively, not get dumped after every plain letter.
    assert extract_alphabet.extract_alphabet("zaæbnoœ") == [
        "a",
        "æ",
        "b",
        "n",
        "o",
        "œ",
        "z",
    ]


def test_extract_alphabet_handles_combining_mark_on_non_dsb_base_letter():
    # A base letter outside the DSB alphabet (Cyrillic "ю") carrying a combining
    # mark must stay one letter and be sorted via its base ("YU" → y-group),
    # instead of crashing the name lookup with a multi-codepoint argument.
    assert extract_alphabet.extract_alphabet("az\u044e\u0301") == [
        "a",
        "\u044e\u0301",
        "z",
    ]


def test_main_without_output_writes_line_to_stdout(tmp_path, capsys):
    infile = tmp_path / "in.txt"
    infile.write_text(EXAMPLE_INPUT, encoding="utf8")

    extract_alphabet.main([str(infile)])

    assert capsys.readouterr().out == EXAMPLE_OUTPUT + "\n"


def test_main_with_output_writes_line_to_file(tmp_path):
    infile = tmp_path / "in.txt"
    infile.write_text(EXAMPLE_INPUT, encoding="utf8")
    outfile = tmp_path / "out.txt"

    extract_alphabet.main([str(infile), str(outfile)])

    assert outfile.read_text(encoding="utf8") == EXAMPLE_OUTPUT + "\n"


def test_main_both_cases_writes_one_line_per_letter_upper_then_lower(tmp_path, capsys):
    infile = tmp_path / "in.txt"
    infile.write_text("abcCDEFŻżĆś", encoding="utf8")

    extract_alphabet.main(["--both-cases", str(infile)])

    assert capsys.readouterr().out == (
        "A a\n" "B b\n" "C c\n" "Ć ć\n" "D d\n" "E e\n" "F f\n" "Ś ś\n" "Ż ż\n"
    )


def test_main_both_cases_keeps_combining_mark_in_both_cases(tmp_path, capsys):
    infile = tmp_path / "in.txt"
    infile.write_text("wu\u0364a", encoding="utf8")

    extract_alphabet.main(["--both-cases", str(infile)])

    assert capsys.readouterr().out == """A a
U\u0364 u\u0364
W w
"""


def test_main_lowercase_outputs_unique_lowercase_alphabet(tmp_path, capsys):
    infile = tmp_path / "in.txt"
    infile.write_text("AaaaaćdEęfgHklŁłńŻ", encoding="utf8")

    extract_alphabet.main(["--lowercase", str(infile)])

    assert capsys.readouterr().out == """a ć d e ę f g h k ł l ń ż
"""


def test_main_uppercase_outputs_unique_uppercase_alphabet(tmp_path, capsys):
    infile = tmp_path / "in.txt"
    infile.write_text("AaaaaćdEęfgHklŁłńŻ", encoding="utf8")

    extract_alphabet.main(["--uppercase", str(infile)])

    assert capsys.readouterr().out == """A Ć D E Ę F G H K Ł L Ń Ż
"""


def test_main_full_unicode_name_outputs_one_named_letter_per_line(tmp_path, capsys):
    infile = tmp_path / "in.txt"
    infile.write_text("ßba", encoding="utf8")

    extract_alphabet.main(["--full-unicode-name", str(infile)])

    assert capsys.readouterr().out == (
        "a LATIN SMALL LETTER A\n"
        "b LATIN SMALL LETTER B\n"
        "ß LATIN SMALL LETTER SHARP S\n"
    )


def test_main_only_latin_excludes_cyrillic_greek_and_bare_modifier_letters(
    tmp_path, capsys
):
    # Greek alpha, Cyrillic a and a bare modifier apostrophe are not Latin
    # letters and must be dropped; the Latin letters keep their order.
    infile = tmp_path / "in.txt"
    infile.write_text("a\u03b1\u0430\u02bbbcz", encoding="utf8")

    extract_alphabet.main(["--only-latin", str(infile)])

    assert capsys.readouterr().out == "a b c z\n"


def test_extract_alphabet_only_latin_keeps_letters_of_latin_orthographies():
    # ae ligature, l with stroke, eng, o with stroke and sharp s are letters of
    # real Latin-script alphabets, so they are kept and sorted with the base
    # letter they are derived from (eng belongs to the n-group).
    assert extract_alphabet.extract_alphabet(
        "\u00e6\u00df\u0142\u00f8\u014b", only_latin=True
    ) == ["\u00e6", "\u0142", "\u014b", "\u00f8", "\u00df"]


def test_extract_alphabet_only_latin_drops_phonetic_letters():
    # Small capital B, latin phi, latin gamma, esh, ezh, schwa and open o are
    # IPA/phonetic symbols, not letters of a Latin-based alphabet.
    assert extract_alphabet.extract_alphabet(
        "a\u0299b\u0278\u0263\u0283\u0292z\u0259\u0254", only_latin=True
    ) == ["a", "b", "z"]


def test_extract_alphabet_only_latin_drops_unlisted_ipa_extension_letter():
    # Turned a is in IPA Extensions but absent from the named phonetic markers.
    assert extract_alphabet.extract_alphabet("a\u0250z", only_latin=True) == [
        "a",
        "z",
    ]


def test_extract_alphabet_only_latin_drops_modifier_and_superscript_letters():
    # Modifier letter small h/j and superscript a/n are modifiers, not letters.
    assert extract_alphabet.extract_alphabet(
        "a\u1d43b\u02b0c\u02b2z\u207f", only_latin=True
    ) == ["a", "b", "c", "z"]


def test_extract_alphabet_only_latin_drops_phonetic_letter_with_combining_mark():
    # "ezh with combining acute" is a marked phonetic symbol and goes too.
    assert extract_alphabet.extract_alphabet("a\u0292\u0301z", only_latin=True) == [
        "a",
        "z",
    ]


def test_extract_alphabet_sorts_eng_and_eth_with_their_base_letter():
    # Their Unicode names ("ENG", "ETH") start with an E, but eng is an n-letter
    # and eth a d-letter; neither may end up in the e-group.
    assert extract_alphabet.extract_alphabet("aden o\u014b\u00f0") == [
        "a",
        "d",
        "\u00f0",
        "e",
        "n",
        "\u014b",
        "o",
    ]


def test_main_only_latin_keeps_combining_mark_on_latin_base_but_drops_cyrillic(
    tmp_path, capsys
):
    # "b" plus a combining stroke stays (Latin base); Cyrillic "yu" plus a
    # combining acute is dropped (non-Latin base).
    infile = tmp_path / "in.txt"
    infile.write_text("b\u0337a\u044e\u0301z", encoding="utf8")

    extract_alphabet.main(["--only-latin", str(infile)])

    assert capsys.readouterr().out == "a b\u0337 z\n"


def test_main_both_cases_with_output_writes_lines_to_file(tmp_path):
    infile = tmp_path / "in.txt"
    infile.write_text(
        """bA	a
""",
        encoding="utf8",
    )
    outfile = tmp_path / "out.txt"

    extract_alphabet.main(["--both-cases", str(infile), str(outfile)])

    assert outfile.read_text(encoding="utf8") == """A a
B b
"""


def test_main_without_arguments_reads_bagofwords_all(datadir, capsys):
    os.makedirs(os.path.join(datadir, "bagofwords"), exist_ok=True)
    with open(
        os.path.join(datadir, "bagofwords", "_all.txt"), "w", encoding="utf8"
    ) as outf:
        outf.write(EXAMPLE_INPUT)
    importlib.reload(extract_alphabet)

    extract_alphabet.main([])

    assert capsys.readouterr().out == EXAMPLE_OUTPUT + "\n"
