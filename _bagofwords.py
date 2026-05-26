import sys
import os
import shutil
import sqlite3
from config import *
from pythoncts import *

doc_year = {}
tokensumperyear = {}
typesumperyear = {}

def process(foldername):
    for yearfile in sorted(os.listdir(foldername+"peryear")):
        print("process "+foldername+":"+yearfile)
        wb = dict()
        with open (foldername+"peryear/"+yearfile, "r", encoding="utf8") as inf:
            for line in inf:
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
            year = int(yearfile.replace(".txt",""))
            for line in inf:
                linearr=line.split("\t")
                token = linearr[0]
                if year in tokensumperyear:
                    tokensumperyear[year] = tokensumperyear[year]+int(linearr[1])
                    typesumperyear[year] = typesumperyear[year]+1
                else:
                    tokensumperyear[year] = int(linearr[1])
                    typesumperyear[year] = 1

                if token in wb:
                    wb[token] = wb[token] + int(linearr[1])
                else:
                    wb[token] = int(linearr[1])
    with open (foldername+"/_all.txt", "w", encoding="utf8") as outf:
        for token,value in sorted(wb.items(), key = lambda x:x[1], reverse=True):
            outf.write(token+"\t"+str(value)+"\n")
    with open (foldername+"/_tokensumperyear.txt", "w", encoding="utf8") as outf:
        for year,value in sorted(tokensumperyear.items()):
            outf.write(str(year)+"\t"+str(value)+"\n")
    with open (foldername+"/_typesumperyear.txt", "w", encoding="utf8") as outf:
        for year,value in sorted(typesumperyear.items()):
            outf.write(str(year)+"\t"+str(value)+"\n")
    with open (foldername+"/_typetokenratioperyear.txt", "w", encoding="utf8") as outf:
        for year,value in sorted(typesumperyear.items()):
            outf.write(str(year)+"\t"+str(typesumperyear[year] / tokensumperyear[year])+"\n")

    wb_max = dict()
    wb_min = dict()
    for yearfile in sorted(os.listdir(foldername+"peryear")):
        with open (foldername+"peryear/"+yearfile, "r", encoding="utf8") as inf:
            for line in inf:
                year = int(yearfile.replace(".txt",""))
                token = line.split("\t")[0]
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
    with open (foldername+"/_minmaxyearzipf.txt", "w", encoding="utf8") as outf:
        for token,value in sorted(wb.items(),key = lambda x:x[1], reverse=True):
            outf.write(token+"\t"+str(wb_min[token])+"\t"+str(wb_max[token])+"\t"+str(value)+"\n")
    daterange = {}
    for token,value in sorted(wb_min.items(),key = lambda x:x[1], reverse=False):
        drange = str(wb_min[token])+"\t"+str(wb_max[token])
        if not drange in daterange:
            daterange[drange] = token
        else:
            daterange[drange] = daterange[drange]+","+token
    with open (foldername+"/_minmaxyearmin.txt", "w", encoding="utf8") as outf:
        for key in daterange:
            outf.write(key+"\t"+daterange[key]+"\n")
            
    daterange = {}
    for token,value in sorted(wb_max.items(),key = lambda x:x[1], reverse=False):
        drange = str(wb_min[token])+"\t"+str(wb_max[token])
        if not drange in daterange:
            daterange[drange] = token
        else:
            daterange[drange] = daterange[drange]+","+token
    with open (foldername+"/_minmaxyearmax.txt", "w", encoding="utf8") as outf:
        for key in daterange:
            outf.write(key+"\t"+daterange[key]+"\n")

def sanitycheck(rs):
    for line in rs.split("\n"):
        linearr = line.split("\t")
        if len(linearr)!= 2:
            print("+"+line)
            return False
    return True

