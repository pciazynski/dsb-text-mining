"""Shared ETL logic for the norm and lemma mapping pipelines.

`normierowasch` and `lemmatisierowasch` are the same pipeline with one word
swapped ("norm" vs "lemma"). Each of them is a thin wrapper that only declares
its per-field configuration (``FIELD``, directory/table names, ``INDEX_SQL``,
the mutable bag dict, ...) and delegates every function here, passing its own
module object as ``mod``. All state and monkeypatch points (``datadir``,
``cts_passage``, ``count``, ...) are read from ``mod`` at call time, so the
wrappers stay patchable in isolation.
"""

import os
import sys
import shutil
import sqlite3
from collections import Counter
from contextlib import closing

from dsb_collation import dsb_sortkey


def _path(mod, *parts):
    return os.path.join(mod.datadir, *parts)


def load_bagofwords(mod):
    with open(_path(mod, "bagofwords", "_all.txt"), "r", encoding="utf8") as bwin:
        for line in bwin:
            token, freq = line.split("\t")[:2]
            mod.bagofwords[token] = int(freq)


def tokencheck(mod, token):
    return token in mod.bagofwords


def _attr_value(attrs, name):
    marker = name + '="'
    start = 0
    while True:
        idx = attrs.find(marker, start)
        if idx == -1:
            return ""
        if idx == 0 or attrs[idx - 1] in " \t\n\r":
            return attrs[idx + len(marker) :].split('"', 1)[0]
        start = idx + 1


def _load_passage(mod, urn):
    passage_path = _path(mod, "passagecache", urn.replace(":", "_#_") + ".txt")
    if os.path.exists(passage_path):
        with open(passage_path, "r", encoding="utf8") as passagein:
            return passagein.read()

    before = getattr(mod, "before_mapping", None)
    if before is not None:
        before(urn)
    res = mod.cts_passage(urn, "&copyrighttoken=" + mod.copyrighttoken)
    if "Error code 7:" not in res:
        os.makedirs(os.path.dirname(passage_path), exist_ok=True)
        with open(passage_path, "w", encoding="utf8") as passageout:
            passageout.write(res)
    return res


def _set_mapping_status(mod, res):
    if "Error code 7:" in res:
        mod.mapping_status = "restricted"
    elif "<w" not in res:
        mod.mapping_status = "invalid"
    else:
        mod.mapping_status = "empty"


def _normalize_token(word_content):
    return (
        word_content.split("</", 1)[0]
        .replace('"', " ")
        .replace("'", " ")
        .replace(".", "")
        .strip()
        .lower()
    )


def mapping(mod, urn):
    bag = getattr(mod, mod.BAG_ATTR)
    res = _load_passage(mod, urn)
    _set_mapping_status(mod, res)
    wordelements = res.split("<w")
    total = str(len(wordelements))
    out = ""
    for wecount, we in enumerate(wordelements):
        if str(wecount).endswith("00"):
            print("\rItems:" + str(wecount) + "/" + total, sep=" ", end="", flush=True)
        if "</w" not in we:
            continue
        word_attributes, word_content = we.split(">", 1)
        token = _normalize_token(word_content)
        if not tokencheck(mod, token):
            with open(_path(mod, "_ERROR.txt"), "a", encoding="utf8") as errout:
                errout.write(
                    urn + " " + mod.MODULE_LABEL + " unknown token " + token + "\n"
                )
            continue
        value = _attr_value(word_attributes, mod.FIELD).replace("'", " ").strip()
        if not value:
            continue
        annotated = "|" + value + "|"
        bag[annotated] = bag.get(annotated, 0) + 1
        wetype = _attr_value(word_attributes, "type")
        subtype = _attr_value(word_attributes, "subtype")
        out += "\t".join([token, annotated, wetype, subtype]) + "\n"
    if out.strip():
        mod.mapping_status = "ok"
    print("\rOK                                       ")
    return out


def process(foldername):
    peryear = foldername + "peryear"
    for yearfile in sorted(os.listdir(peryear)):
        print("process " + foldername + ":" + yearfile)
        wb = Counter()
        path = os.path.join(peryear, yearfile)
        with open(path, "r", encoding="utf8") as inf:
            for line in inf:
                wb[line.replace("\n", "")] += 1
        with open(path, "w", encoding="utf8") as outf:
            for token, value in wb.most_common():
                outf.write(token + "\t" + str(value) + "\n")

    wb = Counter()
    for yearfile in sorted(os.listdir(peryear)):
        with open(os.path.join(peryear, yearfile), "r", encoding="utf8") as inf:
            for line in inf:
                linearr = line.split("\t")
                wb["\t".join(linearr[:4])] += int(linearr[4])
    with open(os.path.join(foldername, "_all.txt"), "w", encoding="utf8") as outf:
        for key, value in wb.most_common():
            outf.write(key + "\t" + str(value) + "\n")


