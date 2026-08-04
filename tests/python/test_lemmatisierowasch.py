import os
import sqlite3

import lemmatisierowasch
import pytest
from dsb_collation import dsb_sortkey


@pytest.fixture(autouse=True)
def reset_module_globals(monkeypatch):
    lemmatisierowasch.bagofwords.clear()
    lemmatisierowasch.lemmabag.clear()
    monkeypatch.setattr(lemmatisierowasch, "ctsurl", "")
    yield
    lemmatisierowasch.bagofwords.clear()
    lemmatisierowasch.lemmabag.clear()


def rows(text):
    """Split tab-separated text into column lists so empty columns stay visible."""
    return [line.split("\t") for line in text.splitlines()]


def read_rows(path):
    with open(path, encoding="utf8") as inf:
        return rows(inf.read())


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
    monkeypatch.setattr(lemmatisierowasch, "datadir", str(tmp_path) + os.sep)

    lemmatisierowasch.load_bagofwords()

    assert lemmatisierowasch.bagofwords == {"a": 17307, "ße": 7204}


def test_requestctsurl_normalizes_urn_and_joins_response_lines(monkeypatch):
    requested_urls = []

    def fake_urlopen(url):
        requested_urls.append(url)
        return [b"https://cts.example/", b"api/"]

    monkeypatch.setattr(lemmatisierowasch, "urlopen", fake_urlopen)

    lemmatisierowasch.requestctsurl("dsb:work")

    assert requested_urls == ["https://urncts.eu/namespaceresolver/dsb"]
    assert lemmatisierowasch.ctsurl == "https://cts.example/api/"


def test_requestctsurl_keeps_existing_endpoint_without_network(monkeypatch):
    monkeypatch.setattr(lemmatisierowasch, "ctsurl", "https://cts.example/")

    def fail_urlopen(url):
        raise AssertionError("unexpected network request to " + url)

    monkeypatch.setattr(lemmatisierowasch, "urlopen", fail_urlopen)

    lemmatisierowasch.requestctsurl("urn:cts:dsb:work")

    assert lemmatisierowasch.ctsurl == "https://cts.example/"


def test_tokencheck_reports_membership():
    lemmatisierowasch.bagofwords["a"] = 17307

    assert lemmatisierowasch.tokencheck("a") is True
    assert lemmatisierowasch.tokencheck("missing") is False


def test_lemmamapping_returns_known_annotated_words(
    tmp_path, monkeypatch, reset_cts_globals
):
    monkeypatch.setattr(lemmatisierowasch, "datadir", str(tmp_path) + os.sep)
    monkeypatch.setattr(lemmatisierowasch, "ctsurl", "https://cts.example/")
    reset_cts_globals.manualurl = "https://cts.example/"
    lemmatisierowasch.bagofwords.update({"dṙewo": 14, "tog": 837})
    payload = '<text><w lemma="DRJEWO">dṙewo</w>' '<w lemma="TEN|TO">tog</w></text>'
    monkeypatch.setattr(
        reset_cts_globals,
        "urlopen",
        lambda url, timeout: [payload.encode("utf8")],
    )

    result = lemmatisierowasch.lemmamapping("urn:cts:dsb:work")

    # token, lemma, type, subtype
    assert rows(result) == [
        ["dṙewo", "|DRJEWO|", "", ""],
        ["tog", "|TEN|TO|", "", ""],
    ]
    assert lemmatisierowasch.lemmabag == {"|DRJEWO|": 1, "|TEN|TO|": 1}
    assert not (tmp_path / "_ERROR.txt").exists()


def test_lemmamapping_logs_unknown_token(tmp_path, monkeypatch, reset_cts_globals):
    monkeypatch.setattr(lemmatisierowasch, "datadir", str(tmp_path) + os.sep)
    monkeypatch.setattr(lemmatisierowasch, "ctsurl", "https://cts.example/")
    reset_cts_globals.manualurl = "https://cts.example/"
    payload = '<text><w lemma="DOM">domu</w></text>'
    monkeypatch.setattr(
        reset_cts_globals,
        "urlopen",
        lambda url, timeout: [payload.encode("utf8")],
    )

    result = lemmatisierowasch.lemmamapping("urn:cts:dsb:work")

    assert result == ""
    assert (tmp_path / "_ERROR.txt").read_text(encoding="utf8") == (
        "urn:cts:dsb:work lemmatisierowasch unknown token domu\n"
    )


