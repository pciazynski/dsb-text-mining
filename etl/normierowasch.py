import sys
import os
import shutil
import sqlite3
from collections import Counter
from contextlib import closing
from settings import count, ctsns, datadir, copyrighttoken, tokenlength
from pythoncts import *
from dsb_collation import dsb_sortkey

normbag = {}
bagofwords = {}

MAPPING_DIR = "normmapping"
PERYEAR_DIR = "normmappingperyear"
DB_NAME = "normmapping.db"
NORMBAG_FILE = "_normbag.txt"


def _path(*parts):
    return os.path.join(datadir, *parts)


def load_bagofwords():
    with open(_path("bagofwords", "_all.txt"), "r", encoding="utf8") as bwin:
        for line in bwin:
            token, freq = line.split("\t")[:2]
            bagofwords[token] = int(freq)


def tokencheck(token):
    return token in bagofwords


def _attr_value(attrs, name):
    marker = " " + name + '="'
    if marker not in attrs:
        return ""
    return attrs.split(marker, 1)[1].split('"', 1)[0]


def normmapping(urn):
    res = cts_passage(urn, "&copyrighttoken=" + copyrighttoken)
    wordelements = res.split("<w")
    total = str(len(wordelements))
    res = ""
    for wecount, we in enumerate(wordelements):
        if str(wecount).endswith("00"):
            print("\rItems:" + str(wecount) + "/" + total, sep=" ", end="", flush=True)
        if "</w" not in we:
            continue
        word_attributes, word_content = we.split(">", 1)
        token = (
            word_content.split("</", 1)[0]
            .replace('"', " ")
            .replace("'", " ")
            .replace(".", "")
            .strip()
            .lower()
        )
        if not tokencheck(token):
            with open(_path("_ERROR.txt"), "a", encoding="utf8") as errout:
                errout.write(urn + " normierowasch unknown token " + token + "\n")
            continue
        normvalue = _attr_value(word_attributes, "norm")
        if not normvalue:
            continue
        norm = "|" + normvalue + "|"
        normbag[norm] = normbag.get(norm, 0) + 1
        wetype = _attr_value(word_attributes, "type")
        subtype = _attr_value(word_attributes, "subtype")
        res += "\t".join([token, norm, wetype, subtype]) + "\n"
    print("\rOK                                       ")
    return res


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
        for token_norm, value in wb.most_common():
            outf.write(token_norm + "\t" + str(value) + "\n")


def reset():
    os.makedirs(datadir, exist_ok=True)
    for name in (MAPPING_DIR, PERYEAR_DIR):
        path = _path(name)
        if os.path.exists(path):
            shutil.rmtree(path)
        os.mkdir(path)


def getdoclist(ctsns):
    if os.path.exists("urnlist.txt"):
        with open("urnlist.txt", "r", encoding="utf8") as inf:
            return inf.read().strip()
    return cts_inventory(ctsns).strip()


def collect():
    global count
    reset()
    print("Collect...")
    doclist = getdoclist(ctsns).split("\n")
    if count == -1:
        count = len(doclist)
    for line in doclist:
        parts = line.split("\t")
        urn = parts[0]
        year = parts[2]

        if len(year) > 1 and count > 0:
            print(str(count) + " " + urn)
            count -= 1
            rs = normmapping(urn)
            if rs.strip():
                urn_path = _path(MAPPING_DIR, urn.replace(":", "_#_") + ".txt")
                year_path = _path(PERYEAR_DIR, year + ".txt")
                with (
                    open(urn_path, "w", encoding="utf8") as outf,
                    open(year_path, "a", encoding="utf8") as outyf,
                ):
                    outf.write(rs)
                    outyf.write(rs)
            else:
                print("No Items")

    process(_path(MAPPING_DIR))
    with open(_path(MAPPING_DIR, NORMBAG_FILE), "w", encoding="utf8") as outf:
        for token, value in sorted(normbag.items(), key=lambda x: x[1], reverse=True):
            if token.strip():
                outf.write(token + "\t" + str(value) + "\n")


def index(db_path=None):
    db_path = db_path or _path(DB_NAME)
    con = sqlite3.connect(db_path)
    cursor = con.cursor()
    print("Indexing...")
    for sql in (
        "CREATE INDEX tokenindextype ON tokennormtypesubtypefrequency(token)",
        "CREATE INDEX normindextype ON tokennormtypesubtypefrequency(norm)",
        "CREATE INDEX typeindextype ON tokennormtypesubtypefrequency(type)",
        "CREATE INDEX subtypeindextype ON tokennormtypesubtypefrequency(subtype)",
        "CREATE INDEX tokenindex ON tokennormtypesubtypedatefrequency(token)",
        "CREATE INDEX normindex ON tokennormtypesubtypedatefrequency(norm)",
        "CREATE INDEX typeindex ON tokennormtypesubtypedatefrequency(type)",
        "CREATE INDEX subtypeindex ON tokennormtypesubtypedatefrequency(subtype)",
        "CREATE INDEX dateindex ON tokennormtypesubtypedatefrequency(date)",
        "CREATE INDEX normfrequencyindex ON normfrequency(norm)",
        "CREATE INDEX normfrequencysortkeyindex ON normfrequency(sortkey)",
        "CREATE INDEX normtokenindex ON normtokenfrequency(norm)",
        "CREATE INDEX normtokentokenindex ON normtokenfrequency(token)",
        "CREATE INDEX normurnindex ON urndatenormbag(urn)",
        "CREATE INDEX urnindex ON urndatenormbag(normbag)",
        "CREATE INDEX urndateindex ON urndatenormbag(date)",
        "CREATE INDEX normnonambignorm ON normnonambig(norm)",
        "CREATE INDEX normnonambigsortkey ON normnonambig(sortkey)",
    ):
        cursor.execute(sql)
    con.commit()
    con.close()


