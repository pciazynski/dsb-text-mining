import os
import sqlite3

import normierowasch
from dsb_collation import dsb_sortkey


# Keep module-level mutable state isolated between tests.
def setup_function():
    normierowasch.bagofwords.clear()
    normierowasch.normbag.clear()


# Keep module-level mutable state isolated between tests.
def teardown_function():
    normierowasch.bagofwords.clear()
    normierowasch.normbag.clear()


def split_rows(text):
    return [line.split("\t") for line in text.splitlines()]


def read_rows(path):
    with open(path, encoding="utf8") as inf:
        return split_rows(inf.read())


def write_rows(path, columns):
    with open(path, "w", encoding="utf8") as outf:
        for row in columns:
            outf.write("\t".join(row) + "\n")


def test_load_bagofwords_reads_token_frequencies(tmp_path, monkeypatch):
    os.makedirs(tmp_path / "bagofwords")
    (tmp_path / "bagofwords" / "_all.txt").write_text(
        """a	17307
ße	7204
""",
        encoding="utf8",
    )
    monkeypatch.setattr(normierowasch, "datadir", str(tmp_path) + os.sep)

    normierowasch.load_bagofwords()

    assert normierowasch.bagofwords == {"a": 17307, "ße": 7204}


def test_tokencheck_reports_membership():
    normierowasch.bagofwords["a"] = 17307

    assert normierowasch.tokencheck("a") is True
    assert normierowasch.tokencheck("missing") is False


def test_normmapping_maps_known_token_and_logs_unknown(tmp_path, monkeypatch):
    monkeypatch.setattr(normierowasch, "datadir", str(tmp_path) + os.sep)
    normierowasch.bagofwords["woda"] = 1
    monkeypatch.setattr(
        normierowasch,
        "cts_passage",
        lambda urn, params: (
            '<text><w norm="WODA" type="noun" subtype="sg">Woda.</w>'
            '<w norm="DOM">dom</w></text>'
        ),
    )

    result = normierowasch.normmapping("urn:cts:dsb:work")

    assert split_rows(result) == [["woda", "|WODA|", "noun", "sg"]]
    assert normierowasch.normbag == {"|WODA|": 1}
    assert (tmp_path / "_ERROR.txt").read_text(encoding="utf8") == (
        "urn:cts:dsb:work normierowasch unknown token dom\n"
    )


def test_process_counts_rows_and_aggregates_years(tmp_path):
    folder = str(tmp_path / "normmapping")
    peryear = tmp_path / "normmappingperyear"
    os.makedirs(folder)
    os.makedirs(peryear)
    write_rows(
        peryear / "1880.txt",
        [
            ["woda", "|WODA|", "noun", "sg"],
            ["woda", "|WODA|", "noun", "sg"],
            ["dom", "|DOM|", "noun", "sg"],
        ],
    )
    write_rows(peryear / "1881.txt", [["woda", "|WODA|", "noun", "sg"]])

    normierowasch.process(folder)

    assert read_rows(peryear / "1880.txt") == [
        ["woda", "|WODA|", "noun", "sg", "2"],
        ["dom", "|DOM|", "noun", "sg", "1"],
    ]
    assert read_rows(peryear / "1881.txt") == [["woda", "|WODA|", "noun", "sg", "1"]]
    assert read_rows(tmp_path / "normmapping" / "_all.txt") == [
        ["woda", "|WODA|", "noun", "sg", "3"],
        ["dom", "|DOM|", "noun", "sg", "1"],
    ]


def test_reset_replaces_mapping_directories(tmp_path, monkeypatch):
    mapping = tmp_path / "normmapping"
    peryear = tmp_path / "normmappingperyear"
    os.makedirs(mapping)
    os.makedirs(peryear)
    (mapping / "stale.txt").write_text("stale", encoding="utf8")
    (peryear / "stale.txt").write_text("stale", encoding="utf8")
    monkeypatch.setattr(normierowasch, "datadir", str(tmp_path) + os.sep)

    normierowasch.reset()

    assert os.listdir(mapping) == []
    assert os.listdir(peryear) == []


def test_getdoclist_prefers_local_urnlist(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "urnlist.txt").write_text(
        """urn:cts:dsb:doc1	Document	1880
""",
        encoding="utf8",
    )

    result = normierowasch.getdoclist("dsb")

    assert result == "urn:cts:dsb:doc1\tDocument\t1880"


