from urllib.request import urlopen
import sys
import os
import shutil
import sqlite3
from collections import Counter
from settings import count, ctsns, datadir, copyrighttoken, tokenlength
from pythoncts import *
from dsb_collation import dsb_sortkey

lemmabag = {}
bagofwords = {}

MAPPING_DIR = "lemmamapping"
PERYEAR_DIR = "lemmamappingperyear"
DB_NAME = "lemmamapping.db"
LEMMABAG_FILE = "_lemmabag.txt"


def _path(*parts):
    return os.path.join(datadir, *parts)


def load_bagofwords():
    with open(_path("bagofwords", "_all.txt"), "r", encoding="utf8") as bwin:
        for line in bwin:
            token, freq = line.split("\t")[:2]
            bagofwords[token] = int(freq)


def requestctsurl(ns):
    global ctsurl
    if ctsurl:
        return
    if not ns.startswith("urn:cts"):
        ns = "urn:cts:" + ns
    ns = ns.split(":")[2]
    data = urlopen("https://urncts.eu/namespaceresolver/" + ns)
    for line in data:
        ctsurl += line.decode("utf-8")


def tokencheck(token):
    return token in bagofwords


def _attr_value(attrs, name):
    marker = name + '="'
    if marker not in attrs:
        return ""
    return attrs.split(marker)[1].split('"')[0]


def lemmamapping(urn):
    global ctsurl
    requestctsurl(urn)
    res = cts_passage(urn, "&copyrighttoken=" + copyrighttoken)
    wordelements = res.split("<w")
    res = ""
    total = str(len(wordelements))
    for wecount, we in enumerate(wordelements):
        if str(wecount).endswith("00"):
            print("\rItems:" + str(wecount) + "/" + total, sep=" ", end="", flush=True)
        if "</w" not in we:
            continue
        wattr = we.split(">", 1)[0]
        wetype = ""
        subtype = ""
        lemma = ""
        token = (
            we.split(">")[1]
            .split("</")[0]
            .replace('"', " ")
            .replace("'", " ")
            .replace(".", "")
            .strip()
            .lower()
        )
        if not tokencheck(token):
            with open(_path("_ERROR.txt"), "a", encoding="utf8") as errout:
                errout.write(urn + " lemmatisierowasch unknown token " + token + "\n")
            continue
        if 'lemma="' in wattr:
            lemmavalue = (
                _attr_value(wattr, "lemma")
                .replace('"', " ")
                .replace("'", " ")
                .strip()
            )
            if lemmavalue:
                lemma = "|" + lemmavalue + "|"
                lemmabag[lemma] = lemmabag.get(lemma, 0) + 1
        # Keep substring checks: "type=" also matches inside "subtype=".
        if "subtype=" in wattr:
            subtype = wattr.split('subtype="')[1].split('"')[0]
        if "type=" in wattr:
            wetype = wattr.split('type="')[1].split('"')[0]
        if lemma.strip():
            res += token + "\t" + lemma
            if wetype or subtype:
                res += "\t" + wetype + "\t" + subtype
            res += "\n"
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
        print("Bagging " + foldername + ":" + yearfile)
        with open(os.path.join(peryear, yearfile), "r", encoding="utf8") as inf:
            for line in inf:
                linearr = line.split("\t")
                token_lemma = "\t".join(linearr[:4])
                wb[token_lemma] += int(linearr[4])
    with open(os.path.join(foldername, "_all.txt"), "w", encoding="utf8") as outf:
        for token_lemma, value in wb.most_common():
            outf.write(token_lemma + "\t" + str(value) + "\n")


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
            rs = lemmamapping(urn)
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
                count += 1

    process(_path(MAPPING_DIR))
    with open(_path(MAPPING_DIR, LEMMABAG_FILE), "w", encoding="utf8") as outf:
        for token, value in sorted(lemmabag.items(), key=lambda x: x[1], reverse=True):
            if token.strip():
                outf.write(token + "\t" + str(value) + "\n")


def index():
    con = sqlite3.connect(_path(DB_NAME))
    cursor = con.cursor()
    print("Indexing...")
    for sql in (
        "CREATE INDEX tokenindextype ON tokenlemmatypesubtypefrequency(token)",
        "CREATE INDEX lemmaindextype ON tokenlemmatypesubtypefrequency(lemma)",
        "CREATE INDEX subtypeindextype ON tokenlemmatypesubtypefrequency(subtype)",
        "CREATE INDEX tokenindex ON tokenlemmatypesubtypedatefrequency(token)",
        "CREATE INDEX lemmaindex ON tokenlemmatypesubtypedatefrequency(lemma)",
        "CREATE INDEX typeindex ON tokenlemmatypesubtypedatefrequency(type)",
        "CREATE INDEX subtypeindex ON tokenlemmatypesubtypedatefrequency(subtype)",
        "CREATE INDEX dateindex ON tokenlemmatypesubtypedatefrequency(date)",
        "CREATE INDEX lemmafrequencyindex ON lemmafrequency(lemma)",
        "CREATE INDEX lemmafrequencysortkeyindex ON lemmafrequency(sortkey)",
        "CREATE INDEX lemmatokenlemmaindex ON lemmatokenfrequency(lemma)",
        "CREATE INDEX lemmatokentokenindex ON lemmatokenfrequency(token)",
        "CREATE INDEX lemmaurnindex ON urndatelemmabag(urn)",
        "CREATE INDEX urnindex ON urndatelemmabag(lemmabag)",
        "CREATE INDEX urndateindex ON urndatelemmabag(date)",
        "CREATE INDEX lemmanonambiglemma ON lemmanonambig(lemma)",
        "CREATE INDEX lemmanonambigsortkey ON lemmanonambig(sortkey)",
    ):
        cursor.execute(sql)
    con.commit()
    con.close()


