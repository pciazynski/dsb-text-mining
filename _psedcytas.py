import sys
import os
import shutil
import sqlite3
from config import *


if not os.path.exists("data"):
    os.mkdir("data")
    
def initTables():
    if os.path.exists("data/psedcytas.db"):
        os.remove("data/psedcytas.db")
    con = sqlite3.connect("data/psedcytas.db")
    cursor = con.cursor()
    cursor.execute("CREATE TABLE urls(url VARCHAR(50));")
    cursor.execute("CREATE INDEX urlindex ON urls(url);")
    con.commit()
    con.close()
    
initTables()
con = sqlite3.connect("data/psedcytas.db")
cursor = con.cursor()

with open ("learn/dnw-audio-urls.txt", "r", encoding="utf8") as inf:
    for line in inf.readlines():
        vals = '"'+line+'"'
        query="INSERT INTO urls(url) VALUES("+vals+")"
        cursor.execute(query)
con.commit()


