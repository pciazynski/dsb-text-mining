"""Regression tests for the defects in normierowasch.py.

Each test asserts the CORRECT / desired behaviour for a previously reported bug.
"""

import os
import sqlite3

import pytest
import normierowasch


def setup_function():
    normierowasch.bagofwords.clear()
    normierowasch.normbag.clear()


def teardown_function():
    normierowasch.bagofwords.clear()
    normierowasch.normbag.clear()


def split_rows(text):
    return [line.split("\t") for line in text.splitlines()]


def write_rows(path, columns):
    with open(path, "w", encoding="utf8") as outf:
        for row in columns:
            outf.write("\t".join(row) + "\n")


def test_normmapping_subtype_only_leaves_type_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(normierowasch, "datadir", str(tmp_path) + os.sep)
    normierowasch.bagofwords["75"] = 1
    monkeypatch.setattr(
        normierowasch,
        "cts_passage",
        lambda urn, params: '<text><w norm="75" subtype="number">75</w></text>',
    )

    result = normierowasch.normmapping("urn:cts:dsb:test")

    assert split_rows(result) == [["75", "|75|", "", "number"]]


def test_normmapping_following_element_attributes_do_not_leak(tmp_path, monkeypatch):
    monkeypatch.setattr(normierowasch, "datadir", str(tmp_path) + os.sep)
    normierowasch.bagofwords["woda"] = 1
    monkeypatch.setattr(
        normierowasch,
        "cts_passage",
        lambda urn, params: (
            '<text><w norm="WODA">woda</w>'
            '<note subtype="description" type="encoders-comment">ignored</note></text>'
        ),
    )

    result = normierowasch.normmapping("urn:cts:dsb:test")

    assert split_rows(result) == [["woda", "|WODA|", "", ""]]


def test_normmapping_empty_norm_creates_no_mapping(tmp_path, monkeypatch):
    monkeypatch.setattr(normierowasch, "datadir", str(tmp_path) + os.sep)
    normierowasch.bagofwords["jo"] = 1
    monkeypatch.setattr(
        normierowasch,
        "cts_passage",
        lambda urn, params: '<text><w norm="">jo</w></text>',
    )

    result = normierowasch.normmapping("urn:cts:dsb:test")

    assert result == ""
    assert normierowasch.normbag == {}


def test_db_normnonambig_contains_no_empty_pipe_alternative(tmp_path, monkeypatch):
    monkeypatch.setattr(normierowasch, "datadir", str(tmp_path) + os.sep)
    monkeypatch.setattr(normierowasch, "tokenlength", 80)
    monkeypatch.setattr(
        normierowasch,
        "getdoclist",
        lambda ns: "urn:cts:dsb:doc1\tTitle\t1880",
    )
    os.makedirs(tmp_path / "normmapping")
    os.makedirs(tmp_path / "normmappingperyear")
    write_rows(
        tmp_path / "normmappingperyear" / "1880.txt",
        [["woda", "|WODA|", "noun", "sg", "2"]],
    )
    write_rows(tmp_path / "normmapping" / "_normbag.txt", [["|WODA|", "2"]])
    write_rows(
        tmp_path / "normmapping" / "urn_#_cts_#_dsb_#_doc1.txt",
        [["woda", "|WODA|", "noun", "sg", "2"]],
    )

    normierowasch.db()

    con = sqlite3.connect(tmp_path / "normmapping.db")
    rows = con.execute(
        "SELECT norm, frequency FROM normnonambig ORDER BY norm"
    ).fetchall()
    con.close()
    assert rows == [("|WODA|", 2)]


def test_collect_limit_one_does_not_process_second_document(tmp_path, monkeypatch):
    monkeypatch.setattr(normierowasch, "datadir", str(tmp_path) + os.sep)
    monkeypatch.setattr(normierowasch, "count", 1)
    monkeypatch.setattr(normierowasch, "ctsns", "dsb")
    normierowasch.bagofwords["woda"] = 1
    monkeypatch.setattr(
        normierowasch,
        "getdoclist",
        lambda ns: "urn:cts:dsb:doc1\tTitle1\t1880\nurn:cts:dsb:doc2\tTitle2\t1881",
    )

    def fake_cts_passage(urn, params):
        if "doc1" in urn:
            return "<text></text>"  # no word elements, so normmapping returns ""
        return '<text><w norm="WODA">woda</w></text>'

    monkeypatch.setattr(normierowasch, "cts_passage", fake_cts_passage)

    normierowasch.collect()

    assert not (tmp_path / "normmapping" / "urn_#_cts_#_dsb_#_doc2.txt").exists()


def test_db_failed_rebuild_preserves_existing_database(tmp_path, monkeypatch):
    monkeypatch.setattr(normierowasch, "datadir", str(tmp_path) + os.sep)
    monkeypatch.setattr(normierowasch, "tokenlength", 80)
    monkeypatch.setattr(
        normierowasch,
        "getdoclist",
        lambda ns: "urn:cts:dsb:doc1\tTitle\t1880",
    )

    # Pre-existing database with a sentinel row
    con = sqlite3.connect(tmp_path / "normmapping.db")
    con.execute("CREATE TABLE marker(value TEXT)")
    con.execute("INSERT INTO marker VALUES('sentinel')")
    con.commit()
    con.close()

    # Malformed peryear file: single column, so linearr[1] raises IndexError
    os.makedirs(tmp_path / "normmapping")
    os.makedirs(tmp_path / "normmappingperyear")
    (tmp_path / "normmappingperyear" / "1880.txt").write_text(
        "malformed_line\n", encoding="utf8"
    )
    (tmp_path / "normmapping" / "_normbag.txt").write_text("", encoding="utf8")

    with pytest.raises(Exception):
        normierowasch.db()

    # Sentinel must survive the failed rebuild
    con = sqlite3.connect(tmp_path / "normmapping.db")
    rows = con.execute("SELECT value FROM marker").fetchall()
    con.close()
    assert rows == [("sentinel",)]