def reset(mod):
    os.makedirs(mod.datadir, exist_ok=True)
    for name in (mod.MAPPING_DIR, mod.PERYEAR_DIR):
        path = _path(mod, name)
        if os.path.exists(path):
            shutil.rmtree(path)
        os.mkdir(path)


def getdoclist(mod, ctsns):
    if os.path.exists("urnlist.txt"):
        with open("urnlist.txt", "r", encoding="utf8") as inf:
            return inf.read().strip()
    return mod.cts_inventory(ctsns).strip()


def collect(mod):
    mod.reset()
    print("Collect...")
    doclist = mod.getdoclist(mod.ctsns).split("\n")
    if mod.count == -1:
        mod.count = len(doclist)
    map_urn = getattr(mod, mod.MAPPING_ATTR)
    status_path = _path(mod, mod.MAPPING_DIR, "_status.txt")
    with open(status_path, "w", encoding="utf8") as statusout:
        for line in doclist:
            parts = line.split("\t")
            urn = parts[0]
            year = parts[2]
            if len(year) <= 1 or mod.count <= 0:
                continue
            print(str(mod.count) + " " + urn)
            mod.count -= 1
            try:
                rs = map_urn(urn)
            except Exception:
                status = "unavailable"
                rs = ""
            else:
                status = getattr(mod, "mapping_status", "empty")
            if rs.strip():
                urn_path = _path(mod, mod.MAPPING_DIR, urn.replace(":", "_#_") + ".txt")
                year_path = _path(mod, mod.PERYEAR_DIR, year + ".txt")
                with (
                    open(urn_path, "w", encoding="utf8") as outf,
                    open(year_path, "a", encoding="utf8") as outyf,
                ):
                    outf.write(rs)
                    outyf.write(rs)
            else:
                print("No Items")
            statusout.write(urn + "\t" + status + "\n")

    mod.process(_path(mod, mod.MAPPING_DIR))
    bag = getattr(mod, mod.BAG_ATTR)
    with open(_path(mod, mod.MAPPING_DIR, mod.BAG_FILE), "w", encoding="utf8") as outf:
        for token, value in sorted(bag.items(), key=lambda x: x[1], reverse=True):
            if token.strip():
                outf.write(token + "\t" + str(value) + "\n")


def index(mod, db_path=None):
    db_path = db_path or _path(mod, mod.DB_NAME)
    con = sqlite3.connect(db_path)
    cursor = con.cursor()
    print("Indexing...")
    for sql in mod.INDEX_SQL:
        cursor.execute(sql)
    con.commit()
    con.close()


def initTables(mod, db_path=None):
    field = mod.FIELD
    db_path = db_path or _path(mod, mod.DB_NAME)
    if os.path.exists(db_path):
        os.remove(db_path)
    con = sqlite3.connect(db_path)
    cursor = con.cursor()
    tl = str(mod.tokenlength)
    cursor.execute(
        f"CREATE TABLE urndate{field}bag(urn VARCHAR (50),date DATE,{field}bag text)"
    )
    cursor.execute(
        f"CREATE TABLE token{field}typesubtypedatefrequency("
        f"token VARCHAR ({tl}),"
        f"{field} VARCHAR (50),type VARCHAR (10),subtype VARCHAR (10),"
        "date DATE,frequency INTEGER)"
    )
    cursor.execute(
        f"CREATE TABLE token{field}typesubtypefrequency("
        f"token VARCHAR ({tl}),"
        f"{field} VARCHAR (50),type VARCHAR (10),subtype VARCHAR (10),"
        "frequency INTEGER)"
    )
    cursor.execute(
        f"CREATE TABLE {field}frequency("
        f"{field} VARCHAR (50),frequency INTEGER,sortkey TEXT)"
    )
    cursor.execute(
        f"CREATE TABLE {field}tokenfrequency("
        f"{field} VARCHAR (50),token VARCHAR ({tl}),frequency INTEGER)"
    )
    cursor.execute(
        f"CREATE TABLE {field}nonambig("
        f"{field} VARCHAR (50),frequency INTEGER,sortkey TEXT)"
    )
    con.commit()
    con.close()


