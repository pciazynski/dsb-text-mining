
import sys
import os
import shutil
import sqlite3
from config import *
from pythoncts import *


def reset():
    print("Reset")
    if not os.path.exists("data"):
        os.mkdir("data")
    if os.path.exists("data/metadata"):
        shutil.rmtree("data/metadata")
    os.mkdir("data/metadata")

def getdoclist(ctsns):
    tmplist = ""
    if os.path.exists("urnlist.txt"):
        with open("urnlist.txt","r",encoding="utf8") as inf:
            for line in inf:
                tmplist+=line
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
    with open("data/metadata/_all.txt", "w",encoding="utf8") as outf:
        for line in doclist:
            urn = line.split("\t")[0]
            year = line.split("\t")[2]

            if (len(year)>1 and count!=0):
                outf.write(line+"\n")
                count-=1

def initTables():
    if os.path.exists("data/metadata.db"):
        os.remove("data/metadata.db")
    con = sqlite3.connect("data/metadata.db")
    cursor = con.cursor()
    cursor.execute("CREATE TABLE docmeta(urn VARCHAR (50), title VARCHAR (50), author VARCHAR (50), restricted BOOLEAN, date INTEGER, lang VARCHAR(50));")
    con.commit()
    con.close()

def index():
    con = sqlite3.connect("data/metadata.db")
    cursor = con.cursor()
    print("Indexing...")
    cursor.execute("CREATE INDEX docmetaurnindex ON docmeta(urn);")
    cursor.execute("CREATE INDEX docmetadateindex ON docmeta(date);")
    cursor.execute("CREATE INDEX docmetaauthorindex ON docmeta(author);")
    cursor.execute("CREATE INDEX docmetatitleindex ON docmeta(title);")
    cursor.execute("CREATE INDEX docmetarestrindex ON docmeta(restricted);")
    cursor.execute("CREATE INDEX docmetalangndex ON docmeta(lang);")
    con.commit()
    con.close()

def db():
    print("DB...")
    initTables()
    con = sqlite3.connect("data/metadata.db")
    cursor = con.cursor()
    with open("data/metadata/_all.txt", "r",encoding="utf8") as inf:
        for line in inf:
            query = "INSERT INTO docmeta(urn,title,date,author,restricted,lang) VALUES(?,?,?,?,?,?)"
            values = ['','','','','','']
            tmp = line.strip("\n").split("\t")
            counter = 0
            for key in tmp:
                values[counter] = key
                counter+=1
            cursor.execute(query,values)

    con.commit()
    con.close()
    index()

print("Metadata")
if len(sys.argv)==2:
    if sys.argv[1] == "db":
        print("DB")
        db()
    else:
        if sys.argv[1] == "collect":
            print("Collect")
            collect()
else:
    print("Collect & DB")
    collect()
    db()
    
