# Shared Lower Sorbian (dsb) collation helper.
#
# Newest Lower Sorbian alphabet (every letter is a single character;
# CH, DŹ and DŽ are NOT treated as separate letters anymore):
#   a b c č ć d e ě f g h i j k ł l m n ń o ó p r ŕ s š ś t u v w x y z ž ź

_ORDER = {
    "A": 1,
    "B": 2,
    "C": 3,
    "Č": 4,
    "Ć": 5,
    "D": 6,
    "E": 7,
    "Ě": 8,
    "F": 9,
    "G": 10,
    "H": 11,
    "I": 12,
    "J": 13,
    "K": 14,
    "Ł": 15,
    "L": 16,
    "M": 17,
    "N": 18,
    "Ń": 19,
    "O": 20,
    "Ó": 21,
    "P": 22,
    "R": 23,
    "Ŕ": 24,
    "S": 25,
    "Š": 26,
    "Ś": 27,
    "T": 28,
    "U": 29,
    "V": 30,
    "W": 31,
    "X": 32,
    "Y": 33,
    "Z": 34,
    "Ž": 35,
    "Ź": 36,
}


def dsb_sortkey(s):
    """Return a fixed-width digit key whose binary (strcmp) order equals dsb order."""
    s = s.upper()
    key = []
    for ch in s:
        weight = _ORDER.get(ch)
        if weight is not None:
            # Known letters get a fixed 2-digit weight (01..36), first digit 0-3.
            key.append("%02d" % weight)
        else:
            # Unknown characters sort after every known letter (first digit 9),
            # ordered among themselves by Unicode codepoint.
            key.append("99" + "%08d" % ord(ch))
    # Fixed-width keys mean a shorter string is a strict prefix of a longer one,
    # so a byte comparison sorts shorter (end-of-word) entries before extensions.
    return "".join(key)