def initTables(db_path=None):
    db_path = db_path or _path(DB_NAME)
    if os.path.exists(db_path):
        os.remove(db_path)
    con = sqlite3.connect(db_path)
    cursor = con.cursor()
    tl = str(tokenlength)
    cursor.execute(
        "CREATE TABLE urndatenormbag(urn VARCHAR (50),date DATE,normbag text)"
    )
    cursor.execute(
        "CREATE TABLE tokennormtypesubtypedatefrequency("
        "token VARCHAR (" + tl + "),"
        "norm VARCHAR (50),type VARCHAR (10),subtype VARCHAR (10),"
        "date DATE,frequency INTEGER)"
    )
    cursor.execute(
        "CREATE TABLE tokennormtypesubtypefrequency("
        "token VARCHAR (" + tl + "),"
        "norm VARCHAR (50),type VARCHAR (10),subtype VARCHAR (10),"
        "frequency INTEGER)"
    )
    cursor.execute(
        "CREATE TABLE normfrequency(norm VARCHAR (50),frequency INTEGER,sortkey TEXT)"
    )
    cursor.execute(
        "CREATE TABLE normtokenfrequency("
        "norm VARCHAR (50),token VARCHAR (" + tl + "),frequency INTEGER)"
    )
    cursor.execute(
        "CREATE TABLE normnonambig(norm VARCHAR (50),frequency INTEGER,sortkey TEXT)"
    )
    con.commit()
    con.close()


def _read_nonempty_lines(path):
    with open(path, "r", encoding="utf8") as inf:
        for line in inf:
            if line.strip():
                yield line


def _fill(db_path):
    initTables(db_path)
    with closing(sqlite3.connect(db_path)) as con:
        cursor = con.cursor()

        normtokenbag = Counter()
        tokennormtypesubtypebag = Counter()
        doc_year = {}

        for line in getdoclist(ctsns).split("\n"):
            urn_date = line.split("\t")
            doc_year[urn_date[0]] = urn_date[2]

        for yearfile in sorted(os.listdir(_path(PERYEAR_DIR))):
            print("sql normmappingperyear:" + yearfile)
            year = yearfile.replace(".txt", "")
            for line in _read_nonempty_lines(_path(PERYEAR_DIR, yearfile)):
                linearr = line.split("\t")
                token, norm, wetype, subtype = linearr[:4]
                freq = int(linearr[4])
                tokennormtypesubtypebag[(token, norm, wetype, subtype)] += freq
                normtokenbag[(token, norm)] += freq
                cursor.execute(
                    "INSERT INTO tokennormtypesubtypedatefrequency"
                    "(token,norm,type,subtype,date,frequency) VALUES(?,?,?,?,?,?)",
                    (token, norm, wetype, subtype, int(year), freq),
                )
            con.commit()

        # An ambiguous "|A|B|" entry counts towards both A and B, so the
        # non-ambiguous totals are only complete after the whole file.
        wb_nonambig = Counter()
        for line in _read_nonempty_lines(_path(MAPPING_DIR, NORMBAG_FILE)):
            norm, frequency = line.split("\t")[:2]
            freq = int(frequency)
            cursor.execute(
                "INSERT INTO normfrequency(norm,frequency,sortkey) VALUES(?,?,?)",
                (norm, freq, dsb_sortkey(norm.strip("|"))),
            )
            for part in norm.split("|"):
                if part.strip():
                    wb_nonambig[part] += freq

        for norm, freq in wb_nonambig.items():
            cursor.execute(
                "INSERT INTO normnonambig(norm,frequency,sortkey) VALUES(?,?,?)",
                ("|" + norm + "|", freq, dsb_sortkey(norm)),
            )
        con.commit()

        for file in sorted(os.listdir(_path(MAPPING_DIR))):
            if not file.startswith("urn_#_"):
                continue
            print("sql normmappingperurn:" + file)
            bag = "#"
            for line in _read_nonempty_lines(_path(MAPPING_DIR, file)):
                bag += line.split("\t")[1] + "#"
            while "#||#" in bag:
                bag = bag.replace("#||#", "#")
            urn = file.replace(".txt", "").replace("_#_", ":")
            cursor.execute(
                "INSERT INTO urndatenormbag(urn,date,normbag) VALUES(?,?,?)",
                (urn, doc_year[urn], bag),
            )
        con.commit()

        for (token, norm), freq in normtokenbag.items():
            cursor.execute(
                "INSERT INTO normtokenfrequency(token,norm,frequency) VALUES(?,?,?)",
                (token, norm, freq),
            )
        con.commit()

        for (token, norm, wetype, subtype), freq in tokennormtypesubtypebag.items():
            cursor.execute(
                "INSERT INTO tokennormtypesubtypefrequency"
                "(token,norm,type,subtype,frequency) VALUES(?,?,?,?,?)",
                (token, norm, wetype, subtype, freq),
            )
        con.commit()


def db():
    """Rebuild the database via a temp file, so a failure keeps the old one."""
    db_path = _path(DB_NAME)
    temp_db_path = db_path + ".tmp"
    try:
        _fill(temp_db_path)
        index(temp_db_path)
        os.replace(temp_db_path, db_path)
    except BaseException:
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
        raise


def main(argv=None):
    load_bagofwords()
    if argv is None:
        argv = sys.argv[1:]
    if len(argv) == 1:
        if argv[0] == "db":
            db()
        elif argv[0] == "collect":
            collect()
    else:
        collect()
        db()


if __name__ == "__main__":
    main()
