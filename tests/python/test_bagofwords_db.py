import os
import sqlite3

from dsb_collation import dsb_sortkey


def make_corpus(datadir, monkeypatch):
    """Write a tiny fixture corpus into datadir, matching collect()'s layout."""
    import bagofwords

    os.makedirs(datadir + "bagofwords", exist_ok=True)
    os.makedirs(datadir + "bagofwordsperyear", exist_ok=True)

    with open(datadir + "bagofwords/_all.txt", "w", encoding="utf8") as outf:
        outf.write("""wóda	5
luft	5
zemja	1
""")

    with open(datadir + "bagofwordsperyear/1800.txt", "w", encoding="utf8") as outf:
        outf.write("""wóda	3
zemja	1
""")
    with open(datadir + "bagofwordsperyear/1850.txt", "w", encoding="utf8") as outf:
        outf.write("""wóda	2
luft	5
""")

    with open(
        datadir + "bagofwords/urn_#_cts_#_dsb_#_doc1.txt", "w", encoding="utf8"
    ) as outf:
        outf.write("""wóda	3
zemja	1""")
    with open(
        datadir + "bagofwords/urn_#_cts_#_dsb_#_doc2.txt", "w", encoding="utf8"
    ) as outf:
        outf.write("""wóda	2
luft	5""")

    doclist = """urn:cts:dsb:doc1	Doc One	1800
urn:cts:dsb:doc2	Doc Two	1850"""
    monkeypatch.setattr(bagofwords, "getdoclist", lambda ns: doclist)


def table_columns(cursor, table):
    return [row[1] for row in cursor.execute("PRAGMA table_info(" + table + ")")]


def test_inittables_creates_expected_schema(datadir):
    import bagofwords

    bagofwords.initTables()
    con = sqlite3.connect(datadir + "bagofwords.db")
    cursor = con.cursor()
    tables = {
        row[0]
        for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert tables == {"tokendatecount", "tokencount", "urndatewordbag"}
    assert table_columns(cursor, "tokendatecount") == ["token", "date", "frequency"]
    assert table_columns(cursor, "tokencount") == ["token", "frequency", "sortkey"]
    assert table_columns(cursor, "urndatewordbag") == ["urn", "date", "wordbag"]
    con.close()


def test_inittables_is_idempotent(datadir):
    import bagofwords

    bagofwords.initTables()
    con = sqlite3.connect(datadir + "bagofwords.db")
    con.execute("INSERT INTO tokencount VALUES ('stale', 1, '')")
    con.commit()
    con.close()

    bagofwords.initTables()  # must replace the existing database
    con = sqlite3.connect(datadir + "bagofwords.db")
    assert con.execute("SELECT COUNT(*) FROM tokencount").fetchone()[0] == 0
    con.close()


def test_db_populates_tables_from_corpus(datadir, monkeypatch):
    import bagofwords

    make_corpus(datadir, monkeypatch)
    bagofwords.db()

    con = sqlite3.connect(datadir + "bagofwords.db")
    cursor = con.cursor()

    rows = cursor.execute(
        "SELECT token, frequency, sortkey FROM tokencount ORDER BY token"
    ).fetchall()
    assert len(rows) == 3
    assert [(t, f) for t, f, _ in rows] == [("luft", 5), ("wóda", 5), ("zemja", 1)]
    for token, _, sortkey in rows:
        assert sortkey == dsb_sortkey(token)

    datecounts = cursor.execute(
        "SELECT token, date, frequency FROM tokendatecount ORDER BY date, token"
    ).fetchall()
    assert datecounts == [
        ("wóda", 1800, 3),
        ("zemja", 1800, 1),
        ("luft", 1850, 5),
        ("wóda", 1850, 2),
    ]

    wordbags = dict(
        cursor.execute("SELECT urn, wordbag FROM urndatewordbag").fetchall()
    )
    assert wordbags == {
        "urn:cts:dsb:doc1": "|wóda|zemja|",
        "urn:cts:dsb:doc2": "|wóda|luft|",
    }
    dates = dict(cursor.execute("SELECT urn, date FROM urndatewordbag").fetchall())
    # SQLite's DATE affinity coerces the year strings to integers on storage.
    assert dates == {"urn:cts:dsb:doc1": 1800, "urn:cts:dsb:doc2": 1850}
    con.close()


def test_db_creates_all_indexes(datadir, monkeypatch):
    import bagofwords

    make_corpus(datadir, monkeypatch)
    bagofwords.db()

    con = sqlite3.connect(datadir + "bagofwords.db")
    names = {
        row[0]
        for row in con.execute("SELECT name FROM sqlite_master WHERE type='index'")
    }
    assert names == {
        "tokenindex",
        "tokensortkeyindex",
        "tokendateindex",
        "dateindex",
        "tokenurnindex",
        "urnindex",
        "urndateindex",
    }
    con.close()
