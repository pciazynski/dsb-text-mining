import os
import string
import sys
import unicodedata

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "etl"))

from dsb_collation import DSB_ALPHABET
from settings import datadir


def _letter_order():
    """DSB alphabet with the Latin letters it omits (e.g. Q) at their alphabetical spot."""
    missing = sorted(set(string.ascii_uppercase) - set(DSB_ALPHABET))
    order = []
    for letter in DSB_ALPHABET:
        while missing and letter in string.ascii_uppercase and missing[0] < letter:
            order.append(missing.pop(0))
        order.append(letter)
    return order + missing


_ORDER = {letter: weight for weight, letter in enumerate(_letter_order())}


# Letter names that do not start with the letter they belong to.
_NAMED_BASE_LETTERS = {"ENG": "N", "ETH": "D"}


def _name_based_base_letter(character):
    """Plain letter `character` sorts with, derived from its Unicode name."""
    name = unicodedata.name(character, "")

    for marker in ("LETTER ", "LIGATURE "):
        if marker not in name:
            continue

        # "... LETTER S WITH ..." / "... LIGATURE OE" → base token, then first char
        # so multi-letter bases (AE, OE) sort with their first plain letter.
        base_name = name.split(marker, 1)[1].split(" WITH ", 1)[0]
        for token in reversed(base_name.split()):
            if token.isalpha():
                return _NAMED_BASE_LETTERS.get(token, token[0])
        return None

    return None


def _base_letter(character):
    """Plain letter `character` sorts with, by decomposition or by its Unicode name."""
    for base_character in unicodedata.normalize("NFKD", character).casefold():
        if base_character.isalpha() and base_character.upper() in _ORDER:
            return base_character.upper()

    return _name_based_base_letter(character)


def _sort_key(letter):
    """Sort key for one letter: its base character plus any combining marks."""
    codepoints = tuple(ord(character) for character in letter)
    weight = _ORDER.get(_base_letter(letter[0]))
    if weight is not None:
        return (0, weight, codepoints)
    return (1, codepoints)


# Name fragments of phonetic symbols that are not letters of a Latin alphabet.
_PHONETIC_MARKERS = ("SMALL CAPITAL", "PHI", "GAMMA", "ESH", "EZH", "SCHWA", "OPEN O")


def _is_latin_letter(letter):
    """Return True for Latin letters, including Latin-derived letters and marks."""
    for character in letter:
        if unicodedata.combining(character):
            continue
        if not character.isalpha():
            return False

        name = unicodedata.name(character, "")
        # Lm covers modifier and superscript letters.
        if unicodedata.category(character) == "Lm":
            return False
        if any(marker in name for marker in _PHONETIC_MARKERS):
            return False
        # IPA Extensions / Spacing Modifier Letters and Phonetic Extensions blocks.
        if 0x0250 <= ord(character) <= 0x02FF or 0x1D00 <= ord(character) <= 0x1D7F:
            return False
        if "LATIN" not in name:
            return False
    return True


def _iter_letters(text):
    """Yield each letter of `text`, keeping combining marks on their base letter."""
    current_letter = ""

    for character in text:
        if current_letter and unicodedata.combining(character):
            current_letter += character
            continue
        if current_letter:
            yield current_letter
        current_letter = character if character.isalpha() else ""

    if current_letter:
        yield current_letter


def extract_alphabet(text, only_latin=False):
    letters = sorted(set(_iter_letters(text)), key=_sort_key)
    if only_latin:
        return [letter for letter in letters if _is_latin_letter(letter)]
    return letters


def _both_cases_lines(letters):
    """One 'Upper lower' line per case-insensitive letter, in alphabet order."""
    seen = {}
    for letter in letters:
        key = letter.casefold()
        if key not in seen or _sort_key(letter) < _sort_key(seen[key]):
            seen[key] = letter
    ordered = sorted(seen.values(), key=_sort_key)
    return [f"{letter.upper()} {letter.lower()}" for letter in ordered]


def _format_output(letters, both_cases=False, full_unicode_name=False):
    if both_cases:
        lines = _both_cases_lines(letters)
    elif full_unicode_name:
        lines = [
            f"{letter} {' '.join(unicodedata.name(character) for character in letter)}"
            for letter in letters
        ]
    else:
        return " ".join(letters) + "\n"

    return "\n".join(lines) + "\n"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    both_cases = False
    full_unicode_name = False
    only_latin = False
    lowercase = False
    uppercase = False
    paths = []
    for arg in argv:
        if arg == "--both-cases":
            both_cases = True
        elif arg == "--full-unicode-name":
            full_unicode_name = True
        elif arg == "--only-latin":
            only_latin = True
        elif arg == "--lowercase":
            lowercase = True
        elif arg == "--uppercase":
            uppercase = True
        else:
            paths.append(arg)

    if len(paths) > 2:
        raise SystemExit(
            "usage: extract_alphabet.py [--both-cases] [--full-unicode-name] [--only-latin] [--lowercase] [--uppercase] [input [output]]"
        )

    input_path = paths[0] if paths else os.path.join(datadir, "bagofwords", "_all.txt")
    output_path = paths[1] if len(paths) == 2 else None

    with open(input_path, "r", encoding="utf8") as inf:
        letters = extract_alphabet(inf.read(), only_latin=only_latin)

    if lowercase:
        letters = sorted({letter.lower() for letter in letters}, key=_sort_key)
    elif uppercase:
        letters = sorted({letter.upper() for letter in letters}, key=_sort_key)

    output = _format_output(
        letters, both_cases=both_cases, full_unicode_name=full_unicode_name
    )

    if output_path is None:
        sys.stdout.write(output)
    else:
        with open(output_path, "w", encoding="utf8") as outf:
            outf.write(output)


if __name__ == "__main__":
    main()
