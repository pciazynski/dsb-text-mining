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


# JUDGMENT CALL: asserts the two stages cover an identical document set. This is
# only clearly wrong on a partial harvest (count>0), where "No Items" restoration
# makes the lemma stage reach deeper into the doclist than the bag stage. On a full
# run (count=-1) unannotated docs are legitimately bagged but not lemmatized, so
# some divergence is by design. Whether partial harvests must stay aligned is a
# stakeholder decision; strict set-equality may be stronger than intent supports.
@pytest.mark.xfail(
    strict=True,
    reason="BUG: 'No Items' restores count so lemmatisierowasch lemmatizes a "
    "different document set than bagofwords bags",
)
def test_both_stages_select_the_same_documents(datadir, monkeypatch):
    doclist = "\n".join(
        [
            "urn:cts:dsb:doc1\tUnannotated\t1880",
            "urn:cts:dsb:doc2\tAnnotated\t1881",
        ]
    )
    monkeypatch.setattr(bagofwords, "count", 1)
    monkeypatch.setattr(bagofwords, "getdoclist", lambda ns: doclist)
    monkeypatch.setattr(bagofwords, "cts_bagofwords", lambda urn: "word\t1")

    bagofwords.collect()

    monkeypatch.setattr(lemmatisierowasch, "datadir", datadir)
    monkeypatch.setattr(lemmatisierowasch, "count", 1)
    monkeypatch.setattr(lemmatisierowasch, "getdoclist", lambda ns: doclist)
    monkeypatch.setattr(
        lemmatisierowasch,
        "lemmamapping",
        lambda urn: "" if urn.endswith("doc1") else "tok\t|X|\t\t\n",
    )

    lemmatisierowasch.collect()

    def urn_files(folder):
        return sorted(
            name for name in os.listdir(datadir + folder) if name.startswith("urn_#_")
        )

    assert urn_files("bagofwords") == urn_files("lemmamapping")


# ------------------------------------------------------ BUG-4: tokenization


# JUDGMENT CALL: only the principle is safe -- the passage and bag-of-words
# tokenizers must agree or valid annotations are silently dropped. HOW they should
# agree (strip ','? 1,00 -> 100 vs 1 00 vs 1,00) is a linguist/normalization
# decision and depends on the server's unversioned $replacearr. This test picks
# one plausible resolution.
@pytest.mark.xfail(
    strict=True,
    reason="BUG: passage token normalization (keeps ',') differs from the "
    "bag-of-words contract, so annotations for numbers like 1,00 are discarded",
)
def test_lemmamapping_keeps_annotation_for_comma_number(
    tmp_path, monkeypatch, reset_cts_globals
):
    setup_remote_passage(
        tmp_path, monkeypatch, reset_cts_globals, '<text><w lemma="STO">1,00</w></text>'
    )
    lemmatisierowasch.bagofwords["100"] = 1

    result = lemmatisierowasch.lemmamapping("urn:cts:dsb:work")

    assert result != ""
    assert not (tmp_path / "_ERROR.txt").exists()


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

    assert result == "jo\t|JO|\t\t\n"


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
        lemmatisierowasch, "getdoclist", lambda ns: "urn:cts:dsb:doc1\tTitle\t1880"
    )
    os.makedirs(datadir + "lemmamappingperyear")
    with open(datadir + "lemmamappingperyear/1880.txt", "w", encoding="utf8") as f:
        f.write("dṙewo\t|DRJEWO|\t\t\t3\n")
    os.makedirs(datadir + "lemmamapping")
    with open(datadir + "lemmamapping/_lemmabag.txt", "w", encoding="utf8") as f:
        f.write("|DRJEWO|\t3\n")
    with open(
        datadir + "lemmamapping/urn_#_cts_#_dsb_#_doc1.txt", "w", encoding="utf8"
    ) as f:
        f.write("dṙewo\t|DRJEWO|\t\t\t3\n")

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
        lemmatisierowasch, "getdoclist", lambda ns: "urn:cts:dsb:doc1\tTitle\t1880"
    )

    con = sqlite3.connect(datadir + "lemmamapping.db")
    con.execute("CREATE TABLE marker(val TEXT)")
    con.execute("INSERT INTO marker VALUES ('keep-me')")
    con.commit()
    con.close()

    os.makedirs(datadir + "lemmamappingperyear")
    with open(datadir + "lemmamappingperyear/1880.txt", "w", encoding="utf8") as f:
        f.write("brokenrow\n")
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