def test_inittables_creates_expected_empty_schema(tmp_path, monkeypatch):
    monkeypatch.setattr(normierowasch, "datadir", str(tmp_path) + os.sep)
    monkeypatch.setattr(normierowasch, "tokenlength", 80)

    normierowasch.initTables()

    con = sqlite3.connect(tmp_path / "normmapping.db")
    tables = {
        row[0]
        for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    columns = [
        row[1]
        for row in con.execute("PRAGMA table_info(tokennormtypesubtypedatefrequency)")
    ]
    assert tables == {
        "urndatenormbag",
        "tokennormtypesubtypedatefrequency",
        "tokennormtypesubtypefrequency",
        "normfrequency",
        "normtokenfrequency",
        "normnonambig",
    }
    assert columns == ["token", "norm", "type", "subtype", "date", "frequency"]
    assert con.execute(
        "SELECT COUNT(*) FROM tokennormtypesubtypedatefrequency"
    ).fetchone() == (0,)
    con.close()


def test_db_populates_tables_indexes_and_current_nonambig_behavior(
    tmp_path, monkeypatch
):
    datadir = str(tmp_path) + os.sep
    monkeypatch.setattr(normierowasch, "datadir", datadir)
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
    write_rows(
        tmp_path / "normmapping" / "_normbag.txt",
        [["|WODA|", "2"]],
    )
    write_rows(
        tmp_path / "normmapping" / "urn_#_cts_#_dsb_#_doc1.txt",
        [["woda", "|WODA|", "noun", "sg", "2"]],
    )

    normierowasch.db()

    con = sqlite3.connect(tmp_path / "normmapping.db")
    assert con.execute(
        "SELECT token, norm, type, subtype, date, frequency "
        "FROM tokennormtypesubtypedatefrequency"
    ).fetchall() == [("woda", "|WODA|", "noun", "sg", 1880, 2)]
    assert con.execute(
        "SELECT token, norm, type, subtype, frequency "
        "FROM tokennormtypesubtypefrequency"
    ).fetchall() == [("woda", "|WODA|", "noun", "sg", 2)]
    assert con.execute(
        "SELECT norm, token, frequency FROM normtokenfrequency"
    ).fetchall() == [("|WODA|", "woda", 2)]
    assert con.execute(
        "SELECT norm, frequency, sortkey FROM normfrequency"
    ).fetchall() == [("|WODA|", 2, dsb_sortkey("WODA"))]
    assert con.execute("SELECT urn, date, normbag FROM urndatenormbag").fetchall() == [
        ("urn:cts:dsb:doc1", 1880, "#|WODA|#")
    ]

    indexes = {
        row[0]
        for row in con.execute("SELECT name FROM sqlite_master WHERE type='index'")
    }
    assert indexes == {
        "tokenindextype",
        "normindextype",
        "typeindextype",
        "subtypeindextype",
        "tokenindex",
        "normindex",
        "typeindex",
        "subtypeindex",
        "dateindex",
        "normfrequencyindex",
        "normfrequencysortkeyindex",
        "normtokenindex",
        "normtokentokenindex",
        "normurnindex",
        "urnindex",
        "urndateindex",
        "normnonambignorm",
        "normnonambigsortkey",
    }
    con.close()


def test_main_dispatches_db_mode(monkeypatch):
    calls = []
    monkeypatch.setattr(normierowasch, "load_bagofwords", lambda: calls.append("load"))
    monkeypatch.setattr(normierowasch, "db", lambda: calls.append("db"))
    monkeypatch.setattr(normierowasch, "collect", lambda: calls.append("collect"))

    normierowasch.main(["db"])

    assert calls == ["load", "db"]


def test_main_dispatches_collect_mode(monkeypatch):
    calls = []
    monkeypatch.setattr(normierowasch, "load_bagofwords", lambda: calls.append("load"))
    monkeypatch.setattr(normierowasch, "db", lambda: calls.append("db"))
    monkeypatch.setattr(normierowasch, "collect", lambda: calls.append("collect"))

    normierowasch.main(["collect"])

    assert calls == ["load", "collect"]


def test_main_without_args_runs_collect_then_db(monkeypatch):
    calls = []
    monkeypatch.setattr(normierowasch, "load_bagofwords", lambda: calls.append("load"))
    monkeypatch.setattr(normierowasch, "db", lambda: calls.append("db"))
    monkeypatch.setattr(normierowasch, "collect", lambda: calls.append("collect"))

    normierowasch.main([])

    assert calls == ["load", "collect", "db"]


def test_collect_writes_ok_and_restricted_status_per_document(tmp_path, monkeypatch):
    monkeypatch.setattr(normierowasch, "datadir", str(tmp_path) + os.sep)
    monkeypatch.setattr(normierowasch, "count", -1)
    monkeypatch.setattr(normierowasch, "getdoclist", lambda ns: "\n".join([
        "urn:cts:dsb:doc1\tRestricted\t1880",
        "urn:cts:dsb:doc2\tOpen\t1881",
    ]))
    normierowasch.bagofwords["jo"] = 1

    def fake_cts_passage(urn, params):
        if urn.endswith("doc1"):
            return "Error code 7: Unauthorized Access"
        return '<text><w norm="JO">jo</w></text>'

    monkeypatch.setattr(normierowasch, "cts_passage", fake_cts_passage)

    normierowasch.collect()

    assert read_rows(tmp_path / "normmapping" / "_status.txt") == [
        ["urn:cts:dsb:doc1", "restricted"],
        ["urn:cts:dsb:doc2", "ok"],
    ]