def _read_nonempty_lines(path):
    with open(path, "r", encoding="utf8") as inf:
        for line in inf:
            if line.strip():
                yield line


def _fill(mod, db_path):
    field = mod.FIELD
    initTables(mod, db_path)
    with closing(sqlite3.connect(db_path)) as con:
        cursor = con.cursor()

        tokenbag = Counter()
        tokentypesubtypebag = Counter()
        doc_year = {}

        for line in mod.getdoclist(mod.ctsns).split("\n"):
            urn_date = line.split("\t")
            doc_year[urn_date[0]] = urn_date[2]

        for yearfile in sorted(os.listdir(_path(mod, mod.PERYEAR_DIR))):
            print("sql " + mod.PERYEAR_DIR + ":" + yearfile)
            year = yearfile.replace(".txt", "")
            for line in _read_nonempty_lines(_path(mod, mod.PERYEAR_DIR, yearfile)):
                linearr = line.split("\t")
                token, value, wetype, subtype = linearr[:4]
                freq = int(linearr[4])
                tokentypesubtypebag[(token, value, wetype, subtype)] += freq
                tokenbag[(token, value)] += freq
                cursor.execute(
                    f"INSERT INTO token{field}typesubtypedatefrequency"
                    f"(token,{field},type,subtype,date,frequency) VALUES(?,?,?,?,?,?)",
                    (token, value, wetype, subtype, int(year), freq),
                )
            con.commit()

        # An ambiguous "|A|B|" entry counts towards both A and B, so the
        # non-ambiguous totals are only complete after the whole file.
        wb_nonambig = Counter()
        for line in _read_nonempty_lines(_path(mod, mod.MAPPING_DIR, mod.BAG_FILE)):
            value, frequency = line.split("\t")[:2]
            freq = int(frequency)
            cursor.execute(
                f"INSERT INTO {field}frequency({field},frequency,sortkey) "
                "VALUES(?,?,?)",
                (value, freq, dsb_sortkey(value.strip("|"))),
            )
            for part in value.split("|"):
                if part.strip():
                    wb_nonambig[part] += freq

        for part, freq in wb_nonambig.items():
            cursor.execute(
                f"INSERT INTO {field}nonambig({field},frequency,sortkey) "
                "VALUES(?,?,?)",
                ("|" + part + "|", freq, dsb_sortkey(part)),
            )
        con.commit()

        for file in sorted(os.listdir(_path(mod, mod.MAPPING_DIR))):
            if not file.startswith("urn_#_"):
                continue
            print("sql " + mod.MAPPING_DIR + "perurn:" + file)
            bag = "#"
            for line in _read_nonempty_lines(_path(mod, mod.MAPPING_DIR, file)):
                bag += line.split("\t")[1] + "#"
            while "#||#" in bag:
                bag = bag.replace("#||#", "#")
            urn = file.replace(".txt", "").replace("_#_", ":")
            cursor.execute(
                f"INSERT INTO urndate{field}bag(urn,date,{field}bag) VALUES(?,?,?)",
                (urn, doc_year[urn], bag),
            )
        con.commit()

        for (token, value), freq in tokenbag.items():
            cursor.execute(
                f"INSERT INTO {field}tokenfrequency(token,{field},frequency) "
                "VALUES(?,?,?)",
                (token, value, freq),
            )
        con.commit()

        for (token, value, wetype, subtype), freq in tokentypesubtypebag.items():
            cursor.execute(
                f"INSERT INTO token{field}typesubtypefrequency"
                f"(token,{field},type,subtype,frequency) VALUES(?,?,?,?,?)",
                (token, value, wetype, subtype, freq),
            )
        con.commit()


def db(mod):
    """Rebuild the database via a temp file, so a failure keeps the old one."""
    db_path = _path(mod, mod.DB_NAME)
    temp_db_path = db_path + ".tmp"
    try:
        _fill(mod, temp_db_path)
        index(mod, temp_db_path)
        os.replace(temp_db_path, db_path)
    except BaseException:
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
        raise


def main(mod, argv=None):
    mod.load_bagofwords()
    if argv is None:
        argv = sys.argv[1:]
    if len(argv) == 1:
        if argv[0] == "db":
            mod.db()
        elif argv[0] == "collect":
            mod.collect()
    else:
        mod.collect()
        mod.db()