def test_process_counts_rows_and_aggregates_years(tmp_path):
    folder = str(tmp_path / "lemmamapping")
    peryear = tmp_path / "lemmamappingperyear"
    os.makedirs(folder)
    os.makedirs(peryear)
    write_rows(
        peryear / "1880.txt",
        [
            ["dṙewo", "|DRJEWO|", "", ""],
            ["dṙewo", "|DRJEWO|", "", ""],
            ["tog", "|TEN|TO|", "", ""],
        ],
    )
    write_rows(peryear / "1881.txt", [["dṙewo", "|DRJEWO|", "", ""]])

    lemmatisierowasch.process(folder)

    # token, lemma, type, subtype, frequency
    assert read_rows(peryear / "1880.txt") == [
        ["dṙewo", "|DRJEWO|", "", "", "2"],
        ["tog", "|TEN|TO|", "", "", "1"],
    ]
    assert read_rows(peryear / "1881.txt") == [["dṙewo", "|DRJEWO|", "", "", "1"]]
    assert read_rows(tmp_path / "lemmamapping" / "_all.txt") == [
        ["dṙewo", "|DRJEWO|", "", "", "3"],
        ["tog", "|TEN|TO|", "", "", "1"],
    ]


def test_process_aggregates_lemmamapping_output_without_type_attributes(
    tmp_path, monkeypatch, reset_cts_globals
):
    monkeypatch.setattr(lemmatisierowasch, "datadir", str(tmp_path) + os.sep)
    monkeypatch.setattr(lemmatisierowasch, "ctsurl", "https://cts.example/")
    reset_cts_globals.manualurl = "https://cts.example/"
    lemmatisierowasch.bagofwords.update({"dṙewo": 14, "tog": 837})
    payload = '<text><w lemma="DRJEWO">dṙewo</w>' '<w lemma="TEN|TO">tog</w></text>'
    monkeypatch.setattr(
        reset_cts_globals,
        "urlopen",
        lambda url, timeout: [payload.encode("utf8")],
    )
    folder = str(tmp_path / "lemmamapping")
    peryear = tmp_path / "lemmamappingperyear"
    os.makedirs(folder)
    os.makedirs(peryear)
    (peryear / "1880.txt").write_text(
        lemmatisierowasch.lemmamapping("urn:cts:dsb:work"), encoding="utf8"
    )

    lemmatisierowasch.process(folder)

    # token, lemma, type, subtype, frequency
    assert read_rows(peryear / "1880.txt") == [
        ["dṙewo", "|DRJEWO|", "", "", "1"],
        ["tog", "|TEN|TO|", "", "", "1"],
    ]
    assert read_rows(tmp_path / "lemmamapping" / "_all.txt") == [
        ["dṙewo", "|DRJEWO|", "", "", "1"],
        ["tog", "|TEN|TO|", "", "", "1"],
    ]


def test_reset_replaces_mapping_directories(tmp_path, monkeypatch):
    mapping = tmp_path / "lemmamapping"
    peryear = tmp_path / "lemmamappingperyear"
    os.makedirs(mapping)
    os.makedirs(peryear)
    (mapping / "stale.txt").write_text("stale", encoding="utf8")
    (peryear / "stale.txt").write_text("stale", encoding="utf8")
    monkeypatch.setattr(lemmatisierowasch, "datadir", str(tmp_path) + os.sep)

    lemmatisierowasch.reset()

    assert os.listdir(mapping) == []
    assert os.listdir(peryear) == []


def test_getdoclist_prefers_local_urnlist(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "urnlist.txt").write_text(
        """urn:cts:dsb:bramborske_nowiny_1880_51.20220111:	Document	1880
""",
        encoding="utf8",
    )

    result = lemmatisierowasch.getdoclist("dsb")

    assert result == "urn:cts:dsb:bramborske_nowiny_1880_51.20220111:	Document	1880"


