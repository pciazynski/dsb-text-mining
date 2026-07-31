import sys
import os
import shutil
import sqlite3
from settings import count, ctsns, datadir
from pythoncts import *
from dsb_collation import dsb_sortkey

doc_year = {}


def normalize_token(token):
    return token.lower()


def normalize_response(response):
    if response is None:
        return None

    if response.endswith(("\n", "\r")):
        return None

    normalized_lines = []
    for line in response.splitlines():
        if not line.strip():
            return None
        fields = line.split("\t")
        if len(fields) != 2:
            return None

        token = normalize_token(fields[0])
        frequency_text = fields[1].strip()
        if not token or not frequency_text:
            return None

        try:
            frequency = int(frequency_text)
        except ValueError:
            return None

        if frequency < 1:
            return None

        normalized_lines.append(f"{token}\t{frequency}")

    if not normalized_lines:
        return None
    return "\n".join(normalized_lines)


def process(foldername):
    tokensumperyear = {}
    typesumperyear = {}
    for yearfile in sorted(os.listdir(foldername + "peryear")):
        print("process " + foldername + ":" + yearfile)
        wb = dict()
        with open(foldername + "peryear/" + yearfile, "r", encoding="utf8") as inf:
            for line in inf:
                linearr = line.rstrip("\n").split("\t")
                token = normalize_token(linearr[0])
                if token in wb:
                    wb[token] = wb[token] + int(linearr[1])
                else:
                    wb[token] = int(linearr[1])
        with open(foldername + "peryear/" + yearfile, "w", encoding="utf8") as outf:
            for token, value in sorted(wb.items(), key=lambda x: x[1], reverse=True):
                outf.write(token + "\t" + str(value) + "\n")

    wb = dict()
    for yearfile in sorted(os.listdir(foldername + "peryear")):
        with open(foldername + "peryear/" + yearfile, "r", encoding="utf8") as inf:
            year = int(yearfile.replace(".txt", ""))
            for line in inf:
                linearr = line.rstrip("\n").split("\t")
                token = normalize_token(linearr[0])
                if year in tokensumperyear:
                    tokensumperyear[year] = tokensumperyear[year] + int(linearr[1])
                    typesumperyear[year] = typesumperyear[year] + 1
                else:
                    tokensumperyear[year] = int(linearr[1])
                    typesumperyear[year] = 1

                if token in wb:
                    wb[token] = wb[token] + int(linearr[1])
                else:
                    wb[token] = int(linearr[1])
    with open(foldername + "/_all.txt", "w", encoding="utf8") as outf:
        for token, value in sorted(wb.items(), key=lambda x: x[1], reverse=True):
            outf.write(token + "\t" + str(value) + "\n")
    with open(foldername + "/_tokensumperyear.txt", "w", encoding="utf8") as outf:
        for year, value in sorted(tokensumperyear.items()):
            outf.write(str(year) + "\t" + str(value) + "\n")
    with open(foldername + "/_typesumperyear.txt", "w", encoding="utf8") as outf:
        for year, value in sorted(typesumperyear.items()):
            outf.write(str(year) + "\t" + str(value) + "\n")
    with open(foldername + "/_typetokenratioperyear.txt", "w", encoding="utf8") as outf:
        for year, value in sorted(typesumperyear.items()):
            outf.write(
                str(year)
                + "\t"
                + str(typesumperyear[year] / tokensumperyear[year])
                + "\n"
            )

    wb_max = dict()
    wb_min = dict()
    for yearfile in sorted(os.listdir(foldername + "peryear")):
        with open(foldername + "peryear/" + yearfile, "r", encoding="utf8") as inf:
            for line in inf:
                year = int(yearfile.replace(".txt", ""))
                token = normalize_token(line.split("\t")[0])
                if token in wb_max:
                    if year > wb_max[token]:
                        wb_max[token] = year
                else:
                    wb_max[token] = year
                if token in wb_min:
                    if year < wb_min[token]:
                        wb_min[token] = year
                else:
                    wb_min[token] = year
    with open(foldername + "/_minmaxyearzipf.txt", "w", encoding="utf8") as outf:
        for token, value in sorted(wb.items(), key=lambda x: x[1], reverse=True):
            outf.write(
                token
                + "\t"
                + str(wb_min[token])
                + "\t"
                + str(wb_max[token])
                + "\t"
                + str(value)
                + "\n"
            )
    daterange = {}
    for token, value in sorted(wb_min.items(), key=lambda x: x[1], reverse=False):
        drange = str(wb_min[token]) + "\t" + str(wb_max[token])
        if not drange in daterange:
            daterange[drange] = token
        else:
            daterange[drange] = daterange[drange] + "," + token
    with open(foldername + "/_minmaxyearmin.txt", "w", encoding="utf8") as outf:
        for key in daterange:
            outf.write(key + "\t" + daterange[key] + "\n")

    daterange = {}
    for token, value in sorted(wb_max.items(), key=lambda x: x[1], reverse=False):
        drange = str(wb_min[token]) + "\t" + str(wb_max[token])
        if not drange in daterange:
            daterange[drange] = token
        else:
            daterange[drange] = daterange[drange] + "," + token
    with open(foldername + "/_minmaxyearmax.txt", "w", encoding="utf8") as outf:
        for key in daterange:
            outf.write(key + "\t" + daterange[key] + "\n")


def sanitycheck(response):
    return normalize_response(response) is not None


def reset():
    print("Reset")
    if not os.path.exists(datadir):
        os.makedirs(datadir, exist_ok=True)
    if os.path.exists(datadir + "bagofwords"):
        shutil.rmtree(datadir + "bagofwords")
    os.mkdir(datadir + "bagofwords")
    if os.path.exists(datadir + "bagofwordsperyear"):
        shutil.rmtree(datadir + "bagofwordsperyear")
    os.mkdir(datadir + "bagofwordsperyear")


