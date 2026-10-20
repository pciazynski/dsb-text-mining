"""Regression tests for known, unfixed bugs in etl/lemmatisierowasch.py.

Each test asserts the CORRECT behaviour and is marked xfail(strict=True): it
passes today because the bug reproduces, and will fail loudly (XPASS) the moment
the bug is fixed, forcing the marker to be removed.
"""

import os
import sqlite3

import lemmatisierowasch
import pytest


@pytest.fixture(autouse=True)
def reset_module_globals():
    lemmatisierowasch.bagofwords.clear()
    lemmatisierowasch.lemmabag.clear()
    lemmatisierowasch.ctsurl = ""
    yield
    lemmatisierowasch.bagofwords.clear()
    lemmatisierowasch.lemmabag.clear()
    lemmatisierowasch.ctsurl = ""


def setup_remote_passage(tmp_path, monkeypatch, reset_cts_globals, payload):
    monkeypatch.setattr(lemmatisierowasch, "datadir", str(tmp_path) + os.sep)
    monkeypatch.setattr(lemmatisierowasch, "ctsurl", "https://cts.example/")
    reset_cts_globals.manualurl = "https://cts.example/"
    monkeypatch.setattr(
        reset_cts_globals, "urlopen", lambda url, timeout: [payload.encode("utf8")]
    )


def setup_db_env(tmp_path, monkeypatch, doclist="urn:cts:dsb:doc1\tTitle\t1880"):
    datadir = str(tmp_path) + os.sep
    monkeypatch.setattr(lemmatisierowasch, "datadir", datadir)
    monkeypatch.setattr(lemmatisierowasch, "tokenlength", 80)
    monkeypatch.setattr(lemmatisierowasch, "getdoclist", lambda ns: doclist)
    os.makedirs(datadir + "lemmamappingperyear")
    os.makedirs(datadir + "lemmamapping")
    return datadir


def write_rows(path, columns):
    with open(path, "w", encoding="utf8") as outf:
        for row in columns:
            outf.write("\t".join(row) + "\n")


def test_lemmamapping_keeps_type_empty_when_only_subtype_is_present(
    tmp_path, monkeypatch, reset_cts_globals
):
    setup_remote_passage(
        tmp_path,
        monkeypatch,
        reset_cts_globals,
        '<text><w lemma="75" subtype="number">75</w></text>',
    )
    lemmatisierowasch.bagofwords["75"] = 1

    result = lemmatisierowasch.lemmamapping("urn:cts:dsb:work")

    assert result.splitlines() == ["75\t|75|\t\tnumber"]


# bagofwords.php serves counts for restricted documents, passage.php does not:
# it answers with a plain-text error body that holds no <w> elements, so those
# documents yield an empty mapping. That is a normal outcome for part of the
# corpus and must not end the run - every document of the requested batch has to
# be tried once. TODO: record the per-document outcome (mapped, unavailable,
# invalid response) in a manifest next to _lemmabag.txt so partial runs stay
# auditable.
def test_collect_continues_after_unavailable_document(datadir, monkeypatch):
    doclist = "\n".join(
        [
            "urn:cts:dsb:doc1	Restricted	1880",
            "urn:cts:dsb:doc2	Open	1881",
            "urn:cts:dsb:doc3	Open	1882",
        ]
    )
    monkeypatch.setattr(lemmatisierowasch, "datadir", datadir)
    monkeypatch.setattr(lemmatisierowasch, "count", 3)
    monkeypatch.setattr(lemmatisierowasch, "ctsurl", "https://cts.example/")
    monkeypatch.setattr(lemmatisierowasch, "getdoclist", lambda ns: doclist)
    lemmatisierowasch.bagofwords["jo"] = 1

    def fake_cts_passage(urn, params):
        if urn.endswith("doc1"):
            return "Error code 7: Unauthorized Access"
        return '<text><w lemma="JO">jo</w></text>'

    monkeypatch.setattr(lemmatisierowasch, "cts_passage", fake_cts_passage)

    lemmatisierowasch.collect()

    mapped = sorted(
        name
        for name in os.listdir(datadir + "lemmamapping")
        if name.startswith("urn_#_")
    )

    assert mapped == ["urn_#_cts_#_dsb_#_doc2.txt", "urn_#_cts_#_dsb_#_doc3.txt"]


