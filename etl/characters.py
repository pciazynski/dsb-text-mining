import os
import shutil
import sys
import sqlite3

from settings import count, ctsns, datadir, copyrighttoken, tokenlength
from pythoncts import *


doc_year = {}

def getdoclist(ctsns):
    tmplist = ""
    if os.path.exists("urnlist.txt"):
        with open("urnlist.txt","r",encoding="utf8") as inf:
            for line in inf:
                tmplist+=line
    else:
        tmplist = cts_inventory(ctsns)
    return tmplist.strip()

doclist = getdoclist(ctsns).split("\n")

def process(foldername):
    global doclist
    for line in doclist:
        urn = line.split("\t")[0]
        year = line.split("\t")[2]
        doc_year[urn] = year
    
    for yearfile in sorted(os.listdir(foldername+"peryear")):
        #print("process "+foldername+":"+yearfile)
        wb = dict()
        with open (foldername+"peryear/"+yearfile, "r", encoding="utf8") as inf:
            for line in inf:
                linearr=line.split("\t")
                char = linearr[0]
                if char in wb:
                    wb[char] = wb[char] + int(linearr[1])
                else:
                    wb[char] = int(linearr[1])
        with open (foldername+"peryear/"+yearfile, "w", encoding="utf8") as outf:
            for char,value in sorted(wb.items(), key = lambda x:x[1], reverse=True):
                outf.write(char+"\t"+str(value)+"\n")
            
            
    wb = dict()
    for yearfile in sorted(os.listdir(foldername+"peryear")):
        with open (foldername+"peryear/"+yearfile, "r", encoding="utf8") as inf:
            for line in inf:
                linearr=line.split("\t")
                char = linearr[0]
                if char in wb:
                    wb[char] = wb[char] + int(linearr[1])
                else:
                    wb[char] = int(linearr[1])

    with open (foldername+"/_all.txt", "w", encoding="utf8") as outf:
        for char,value in sorted(wb.items(), key = lambda x:x[1], reverse=True):
            outf.write(char+"\t"+str(value)+"\n")

def initTables():
    if os.path.exists(datadir + "characters.db"):
        os.remove(datadir + "characters.db")
    con = sqlite3.connect(datadir + "characters.db")
    cursor = con.cursor()
    cursor.execute("CREATE TABLE chardatecount(char VARCHAR (2),date DATE,frequency INTEGER);")
    cursor.execute("CREATE TABLE charcount(char VARCHAR (2),frequency INTEGER);")
    cursor.execute("CREATE TABLE urncharbag(urn VARCHAR (50),date DATE,charbag text);")
    con.commit()
    con.close()

def index():
    con = sqlite3.connect(datadir + "characters.db")
    cursor = con.cursor()
    print("Indexing...")
    cursor.execute("CREATE INDEX charindex ON charcount(char);")
    cursor.execute("CREATE INDEX chardateindex ON chardatecount(char);")
    cursor.execute("CREATE INDEX chardatedateindex ON chardatecount(date);")
    cursor.execute("CREATE INDEX charurnindex ON urncharbag(urn);")
    cursor.execute("CREATE INDEX urnindex ON urncharbag(charbag);")
    cursor.execute("CREATE INDEX urndateindex ON urncharbag(date);")
    con.commit()
    con.close()

def db():
    print("DB...")
    initTables()
    con = sqlite3.connect(datadir + "characters.db")
    cursor = con.cursor()

    with open (datadir + "characters/_all.txt", "r", encoding="utf8") as inf:
        for line in inf.readlines():
            if len(line.strip())>0:
                linearr = line.split("\t")
                vals = '"'+linearr[0]+'",'+linearr[1]
                query="INSERT INTO charcount(char,frequency) VALUES("+vals+")"
                cursor.execute(query)
    con.commit()
        
    yearfiles = sorted(os.listdir(datadir + "charactersperyear"))
    for year in yearfiles:
        #print("sql bagofwordsperyear:"+year)
        with open (datadir + "charactersperyear/"+year, "r", encoding="utf8") as inf:
            for line in inf.readlines():
                if len(line.strip())>0:
                    linearr = line.split("\t")
                    vals = '"'+linearr[0]+'",'+year.replace(".txt","")+','+linearr[1]
                    query="INSERT INTO chardatecount(char,date,frequency) VALUES("+vals+")"
                    cursor.execute(query)
        con.commit()
        
    files = sorted(os.listdir(datadir + "characters"))
    for file in files:
        if file.startswith("urn_#_"):
            #print("sql bagofwordsperurn:"+file)
            with open (datadir + "characters/"+file, "r", encoding="utf8") as inf:
                charbag = "|"
                for line in inf.readlines():
                    if len(line.strip())>0:
                        charbag += line.split("\t")[0]+"|"
                urn = file.replace(".txt","").replace("_#_",":")
                year = doc_year[urn]
                vals = '"'+urn+'","'+year+'","'+charbag+'"'
                query="INSERT INTO urncharbag(urn,date,charbag) VALUES("+vals+")"
                cursor.execute(query)
        con.commit()
    index()

def listcharacters(file):

    charcount = {}
    with open (file, "r", encoding="utf8") as f:
        for line in f:
            linearr = line.split("\t")
            token = linearr[0]
            count = int(linearr[1])
            for char in token:
                if char in charcount:
                    charcount[char] = charcount[char] + count
                else:
                    charcount[char] = count

    with open (file.replace("bagofwords","characters"), "w", encoding="utf8") as f:
        for char,value in sorted(charcount.items(), key = lambda x:x[1], reverse=True):
            f.write(char+"\t"+str(value)+"\n")

def collect():
    if os.path.exists(datadir + "characters"):
        shutil.rmtree(datadir + "characters")
    os.mkdir(datadir + "characters")

    if os.path.exists(datadir + "charactersperyear"):
        shutil.rmtree(datadir + "charactersperyear")
    os.mkdir(datadir + "charactersperyear")

    listcharacters(datadir + "bagofwords/_all.txt")
    for file in os.listdir(datadir + "bagofwords/"):
        if file.startswith("urn_#_"):
            listcharacters(datadir + "bagofwords/"+file)
    for file in os.listdir(datadir + "bagofwordsperyear/"):
        listcharacters(datadir + "bagofwordsperyear/"+file)
            
    process(datadir + "characters")

if len(sys.argv)==2:
    if sys.argv[1] == "db":
        db()
    else:
        if sys.argv[1] == "collect":
            collect()
else:
    collect()
    db()
    
