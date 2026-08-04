"""Regression tests for known, unfixed bugs in etl/lemmatisierowasch.py.

Each test asserts the CORRECT behaviour and is marked xfail(strict=True): it
passes today because the bug reproduces, and will fail loudly (XPASS) the moment
the bug is fixed, forcing the marker to be removed.
"""

import os
import sqlite3

import bagofwords
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


# --------------------------------------------------------- BUG-3: document sets


# A partial harvest selects a fixed inventory cohort. Missing lemma annotations
# must not silently substitute a later document from a different year or corpus
# segment. TODO: decide whether to record explicit per-document outcomes (empty,
# unauthorized, invalid response, etc.) in a harvest manifest.
@pytest.mark.xfail(
    strict=True,
    reason="BUG: 'No Items' restores count so a partial lemma harvest silently "
    "substitutes a later document",
)
def test_partial_harvest_does_not_replace_unannotated_document(datadir, monkeypatch):
    doclist = "\n".join(
        [
            "urn:cts:dsb:doc1	Unannotated	1880",
            "urn:cts:dsb:doc2	Annotated	1881",
        ]
    )
    monkeypatch.setattr(bagofwords, "count", 1)
    monkeypatch.setattr(bagofwords, "getdoclist", lambda ns: doclist)
    monkeypatch.setattr(bagofwords, "cts_bagofwords", lambda urn: "word	1")

    bagofwords.collect()

    monkeypatch.setattr(lemmatisierowasch, "datadir", datadir)
    monkeypatch.setattr(lemmatisierowasch, "count", 1)
    monkeypatch.setattr(lemmatisierowasch, "getdoclist", lambda ns: doclist)
    monkeypatch.setattr(
        lemmatisierowasch,
        "lemmamapping",
        lambda urn: (
            ""
            if urn.endswith("doc1")
            else """tok	|X|
"""
        ),
    )

    lemmatisierowasch.collect()

    def urn_files(folder):
        return sorted(
            name for name in os.listdir(datadir + folder) if name.startswith("urn_#_")
        )

    assert urn_files("bagofwords") == ["urn_#_cts_#_dsb_#_doc1.txt"]
    assert urn_files("lemmamapping") == []


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


# ---------------------------------------------------- BUG-5: attribute leakage


@pytest.mark.xfail(
    strict=True,
    reason="BUG: attributes from a following <note> element leak onto the word, "
    "and type= matches inside subtype=",
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

    assert result == """jo	|JO|		
"""


# ------------------------------------------------------- BUG-6: empty lemmas


@pytest.mark.xfail(
    strict=True,
    reason='BUG: an empty lemma="" is stored as the || mapping instead of '
    "being skipped",
)
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


@pytest.mark.xfail(
    strict=True,
    reason="BUG: pipe-splitting counts the empty boundary components, producing "
    "an inflated || (empty) lemmanonambig row",
)
def test_db_valid_lemma_creates_no_empty_nonambiguous_row(tmp_path, monkeypatch):
    datadir = str(tmp_path) + os.sep
    monkeypatch.setattr(lemmatisierowasch, "datadir", datadir)
    monkeypatch.setattr(lemmatisierowasch, "tokenlength", 80)
    monkeypatch.setattr(
        lemmatisierowasch, "getdoclist", lambda ns: "urn:cts:dsb:doc1	Title	1880"
    )
    os.makedirs(datadir + "lemmamappingperyear")
    with open(datadir + "lemmamappingperyear/1880.txt", "w", encoding="utf8") as f:
        f.write("""dṙewo	|DRJEWO|			3
""")
    os.makedirs(datadir + "lemmamapping")
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


# ----------------------------------------------- BUG-2: failed rebuild data loss


@pytest.mark.xfail(
    strict=True,
    reason="BUG: db() runs initTables() first, so a malformed per-year row "
    "destroys the previous database instead of preserving it",
)
def test_db_failed_rebuild_preserves_existing_database(tmp_path, monkeypatch):
    datadir = str(tmp_path) + os.sep
    monkeypatch.setattr(lemmatisierowasch, "datadir", datadir)
    monkeypatch.setattr(lemmatisierowasch, "tokenlength", 80)
    monkeypatch.setattr(
        lemmatisierowasch, "getdoclist", lambda ns: "urn:cts:dsb:doc1	Title	1880"
    )

    con = sqlite3.connect(datadir + "lemmamapping.db")
    con.execute("CREATE TABLE marker(val TEXT)")
    con.execute("INSERT INTO marker VALUES ('keep-me')")
    con.commit()
    con.close()

    os.makedirs(datadir + "lemmamappingperyear")
    with open(datadir + "lemmamappingperyear/1880.txt", "w", encoding="utf8") as f:
        f.write("""brokenrow
""")
    os.makedirs(datadir + "lemmamapping")

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