def test_inittables_creates_expected_empty_schema(tmp_path, monkeypatch):
    monkeypatch.setattr(lemmatisierowasch, "datadir", str(tmp_path) + os.sep)
    monkeypatch.setattr(lemmatisierowasch, "tokenlength", 80)

    lemmatisierowasch.initTables()

    con = sqlite3.connect(tmp_path / "lemmamapping.db")
    tables = {
        row[0]
        for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    columns = [
        row[1]
        for row in con.execute("PRAGMA table_info(tokenlemmatypesubtypedatefrequency)")
    ]
    assert tables == {
        "urndatelemmabag",
        "tokenlemmatypesubtypedatefrequency",
        "tokenlemmatypesubtypefrequency",
        "lemmafrequency",
        "lemmatokenfrequency",
        "lemmanonambig",
    }
    assert columns == ["token", "lemma", "type", "subtype", "date", "frequency"]
    assert con.execute(
        "SELECT COUNT(*) FROM tokenlemmatypesubtypedatefrequency"
    ).fetchone() == (0,)
    con.close()


def test_db_populates_all_tables_and_indexes(tmp_path, monkeypatch):
    mapping = tmp_path / "lemmamapping"
    peryear = tmp_path / "lemmamappingperyear"
    os.makedirs(mapping)
    os.makedirs(peryear)
    (peryear / "1880.txt").write_text(
        """dṙewo	|DRJEWO|			2
""",
        encoding="utf8",
    )
    (mapping / "_lemmabag.txt").write_text(
        """|DRJEWO|	2
""",
        encoding="utf8",
    )
    (
        mapping / "urn_#_cts_#_dsb_#_bramborske_nowiny_1880_51.20220111_#_.txt"
    ).write_text(
        """dṙewo	|DRJEWO|		""",
        encoding="utf8",
    )
    (tmp_path / "urnlist.txt").write_text(
        """urn:cts:dsb:bramborske_nowiny_1880_51.20220111:	Document	1880
""",
        encoding="utf8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(lemmatisierowasch, "datadir", str(tmp_path) + os.sep)

    lemmatisierowasch.db()

    con = sqlite3.connect(tmp_path / "lemmamapping.db")
    assert con.execute(
        "SELECT token, lemma, type, subtype, date, frequency "
        "FROM tokenlemmatypesubtypedatefrequency"
    ).fetchall() == [("dṙewo", "|DRJEWO|", "", "", 1880, 2)]
    assert con.execute(
        "SELECT token, lemma, type, subtype, frequency "
        "FROM tokenlemmatypesubtypefrequency"
    ).fetchall() == [("dṙewo", "|DRJEWO|", "", "", 2)]
    assert con.execute(
        "SELECT lemma, token, frequency FROM lemmatokenfrequency"
    ).fetchall() == [("|DRJEWO|", "dṙewo", 2)]
    assert con.execute(
        "SELECT lemma, frequency, sortkey FROM lemmafrequency"
    ).fetchall() == [("|DRJEWO|", 2, dsb_sortkey("DRJEWO"))]
    assert con.execute(
        "SELECT urn, date, lemmabag FROM urndatelemmabag"
    ).fetchall() == [
        (
            "urn:cts:dsb:bramborske_nowiny_1880_51.20220111:",
            1880,
            "#|DRJEWO|#",
        )
    ]
    indexes = {
        row[0]
        for row in con.execute("SELECT name FROM sqlite_master WHERE type='index'")
    }
    assert indexes == {
        "tokenindextype",
        "lemmaindextype",
        "subtypeindextype",
        "tokenindex",
        "lemmaindex",
        "typeindex",
        "subtypeindex",
        "dateindex",
        "lemmafrequencyindex",
        "lemmafrequencysortkeyindex",
        "lemmatokenlemmaindex",
        "lemmatokentokenindex",
        "lemmaurnindex",
        "urnindex",
        "urndateindex",
        "lemmanonambiglemma",
        "lemmanonambigsortkey",
    }
    con.close()


# --------------------------------------------------- per document status file

PASSAGE = '<text><w lemma="JO">jo</w></text>'
UNAUTHORIZED = "Error code 7: Unauthorized Access"


def setup_collect(tmp_path, monkeypatch, pythoncts, doclist, respond):
    """Run collect() against a fake CTS endpoint; respond(url, timeout) fakes it."""
    monkeypatch.setattr(lemmatisierowasch, "datadir", str(tmp_path) + os.sep)
    monkeypatch.setattr(lemmatisierowasch, "count", -1)
    monkeypatch.setattr(lemmatisierowasch, "ctsurl", "https://cts.example/")
    monkeypatch.setattr(lemmatisierowasch, "getdoclist", lambda ns: doclist)
    pythoncts.manualurl = "https://cts.example/"
    monkeypatch.setattr(pythoncts, "urlopen", respond)


def test_collect_writes_ok_and_restricted_status_per_document(
    tmp_path, monkeypatch, reset_cts_globals
):
    doclist = "\n".join(
        [
            "urn:cts:dsb:doc1	Restricted	1880",
            "urn:cts:dsb:doc2	Open	1881",
        ]
    )
    lemmatisierowasch.bagofwords["jo"] = 1

    def respond(url, timeout):
        if "doc1" in url:
            return [UNAUTHORIZED.encode("utf8")]
        return [PASSAGE.encode("utf8")]

    setup_collect(tmp_path, monkeypatch, reset_cts_globals, doclist, respond)

    lemmatisierowasch.collect()

    # urn, status
    assert read_rows(tmp_path / "lemmamapping" / "_status.txt") == [
        ["urn:cts:dsb:doc1", "restricted"],
        ["urn:cts:dsb:doc2", "ok"],
    ]


def test_collect_writes_invalid_status_for_response_without_word_elements(
    tmp_path, monkeypatch, reset_cts_globals
):
    doclist = "urn:cts:dsb:doc1	Open	1880"
    lemmatisierowasch.bagofwords["jo"] = 1
    payload = "<br /><b>Warning</b>: Undefined variable $urn in passage.php"

    setup_collect(
        tmp_path,
        monkeypatch,
        reset_cts_globals,
        doclist,
        lambda url, timeout: [payload.encode("utf8")],
    )

    lemmatisierowasch.collect()

    assert read_rows(tmp_path / "lemmamapping" / "_status.txt") == [
        ["urn:cts:dsb:doc1", "invalid"]
    ]


def test_collect_writes_empty_status_when_no_word_is_mapped(
    tmp_path, monkeypatch, reset_cts_globals
):
    doclist = "urn:cts:dsb:doc1	Open	1880"
    payload = '<text><w lemma="DOM">domu</w></text>'

    setup_collect(
        tmp_path,
        monkeypatch,
        reset_cts_globals,
        doclist,
        lambda url, timeout: [payload.encode("utf8")],
    )

    lemmatisierowasch.collect()

    assert read_rows(tmp_path / "lemmamapping" / "_status.txt") == [
        ["urn:cts:dsb:doc1", "empty"]
    ]


def test_collect_writes_ok_status_when_a_retried_request_finally_succeeds(
    tmp_path, monkeypatch, reset_cts_globals, no_sleep
):
    doclist = "urn:cts:dsb:doc1	Open	1880"
    lemmatisierowasch.bagofwords["jo"] = 1
    attempts = []

    def respond(url, timeout):
        attempts.append(url)
        if len(attempts) < 3:
            raise TimeoutError("timed out")
        return [PASSAGE.encode("utf8")]

    setup_collect(tmp_path, monkeypatch, reset_cts_globals, doclist, respond)

    lemmatisierowasch.collect()

    assert len(attempts) == 3
    assert read_rows(tmp_path / "lemmamapping" / "_status.txt") == [
        ["urn:cts:dsb:doc1", "ok"]
    ]


def test_collect_writes_unavailable_status_when_all_retries_fail(
    tmp_path, monkeypatch, reset_cts_globals, no_sleep
):
    doclist = "\n".join(
        [
            "urn:cts:dsb:doc1	Unreachable	1880",
            "urn:cts:dsb:doc2	Open	1881",
        ]
    )
    lemmatisierowasch.bagofwords["jo"] = 1

    def respond(url, timeout):
        if "doc1" in url:
            raise TimeoutError("timed out")
        return [PASSAGE.encode("utf8")]

    setup_collect(tmp_path, monkeypatch, reset_cts_globals, doclist, respond)

    lemmatisierowasch.collect()

    assert read_rows(tmp_path / "lemmamapping" / "_status.txt") == [
        ["urn:cts:dsb:doc1", "unavailable"],
        ["urn:cts:dsb:doc2", "ok"],
    ]
    assert (tmp_path / "lemmamapping" / "urn_#_cts_#_dsb_#_doc2.txt").exists()
