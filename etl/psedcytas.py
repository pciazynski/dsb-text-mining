import sys
import os
import shutil
import sqlite3
from settings import datadir


def initTables():
    if os.path.exists(datadir + "psedcytas.db"):
        os.remove(datadir + "psedcytas.db")
    con = sqlite3.connect(datadir + "psedcytas.db")
    cursor = con.cursor()
    cursor.execute("CREATE TABLE urls(url VARCHAR(50));")
    cursor.execute("CREATE INDEX urlindex ON urls(url);")
    con.commit()
    con.close()


def main(argv=None):
    os.makedirs(datadir, exist_ok=True)
    initTables()
    con = sqlite3.connect(datadir + "psedcytas.db")
    cursor = con.cursor()

    with open("learn/dnw-audio-urls.txt", "r", encoding="utf8") as inf:
        for line in inf.readlines():
            vals = '"' + line + '"'
            query = "INSERT INTO urls(url) VALUES(" + vals + ")"
            cursor.execute(query)
    con.commit()
    con.close()


if __name__ == "__main__":
    main()