# ------------------------------------------------------ BUG-4: tokenization


# TODO: Decide whether to reproduce and version the production tokenizer or
# derive frequencies and annotations from one parsed passage stream. Until then,
# do not invent a one-token mapping for a <w> that the bag-of-words endpoint
# tokenizes differently; exclude it and retain an auditable error record.
def test_lemmamapping_excludes_comma_number_with_mismatched_tokenization(
    tmp_path, monkeypatch, reset_cts_globals
):
    setup_remote_passage(
        tmp_path, monkeypatch, reset_cts_globals, '<text><w lemma="STO">1,00</w></text>'
    )
    lemmatisierowasch.bagofwords["100"] = 1

    result = lemmatisierowasch.lemmamapping("urn:cts:dsb:work")

    assert result == ""
    assert (tmp_path / "_ERROR.txt").read_text(encoding="utf8") == (
        "urn:cts:dsb:work lemmatisierowasch unknown token 1,00\n"
    )


def test_lemmamapping_ignores_attributes_of_following_element(
    tmp_path, monkeypatch, reset_cts_globals
):
    payload = (
        '<text><w lemma="JO">jo</w>'
        '<note subtype="description" type="encoders-comment">x</note></text>'
    )
    setup_remote_passage(tmp_path, monkeypatch, reset_cts_globals, payload)
    lemmatisierowasch.bagofwords["jo"] = 1

    result = lemmatisierowasch.lemmamapping("urn:cts:dsb:work")

    expected = tmp_path / "expected.tsv"
    write_rows(expected, [["jo", "|JO|", "", ""]])

    assert result == expected.read_text(encoding="utf8")


def test_lemmamapping_empty_lemma_creates_no_mapping(
    tmp_path, monkeypatch, reset_cts_globals
):
    setup_remote_passage(
        tmp_path, monkeypatch, reset_cts_globals, '<text><w lemma="">jo</w></text>'
    )
    lemmatisierowasch.bagofwords["jo"] = 1

    result = lemmatisierowasch.lemmamapping("urn:cts:dsb:work")

    assert result == ""
    assert lemmatisierowasch.lemmabag == {}


def test_db_valid_lemma_creates_no_empty_nonambiguous_row(tmp_path, monkeypatch):
    datadir = setup_db_env(tmp_path, monkeypatch)
    with open(datadir + "lemmamappingperyear/1880.txt", "w", encoding="utf8") as f:
        f.write("""dṙewo	|DRJEWO|			3
""")
    with open(datadir + "lemmamapping/_lemmabag.txt", "w", encoding="utf8") as f:
        f.write("""|DRJEWO|	3
""")
    with open(
        datadir + "lemmamapping/urn_#_cts_#_dsb_#_doc1.txt", "w", encoding="utf8"
    ) as f:
        f.write("""dṙewo	|DRJEWO|			3
""")

    lemmatisierowasch.db()

    con = sqlite3.connect(datadir + "lemmamapping.db")
    empty_rows = con.execute(
        "SELECT frequency FROM lemmanonambig WHERE lemma='||'"
    ).fetchall()
    con.close()
    assert empty_rows == []


def test_db_failed_rebuild_preserves_existing_database(tmp_path, monkeypatch):
    datadir = setup_db_env(tmp_path, monkeypatch)

    con = sqlite3.connect(datadir + "lemmamapping.db")
    con.execute("CREATE TABLE marker(val TEXT)")
    con.execute("INSERT INTO marker VALUES ('keep-me')")
    con.commit()
    con.close()

    with open(datadir + "lemmamappingperyear/1880.txt", "w", encoding="utf8") as f:
        f.write("""brokenrow
""")

    try:
        lemmatisierowasch.db()
    except Exception:
        pass

    con = sqlite3.connect(datadir + "lemmamapping.db")
    has_marker = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='marker'"
    ).fetchall()
    rows = con.execute("SELECT val FROM marker").fetchall() if has_marker else []
    con.close()
    assert rows == [("keep-me",)]