def getdoclist(ctsns):
    tmplist = ""
    if os.path.exists("urnlist.txt"):
        with open("urnlist.txt", "r", encoding="utf8") as inf:
            for line in inf:
                tmplist += line
    else:
        tmplist = cts_inventory(ctsns)
    return tmplist.strip()


def collect():
    global count
    reset()
    print("Collect...")
    doclist = getdoclist(ctsns).split("\n")
    if count == -1:
        count = len(doclist)
    for line in doclist:
        if not line.strip():
            continue

        inventory_fields = line.split("\t")
        if len(inventory_fields) < 3:
            continue

        urn = inventory_fields[0].strip()
        year = inventory_fields[2].strip()
        try:
            year_value = int(year)
        except ValueError:
            continue

        response = cts_bagofwords(urn)
        normalized_response = normalize_response(response)
        if normalized_response is None:
            with open(datadir + "_ERROR.txt", "a", encoding="utf8") as errf:
                errf.write("Error Bagofwords:-->" + urn + "\n")
            continue

        if count != 0:
            doc_year[urn] = year_value
            print(str(count) + " " + urn)
            count -= 1
            with (
                open(
                    datadir + "bagofwords/" + urn.replace(":", "_#_") + ".txt",
                    "w",
                    encoding="utf8",
                ) as outf,
                open(
                    os.path.join(
                        datadir + "bagofwordsperyear", str(year_value) + ".txt"
                    ),
                    "a",
                    encoding="utf8",
                ) as outyf,
            ):
                outf.write(normalized_response)
                outyf.write(normalized_response + "\n")
    process(datadir + "bagofwords")


def initTables():
    if os.path.exists(datadir + "bagofwords.db"):
        os.remove(datadir + "bagofwords.db")
    con = sqlite3.connect(datadir + "bagofwords.db")
    cursor = con.cursor()
    cursor.execute(
        "CREATE TABLE tokendatecount(token VARCHAR (50),date DATE,frequency INTEGER);"
    )
    cursor.execute(
        "CREATE TABLE tokencount(token VARCHAR (50),frequency INTEGER,sortkey TEXT);"
    )
    cursor.execute(
        "CREATE TABLE urndatewordbag(urn VARCHAR (50),date DATE,wordbag text);"
    )
    con.commit()
    con.close()


def index():
    con = sqlite3.connect(datadir + "bagofwords.db")
    cursor = con.cursor()
    print("Indexing...")
    cursor.execute("CREATE INDEX tokenindex ON tokencount(token);")
    cursor.execute("CREATE INDEX tokensortkeyindex ON tokencount(sortkey);")
    cursor.execute("CREATE INDEX tokendateindex ON tokendatecount(token);")
    cursor.execute("CREATE INDEX dateindex ON tokendatecount(date);")
    cursor.execute("CREATE INDEX tokenurnindex ON urndatewordbag(urn);")
    cursor.execute("CREATE INDEX urnindex ON urndatewordbag(wordbag);")
    cursor.execute("CREATE INDEX urndateindex ON urndatewordbag(date);")
    con.commit()
    con.close()


def db():
    print("DB...")
    initTables()
    con = sqlite3.connect(datadir + "bagofwords.db")
    cursor = con.cursor()

    doclist = getdoclist(ctsns).split("\n")
    for line in doclist:
        urn_date = line.split("\t")
        doc_year[urn_date[0]] = urn_date[2]

    with open(datadir + "bagofwords/_all.txt", "r", encoding="utf8") as inf:
        for line in inf.readlines():
            if len(line.strip()) > 0:
                linearr = line.rstrip("\n").split("\t")
                token = linearr[0]
                frequency = int(linearr[1])
                cursor.execute(
                    "INSERT INTO tokencount(token,frequency,sortkey) VALUES(?,?,?)",
                    (token, frequency, dsb_sortkey(token)),
                )
    con.commit()

    yearfiles = sorted(os.listdir(datadir + "bagofwordsperyear"))
    for year in yearfiles:
        # print("sql bagofwordsperyear:"+year)

        with open(datadir + "bagofwordsperyear/" + year, "r", encoding="utf8") as inf:
            for line in inf.readlines():
                if len(line.strip()) > 0:
                    linearr = line.rstrip("\n").split("\t")
                    token = linearr[0]
                    date = int(year.replace(".txt", ""))
                    frequency = int(linearr[1])
                    cursor.execute(
                        "INSERT INTO tokendatecount(token,date,frequency) VALUES(?,?,?)",
                        (token, date, frequency),
                    )
        con.commit()

    files = sorted(os.listdir(datadir + "bagofwords"))
    for file in files:
        if file.startswith("urn_#_"):
            # print("sql bagofwordsperurn:"+file)
            with open(datadir + "bagofwords/" + file, "r", encoding="utf8") as inf:
                wordbag = "|"
                for line in inf.readlines():
                    if len(line.strip()) > 0:
                        wordbag += line.split("\t")[0] + "|"
                urn = file.replace(".txt", "").replace("_#_", ":")
                year = doc_year[urn]
                cursor.execute(
                    "INSERT INTO urndatewordbag(urn,date,wordbag) VALUES(?,?,?)",
                    (urn, year, wordbag),
                )
        con.commit()
    index()


def main(argv=None):
    print("Bagofwords")
    if argv is None:
        argv = sys.argv[1:]
    if len(argv) == 1:
        if argv[0] == "db":
            print("DB")
            db()
        elif argv[0] == "collect":
            print("Collect")
            collect()
    else:
        print("Collect & DB")
        collect()
        db()


if __name__ == "__main__":
    main()
