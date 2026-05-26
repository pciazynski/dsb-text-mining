import sys
import os
import shutil
import sqlite3
from pythoncts import *
from config import *

n=sys.argv[1]

deudict = {}

with open("data/langDetect"+str(n)+"/deu.txt", "r", encoding="utf8") as inf:
    for line in inf:
        deudict[line.split("\t")[0].strip()]=1

if not os.path.exists("data"):
    os.mkdir("data")

def reset():
    print("Reset")
    if os.path.exists("data/langseparation"):
        shutil.rmtree("data/langseparation")
    os.mkdir("data/langseparation")
    if os.path.exists("data/langseparationperyear"):
        shutil.rmtree("data/langseparationperyear")
    os.mkdir("data/langseparationperyear")

def langseparation(urn):
    global copyrighttoken
    res = ""
    data = structurebagofwords(urn,"&deletexml&lowercase&copyrighttoken="+copyrighttoken).split("\n")
    for line in data:
        linearr = line.split("\t")
        if len(linearr)==3:
            urn = linearr[0]
            textarr = linearr[2].split(",")
            occdeu = 0
            founddeu = ""
            for token in textarr:
                token = token.split(":")[0]
                if token in deudict:
                    occdeu += 1
                    founddeu += token+","
            
            if occdeu > 0:
                founddeu = founddeu[:-1]
                res+=line+"\t"+founddeu+"\n"
    return res.strip()

def process(foldername):
    with open (foldername+"/_all.txt", "w", encoding="utf8") as outf:
        for yearfile in sorted(os.listdir(foldername+"peryear")):
            print("process "+foldername+":"+yearfile)
            with open (foldername+"peryear/"+yearfile, "r", encoding="utf8") as inf:
                for line in inf:
                    outf.write(line)

def getdoclist(ctsns):
    tmplist = ""
    if os.path.exists("urnlist.txt"):
        with open("urnlist.txt","r",encoding="utf8") as inf:
            for line in inf:
                tmplist+=line
    else:
        tmplist = inventory(ctsns)
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
            print(str(count)+" "+urn)
            count-=1
            rs = langseparation(urn)
            if len(rs.strip())>0:
                with open ("data/langseparation/"+urn.replace(":","_#_")+".txt", "w",encoding="utf8") as outf,open ("data/langseparationperyear/"+year+".txt", "a",encoding="utf8") as outyf:
                    outf.write(rs)
                    outyf.write(rs+"\n")
    process("data/langseparation")
    
def initTables():
    if os.path.exists("data/langDeu"+str(n)+".db"):
        os.remove("data/langDeu"+str(n)+".db")
    con = sqlite3.connect("data/langDeu"+str(n)+".db")
    cursor = con.cursor()
    cursor.execute("CREATE TABLE tokenurnyearpassagestructureelementfrequency(token VARCHAR (50),docurn VARCHAR (50),urn VARCHAR (50), year DATE,structureelement VARCHAR(50), frequency INTEGER);")
    con.commit()
    con.close()

def index():
    con = sqlite3.connect("data/langDeu"+str(n)+".db")
    cursor = con.cursor()
    print("Indexing...")
    cursor.execute("CREATE INDEX tokenindex ON tokenurnyearpassagestructureelementfrequency(token);")
    cursor.execute("CREATE INDEX yearindex ON tokenurnyearpassagestructureelementfrequency(year);")
    cursor.execute("CREATE INDEX urnindex ON tokenurnyearpassagestructureelementfrequency(urn);")
    cursor.execute("CREATE INDEX freqindex ON tokenurnyearpassagestructureelementfrequency(frequency);")
    cursor.execute("CREATE INDEX docurnindex ON tokenurnyearpassagestructureelementfrequency(docurn);")
    cursor.execute("CREATE INDEX structureelement ON tokenurnyearpassagestructureelementfrequency(structureelement);")
    con.commit()
    con.close()

def db():
    print("DB...")
    initTables()
    con = sqlite3.connect("data/langDeu"+str(n)+".db")
    cursor = con.cursor()

    for yearfile in sorted(os.listdir("data/langseparationperyear/")):
        with open ("data/langseparationperyear/"+yearfile, "r", encoding="utf8") as inf:
            for line in inf:
                line=line.strip()
                rs = line.split("\t")
                docurn=rs[0].split(":")
                docurn=docurn[0]+":"+docurn[1]+":"+docurn[2]+":"+docurn[3]+":"
                tokencountarr = rs[2].split(",")
                tokencountdict = {}
                for token in tokencountarr:
                    tokenarr = token.split(":")
                    tokencountdict[tokenarr[0]] = tokenarr[1]
                tokenarr = rs[3].split(",")
                for token in tokenarr:
                    if len(token.strip())>0:
                        vals =  "'"+tokenarr[0].strip()+"','"+rs[0].strip()+"','"+docurn.strip()+"','"+yearfile.replace(".txt","")+"','"+rs[1].strip()+"',"+str(tokencountdict[token])
                        query="INSERT INTO tokenurnyearpassagestructureelementfrequency(token,urn,docurn,year,structureelement,frequency) VALUES("+vals+")"
                        cursor.execute(query)
    con.commit()
    con.close()
    index()
    
    

if len(sys.argv)==3:
    if sys.argv[2] == "db":
        db()
    else:
        if sys.argv[2] == "collect":
            collect()
else:
    collect()
    db()
    