def initTables():
    db_path = _path(DB_NAME)
    if os.path.exists(db_path):
        os.remove(db_path)
    con = sqlite3.connect(db_path)
    cursor = con.cursor()
    tl = str(tokenlength)
    cursor.execute(
        "CREATE TABLE urndatelemmabag(urn VARCHAR (50),date DATE,lemmabag text)"
    )
    cursor.execute(
        "CREATE TABLE tokenlemmatypesubtypedatefrequency("
        "token VARCHAR (" + tl + "),"
        "lemma VARCHAR (50),type VARCHAR (10),subtype VARCHAR (10),"
        "date DATE,frequency INTEGER)"
    )
    cursor.execute(
        "CREATE TABLE tokenlemmatypesubtypefrequency("
        "token VARCHAR (" + tl + "),"
        "lemma VARCHAR (50),type VARCHAR (10),subtype VARCHAR (10),"
        "frequency INTEGER)"
    )
    cursor.execute(
        "CREATE TABLE lemmafrequency(lemma VARCHAR (50),frequency INTEGER,sortkey TEXT)"
    )
    cursor.execute(
        "CREATE TABLE lemmatokenfrequency("
        "lemma VARCHAR (50),token VARCHAR (" + tl + "),frequency INTEGER)"
    )
    cursor.execute(
        "CREATE TABLE lemmanonambig(lemma VARCHAR (50),frequency INTEGER,sortkey TEXT)"
    )
    con.commit()
    con.close()


def _read_nonempty_lines(path):
    with open(path, "r", encoding="utf8") as inf:
        for line in inf:
            if line.strip():
                yield line


def db():
    initTables()
    con = sqlite3.connect(_path(DB_NAME))
    cursor = con.cursor()

    lemmatokenbag = Counter()
    lemmatokentypesubtypebag = Counter()
    doc_year = {}

    for line in getdoclist(ctsns).split("\n"):
        urn_date = line.split("\t")
        doc_year[urn_date[0]] = urn_date[2]

    for yearfile in sorted(os.listdir(_path(PERYEAR_DIR))):
        print("sql lemmamappingperyear:" + yearfile)
        year = yearfile.replace(".txt", "")
        for line in _read_nonempty_lines(_path(PERYEAR_DIR, yearfile)):
            linearr = line.split("\t")
            token, lemma, wetype, subtype = linearr[0], linearr[1], linearr[2], linearr[3]
            freq = int(linearr[4])
            lemmatokentypesubtypebag["\t".join((token, lemma, wetype, subtype))] += freq
            lemmatokenbag[token + "\t" + lemma] += freq
            cursor.execute(
                "INSERT INTO tokenlemmatypesubtypedatefrequency"
                "(token,lemma,type,subtype,date,frequency) VALUES(?,?,?,?,?,?)",
                (token, lemma, wetype, subtype, int(year), freq),
            )
        con.commit()

    for line in _read_nonempty_lines(_path(MAPPING_DIR, LEMMABAG_FILE)):
        linearr = line.split("\t")
        lemma = linearr[0]
        freq = int(linearr[1].strip())
        cursor.execute(
            "INSERT INTO lemmafrequency(lemma,frequency,sortkey) VALUES(?,?,?)",
            (lemma, freq, dsb_sortkey(lemma.strip("|"))),
        )
    con.commit()

    wb_nonambig = Counter()
    for line in _read_nonempty_lines(_path(MAPPING_DIR, LEMMABAG_FILE)):
        linearr = line.split("\t")
        freq = int(linearr[1])
        for lemma in linearr[0].split("|"):
            if lemma.strip():
                wb_nonambig[lemma] += freq

    for lemma, freq in wb_nonambig.items():
        cursor.execute(
            "INSERT INTO lemmanonambig(lemma,frequency,sortkey) VALUES(?,?,?)",
            ("|" + lemma + "|", freq, dsb_sortkey(lemma)),
        )
    con.commit()

    for file in sorted(os.listdir(_path(MAPPING_DIR))):
        if not file.startswith("urn_#_"):
            continue
        print("sql lemmamappingperurn:" + file)
        bag = "#"
        for line in _read_nonempty_lines(_path(MAPPING_DIR, file)):
            bag += line.split("\t")[1] + "#"
        while "#||#" in bag:
            bag = bag.replace("#||#", "#")
        urn = file.replace(".txt", "").replace("_#_", ":")
        cursor.execute(
            "INSERT INTO urndatelemmabag(urn,date,lemmabag) VALUES(?,?,?)",
            (urn, doc_year[urn], bag),
        )
    con.commit()

    for key, freq in lemmatokenbag.items():
        token, lemma = key.split("\t", 1)
        cursor.execute(
            "INSERT INTO lemmatokenfrequency(token,lemma,frequency) VALUES(?,?,?)",
            (token, lemma, freq),
        )
    con.commit()

    for key, freq in lemmatokentypesubtypebag.items():
        token, lemma, wetype, subtype = key.split("\t")
        cursor.execute(
            "INSERT INTO tokenlemmatypesubtypefrequency"
            "(token,lemma,type,subtype,frequency) VALUES(?,?,?,?,?)",
            (token, lemma, wetype, subtype, freq),
        )
    con.commit()
    con.close()

    index()


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
