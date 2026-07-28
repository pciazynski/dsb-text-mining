"""Regression tests for the defects listed in docs/bagofwords-py-review.md.

Every test in this module describes the *intended* behaviour and is marked
xfail(strict=True): it will start failing loudly as soon as the underlying bug
is fixed, which is the signal to drop the marker.
"""

import os
import sqlite3

import pytest

import bagofwords


def read_tsv(path):
    with open(path, encoding="utf8") as inf:
        return [line.rstrip("\n").split("\t") for line in inf if line.strip()]


def read_lines(path):
    with open(path, encoding="utf8") as inf:
        return [line.rstrip("\n") for line in inf if line.strip()]


# ------------------------------------------------- 1a/1b: Unicode lowercasing


@pytest.mark.xfail(
    strict=True,
    reason="review 1a: tokens are stored verbatim, so server-side ASCII-only "
    "lowercasing leaves non-ASCII capitals as separate types",
)
def test_process_merges_non_ascii_case_variants(tmp_path, write_peryear):
    """ "Żož" and "żož" are one type; Python's .lower() must fold them."""
    base = write_peryear(
        str(tmp_path / "bagofwords"),
        {
            1800: {"Żož": 21, "ṅejo": 100},
            1850: {"żož": 184, "Ṅejo": 3},
        },
    )
    bagofwords.process(base)

    assert read_tsv(base + "/_all.txt") == [
        ["żož", "205"],
        ["ṅejo", "103"],
    ]


@pytest.mark.xfail(
    strict=True,
    reason="review 1a: case collisions inflate the type count and corrupt the "
    "type/token ratio",
)
def test_process_case_variants_do_not_inflate_type_counts(tmp_path, write_peryear):
    base = write_peryear(
        str(tmp_path / "bagofwords"),
        {1800: {"Żož": 21, "żož": 184}},
    )
    bagofwords.process(base)

    assert read_tsv(base + "/_typesumperyear.txt") == [["1800", "1"]]
    assert read_tsv(base + "/_typetokenratioperyear.txt") == [["1800", str(1 / 205)]]


@pytest.mark.xfail(
    strict=True,
    reason="review 1a: a sentence-initial capitalised form gets its own, wrong, "
    "first/last attestation range in _minmaxyearzipf.txt",
)
def test_process_case_variants_share_one_attestation_range(tmp_path, write_peryear):
    base = write_peryear(
        str(tmp_path / "bagofwords"),
        {
            1800: {"Żož": 1},
            1850: {"żož": 2},
        },
    )
    bagofwords.process(base)

    assert read_tsv(base + "/_minmaxyearzipf.txt") == [["żož", "1800", "1850", "3"]]


@pytest.mark.xfail(
    strict=True,
    reason="review 1b: _all.txt is the whitelist for normierowasch/"
    "lemmatisierowasch, which tokenise with Python .lower()",
)
def test_all_txt_contains_only_lowercase_tokens(tmp_path, write_peryear):
    # TODO: define lowercasing, write all cases here in test
    base = write_peryear(
        str(tmp_path / "bagofwords"),
        {1800: {"Źeden": 3, "K’žiſcham": 2, "ńejźij": 1}},
    )
    bagofwords.process(base)

    tokens = [row[0] for row in read_tsv(base + "/_all.txt")]
    assert tokens == [token.lower() for token in tokens]


# ---------------------------------------------------- 2a: SQL string building


def make_corpus(datadir, monkeypatch, tokens, urn_tokens=None):
    """Write a minimal collect()-shaped corpus using the given tokens."""
    os.makedirs(datadir + "bagofwords", exist_ok=True)
    os.makedirs(datadir + "bagofwordsperyear", exist_ok=True)

    with open(datadir + "bagofwords/_all.txt", "w", encoding="utf8") as outf:
        for token, freq in tokens.items():
            outf.write(token + "\t" + str(freq) + "\n")
    with open(datadir + "bagofwordsperyear/1800.txt", "w", encoding="utf8") as outf:
        for token, freq in tokens.items():
            outf.write(token + "\t" + str(freq) + "\n")
    with open(
        datadir + "bagofwords/urn_#_cts_#_dsb_#_doc1.txt", "w", encoding="utf8"
    ) as outf:
        for token, freq in (urn_tokens or tokens).items():
            outf.write(token + "\t" + str(freq) + "\n")

    monkeypatch.setattr(
        bagofwords, "getdoclist", lambda ns: "urn:cts:dsb:doc1\tDoc One\t1800"
    )


@pytest.mark.xfail(
    strict=True,
    reason="review 2a: db() interpolates tokens into double-quoted SQL literals "
    "instead of binding parameters",
)
def test_db_stores_token_containing_double_quote(datadir, monkeypatch):
    make_corpus(datadir, monkeypatch, {'ſ"tym': 4})
    bagofwords.db()

    con = sqlite3.connect(datadir + "bagofwords.db")
    assert con.execute("SELECT token, frequency FROM tokencount").fetchall() == [
        ('ſ"tym', 4)
    ]
    assert con.execute("SELECT token, frequency FROM tokendatecount").fetchall() == [
        ('ſ"tym', 4)
    ]
    con.close()


@pytest.mark.xfail(
    strict=True,
    reason="review 2a: a token closing the SQL literal is executed as SQL "
    "rather than stored as data",
)
def test_db_does_not_execute_sql_injected_via_token(datadir, monkeypatch):
    payload = 'evil",0,"");DROP TABLE tokencount;--'
    make_corpus(datadir, monkeypatch, {payload: 1})
    bagofwords.db()

    con = sqlite3.connect(datadir + "bagofwords.db")
    tables = {
        row[0]
        for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert "tokencount" in tables
    assert con.execute("SELECT token FROM tokencount").fetchall() == [(payload,)]
    con.close()


@pytest.mark.xfail(
    strict=True,
    reason="review 2a: the wordbag column is built by the same concatenation",
)
def test_db_stores_wordbag_containing_double_quote(datadir, monkeypatch):
    make_corpus(datadir, monkeypatch, {"woda": 1}, urn_tokens={'k’"nam': 1})
    bagofwords.db()

    con = sqlite3.connect(datadir + "bagofwords.db")
    assert con.execute("SELECT urn, wordbag FROM urndatewordbag").fetchall() == [
        ("urn:cts:dsb:doc1", '|k’"nam|')
    ]
    con.close()
