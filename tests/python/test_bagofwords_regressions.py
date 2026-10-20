"""Regression tests for the defects listed in docs/bagofwords-py-review.md.

Each test in this module documents intended behaviour and guards against
reintroducing previously identified bugs.
"""

import os
import sqlite3

import bagofwords
import pytest


def read_tsv(path):
    with open(path, encoding="utf8") as inf:
        return [line.rstrip("\n").split("\t") for line in inf if line.strip()]


def read_lines(path):
    with open(path, encoding="utf8") as inf:
        return [line.rstrip("\n") for line in inf if line.strip()]


def set_remote_document(monkeypatch, year, response):
    monkeypatch.setattr(
        bagofwords,
        "getdoclist",
        lambda ns: "urn:cts:dsb:doc1	Doc One	" + year,
    )
    monkeypatch.setattr(bagofwords, "cts_bagofwords", lambda urn: response)


def test_collect_document_limit_stops_remote_requests(datadir, monkeypatch):
    doclist = "\n".join(
        [
            "urn:cts:dsb:doc1	Doc One	1800",
            "urn:cts:dsb:doc2	Doc Two	1801",
            "urn:cts:dsb:doc3	Doc Three	1802",
        ]
    )
    requested_urns = []
    monkeypatch.setattr(bagofwords, "count", 2)
    monkeypatch.setattr(bagofwords, "getdoclist", lambda ns: doclist)
    monkeypatch.setattr(
        bagofwords,
        "cts_bagofwords",
        lambda urn: requested_urns.append(urn) or "word	1",
    )

    bagofwords.collect()

    assert requested_urns == ["urn:cts:dsb:doc1", "urn:cts:dsb:doc2"]
    assert sorted(os.listdir(datadir + "bagofwordsperyear")) == [
        "1800.txt",
        "1801.txt",
    ]


# ------------------------------------------------- 1a/1b: Unicode lowercasing


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


def test_process_case_variants_do_not_inflate_type_counts(tmp_path, write_peryear):
    base = write_peryear(
        str(tmp_path / "bagofwords"),
        {1800: {"Żož": 21, "żož": 184}},
    )
    bagofwords.process(base)

    assert read_tsv(base + "/_typesumperyear.txt") == [["1800", "1"]]
    assert read_tsv(base + "/_typetokenratioperyear.txt") == [["1800", str(1 / 205)]]


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


def test_all_txt_contains_only_lowercase_tokens(tmp_path, write_peryear):
    # TODO: define lowercasing, write all cases here in test
    base = write_peryear(
        str(tmp_path / "bagofwords"),
        {1800: {"Źeden": 3, "K’žiſcham": 2, "ńejźij": 1}},
    )
    bagofwords.process(base)

    tokens = [row[0] for row in read_tsv(base + "/_all.txt")]
    assert tokens == [token.lower() for token in tokens]


# ------------------------------------------ Remote collection validation


def test_collect_traversal_year_rejected_without_external_file(datadir, monkeypatch):
    year = "../../escaped"
    collection_dir = datadir + "corpus/"
    os.mkdir(collection_dir)
    monkeypatch.setattr(bagofwords, "datadir", collection_dir)
    escaped_path = os.path.abspath(
        collection_dir + "bagofwordsperyear/" + year + ".txt"
    )
    set_remote_document(monkeypatch, year, "word	1")

    bagofwords.collect()

    assert os.path.commonpath([collection_dir, escaped_path]) != os.path.commonpath(
        [collection_dir]
    )
    assert not os.path.exists(escaped_path)
    assert not os.path.exists(collection_dir + "bagofwords/urn_#_cts_#_dsb_#_doc1.txt")


def test_collect_non_numeric_year_rejected_without_document_data(datadir, monkeypatch):
    set_remote_document(monkeypatch, "unknown", "word	1")

    bagofwords.collect()

    assert os.listdir(datadir + "bagofwordsperyear") == []
    assert not os.path.exists(datadir + "bagofwords/urn_#_cts_#_dsb_#_doc1.txt")


@pytest.mark.parametrize("frequency", ["not-a-number", "-1"])
def test_collect_invalid_frequency_rejected_without_document_data(
    datadir, monkeypatch, frequency
):
    set_remote_document(monkeypatch, "1800", "word	" + frequency)

    bagofwords.collect()

    assert os.listdir(datadir + "bagofwordsperyear") == []
    assert not os.path.exists(datadir + "bagofwords/urn_#_cts_#_dsb_#_doc1.txt")


def test_main_empty_response_does_not_insert_document(datadir, monkeypatch):
    set_remote_document(monkeypatch, "1800", "")

    bagofwords.main([])

    con = sqlite3.connect(datadir + "bagofwords.db")
    rows = con.execute("SELECT urn, wordbag FROM urndatewordbag").fetchall()
    con.close()
    assert rows == []


def test_main_unicode_token_uses_canonical_case_in_all_tables(datadir, monkeypatch):
    set_remote_document(monkeypatch, "1800", "Żož	1")

    bagofwords.main([])

    con = sqlite3.connect(datadir + "bagofwords.db")
    token_rows = con.execute("SELECT token FROM tokencount").fetchall()
    wordbag_rows = con.execute("SELECT wordbag FROM urndatewordbag").fetchall()
    con.close()
    assert token_rows == [("żož",)]
    assert wordbag_rows == [("|żož|",)]


# ---------------------------------------------------- 2a: SQL string building


def make_corpus(datadir, monkeypatch, tokens, urn_tokens=None):
    """Write a minimal collect()-shaped corpus using the given tokens."""
    os.makedirs(datadir + "bagofwords", exist_ok=True)
    os.makedirs(datadir + "bagofwordsperyear", exist_ok=True)

    with open(datadir + "bagofwords/_all.txt", "w", encoding="utf8") as outf:
        for token, freq in tokens.items():
            print(token, freq, sep="	", file=outf)
    with open(datadir + "bagofwordsperyear/1800.txt", "w", encoding="utf8") as outf:
        for token, freq in tokens.items():
            print(token, freq, sep="	", file=outf)
    with open(
        datadir + "bagofwords/urn_#_cts_#_dsb_#_doc1.txt", "w", encoding="utf8"
    ) as outf:
        for token, freq in (urn_tokens or tokens).items():
            print(token, freq, sep="	", file=outf)

    monkeypatch.setattr(
        bagofwords, "getdoclist", lambda ns: "urn:cts:dsb:doc1	Doc One	1800"
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


def test_db_stores_wordbag_containing_double_quote(datadir, monkeypatch):
    make_corpus(datadir, monkeypatch, {"woda": 1}, urn_tokens={'k’"nam': 1})
    bagofwords.db()

    con = sqlite3.connect(datadir + "bagofwords.db")
    assert con.execute("SELECT urn, wordbag FROM urndatewordbag").fetchall() == [
        ("urn:cts:dsb:doc1", '|k’"nam|')
    ]
    con.close()