def reset():
    print("Reset")
    if not os.path.exists("data"):
        os.mkdir("data")
    if os.path.exists("data/bagofwords"):
        shutil.rmtree("data/bagofwords")
    os.mkdir("data/bagofwords")
    if os.path.exists("data/bagofwordsperyear"):
        shutil.rmtree("data/bagofwordsperyear")
    os.mkdir("data/bagofwordsperyear")

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
    for line in doclist:
        urn = line.split("\t")[0]
        urnarr = urn.split(".")
        year = line.split("\t")[2]

        if (len(year)>1 and count!=0):
            doc_year[urn] = year
            print(str(count)+" "+urn)
            count-=1
            with open ("data/bagofwords/"+urn.replace(":","_#_")+".txt", "w",encoding="utf8") as outf,open ("data/bagofwordsperyear/"+year+".txt", "a",encoding="utf8") as outyf:
                rs = cts_bagofwords(urn)
                if sanitycheck(rs):
                    outf.write(rs)
                    outyf.write(rs+"\n")
                else:
                    with open("_ERROR.txt","a",encoding="utf8") as errf:
                        errf.write("Error Bagofwords:-->"+urn+"\n")
    process("data/bagofwords")

def initTables():
    if os.path.exists("data/bagofwords.db"):
        os.remove("data/bagofwords.db")
    con = sqlite3.connect("data/bagofwords.db")
    cursor = con.cursor()
    cursor.execute("CREATE TABLE tokendatecount(token VARCHAR (50),date DATE,frequency INTEGER);")
    cursor.execute("CREATE TABLE tokencount(token VARCHAR (50),frequency INTEGER);")
    cursor.execute("CREATE TABLE urndatewordbag(urn VARCHAR (50),date DATE,wordbag text);")
    con.commit()
    con.close()

def index():
    con = sqlite3.connect("data/bagofwords.db")
    cursor = con.cursor()
    print("Indexing...")
    cursor.execute("CREATE INDEX tokenindex ON tokencount(token);")
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
    con = sqlite3.connect("data/bagofwords.db")
    cursor = con.cursor()

    doclist = getdoclist(ctsns).split("\n")
    for line in doclist:
        urn_date = line.split("\t")
        doc_year[urn_date[0]] = urn_date[2]

    with open ("data/bagofwords/_all.txt", "r", encoding="utf8") as inf:
        for line in inf.readlines():
            if len(line.strip())>0:
                linearr = line.split("\t")
                vals = '"'+linearr[0]+'",'+linearr[1]
                query="INSERT INTO tokencount(token,frequency) VALUES("+vals+")"
                cursor.execute(query)
    con.commit()
    
    yearfiles = sorted(os.listdir("data/bagofwordsperyear"))
    for year in yearfiles:
        #print("sql bagofwordsperyear:"+year)
        
        with open ("data/bagofwordsperyear/"+year, "r", encoding="utf8") as inf:
            for line in inf.readlines():
                if len(line.strip())>0:
                    linearr = line.split("\t")
                    vals = '"'+linearr[0]+'",'+year.replace(".txt","")+','+linearr[1]
                    query="INSERT INTO tokendatecount(token,date,frequency) VALUES("+vals+")"
                    cursor.execute(query)
        con.commit()
        
    files = sorted(os.listdir("data/bagofwords"))
    for file in files:
        if file.startswith("urn_#_"):
            #print("sql bagofwordsperurn:"+file)
            with open ("data/bagofwords/"+file, "r", encoding="utf8") as inf:
                wordbag = "|"
                for line in inf.readlines():
                    if len(line.strip())>0:
                        wordbag += line.split("\t")[0]+"|"
                urn = file.replace(".txt","").replace("_#_",":")
                year = doc_year[urn]
                vals = '"'+urn+'","'+year+'","'+wordbag+'"'
                query="INSERT INTO urndatewordbag(urn,date,wordbag) VALUES("+vals+")"
                cursor.execute(query)
        con.commit()
    index()

print("Bagofwords")
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
    
