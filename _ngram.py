import sys
import os
import shutil
import sqlite3
import sys
from config import *
from pythoncts import *

n=sys.argv[1]
bagofwords = {}

def getdoclist(ctsns):
    tmplist = ""
    if os.path.exists("urnlist.txt"):
        with open("urnlist.txt","r",encoding="utf8") as inf:
            for line in inf:
                tmplist+=line
    else:
        tmplist = cts_inventory(ctsns)
    return tmplist.strip()
    
with open("data/bagofwords/_all.txt", "r", encoding = "utf8") as bwin:
    for line in bwin:
        linearr = line.split("\t")
        bagofwords[linearr[0]] = int(linearr[1])

def tokencheck(line):
    linearr = line.split("\t")[0].split(" ")
    for token in linearr:
        if not token.strip() in bagofwords:
            return False
    return True
    
def process(foldername):
    for yearfile in sorted(os.listdir(foldername+"peryear")):
        print("process "+foldername+":"+yearfile)
        wb = dict()
        with open (foldername+"peryear/"+yearfile, "r", encoding="utf8") as inf:
            for line in inf:
                if len(line.strip())>0:
                    linearr=line.split("\t")
                    token = linearr[0]
                    if token in wb:
                        wb[token] = wb[token] + int(linearr[1])
                    else:
                        wb[token] = int(linearr[1])
        with open (foldername+"peryear/"+yearfile, "w", encoding="utf8") as outf:
            for token,value in sorted(wb.items(), key = lambda x:x[1], reverse=True):
                outf.write(token+"\t"+str(value)+"\n")
            
            
    wb = dict()
    for yearfile in sorted(os.listdir(foldername+"peryear")):
        with open (foldername+"peryear/"+yearfile, "r", encoding="utf8") as inf:
            for line in inf:
                linearr=line.split("\t")
                token = linearr[0]
                if token in wb:
                    wb[token] = wb[token] + int(linearr[1])
                else:
                    wb[token] = int(linearr[1])
    with open (foldername+"/_all.txt", "w", encoding="utf8") as outf:
        for token,value in sorted(wb.items(), key = lambda x:x[1], reverse=True):
            outf.write(token+"\t"+str(value)+"\n")

def reset():
    global n
    print("Reset")

    if not os.path.exists("data"):
        os.mkdir("data")
    if os.path.exists("data/ngram"+n):
        shutil.rmtree("data/ngram"+n)
    os.mkdir("data/ngram"+n)
    if os.path.exists("data/ngram"+n+"peryear"):
        shutil.rmtree("data/ngram"+n+"peryear")
    os.mkdir("data/ngram"+n+"peryear")

def collect():
    global count
    global n
    reset()
    print("Collect...")
    doclist = getdoclist(ctsns).split("\n")
    if count == -1:
        count = len(doclist)
    for line in doclist:
        urn = line.split("\t")[0]
        urnarr = urn.split(".")
        year = line.split("\t")[2]

        if (len(year)>1 and count!=0):
            print(str(count)+" "+urn)
            count-=1

            with open ("data/ngram"+n+"/"+urn.replace(":","_#_")+".txt", "w",encoding="utf8") as outf,open ("data/ngram"+n+"peryear/"+year+".txt", "a",encoding="utf8") as outyf:
                try:
                    rs = cts_ngram(urn,"&sort&lowercase&n="+n)
                    outf.write(rs)
                    outyf.write(rs+"\n")
                except:
                    with open("_ERROR.txt","a",encoding="utf8") as errf:
                        errf.write("Error nGram:-->"+urn+"\n")

    process("data/ngram"+n)

def index(n):
    con = sqlite3.connect("data/ngram"+n+".db")
    cursor = con.cursor()
    print("Indexing...")
    cursor.execute("CREATE INDEX ngramdateindex ON ngramdatecount(ngram);")
    cursor.execute("CREATE INDEX dateindex ON ngramdatecount(date);")
    cursor.execute("CREATE INDEX ngramindex ON ngramcount(ngram);")
    con.commit()
    con.close()

def initTables(n):
    if os.path.exists("data/ngram"+n+".db"):
        os.remove("data/ngram"+n+".db")
    con = sqlite3.connect("data/ngram"+n+".db")
    cursor = con.cursor()
    cursor.execute("CREATE TABLE ngramdatecount(ngram VARCHAR (50),date DATE,frequency INTEGER);")
    cursor.execute("CREATE TABLE ngramcount(ngram VARCHAR (50),frequency INTEGER);")
    con.commit()
    con.close()

def db():
    print("DB...")
    global n
    initTables(n)
    con = sqlite3.connect("data/ngram"+n+".db")
    cursor = con.cursor()

    #for file in sorted(os.listdir("data")):
    #    if(file.startswith("ngram")  and not ".db" in file and file.endswith("peryear")):
    for year in sorted(os.listdir("data/ngram"+n+"peryear")):
        print("sql ngram"+n+"peryear:"+year)
        with open ("data/ngram"+n+"peryear/"+year, "r", encoding="utf8") as inf:
            for line in inf.readlines():
                if len(line.strip())>0:
                    linearr = line.split("\t")
                    vals = '" '+linearr[0]+' ",'+year.replace(".txt","")+','+linearr[1].strip()
                    query="INSERT INTO ngramdatecount(ngram,date,frequency) VALUES("+vals+")"
                    cursor.execute(query)
                
    con.commit()

    #for file in sorted(os.listdir("data")):
    #    if(file.startswith("ngram") and not ".db" in file and not file.endswith("peryear")):
    with open ("data/ngram"+n+"/_all.txt", "r", encoding="utf8") as inf:
        for line in inf.readlines():
            if len(line.strip())>0:
                linearr = line.split("\t")
                vals = '" '+linearr[0]+' ",'+linearr[1].strip()
                query="INSERT INTO ngramcount(ngram,frequency) VALUES("+vals+")"
                cursor.execute(query)
    con.commit()
    con.close()
    index(n)

if len(sys.argv)==3:
    if sys.argv[2] == "db":
        db()
    else:
        if sys.argv[2] == "collect":
            collect()
else:
    collect()
    db()
    
