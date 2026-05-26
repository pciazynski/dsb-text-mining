from urllib.request import urlopen
import sys
import os
import shutil
import sqlite3
from config import *
from pythoncts import *

lemmabag = {}
bagofwords = {}

with open("data/bagofwords/_all.txt", "r", encoding = "utf8") as bwin:
    for line in bwin:
        linearr = line.split("\t")
        bagofwords[linearr[0]] = int(linearr[1])

def requestctsurl(ns):
    global ctsurl
    if len(ctsurl) == 0:
        if not ns.startswith("urn:cts"):
            ns = "urn:cts:"+ns
        ns = ns.split(":")[2]
        data = urlopen("https://urncts.eu/namespaceresolver/"+ns) 
        for line in data: 
            ctsurl+=line.decode('utf-8')
        

def tokencheck(token):
    if not token in bagofwords:
        return False
    return True
    
def lemmamapping(urn):
    global ctsurl
    global copyrighttoken
    requestctsurl(urn)
    res = cts_passage(urn,"&copyrighttoken="+copyrighttoken)
    wordelements = res.split("<w")
    res = ""
    wecount = 0
    insg = str(len(wordelements))
    for we in wordelements:
        if str(wecount).endswith("00"):
            print("\rItems:"+str(wecount)+"/"+insg, sep=' ', end='', flush=True)
        wecount+=1
        if("</w" in we):
            wetype = ""
            subtype=""
            lemma=""
            token = we.split('>')[1].split('</')[0].replace('"',' ').replace("'"," ").replace(".","").strip().lower()
            if tokencheck(token):
                if 'lemma="' in we:
                    lemma = "|"+we.split('lemma="')[1].split('"')[0].replace('"',' ').replace("'"," ").strip()+"|"
                    #if len(lemma) == 2:
                    #    lemma=""
                    #else:
                        #lemmaarr=lemma.split("|")
                        #for lemmatoken in lemmaarr:
                    if lemma in lemmabag:
                        lemmabag[lemma] = lemmabag[lemma]+1
                    else:
                        lemmabag[lemma] = 1
                if "subtype=" in we:
                    subtype = we.split('subtype="')[1].split('"')[0]
                if "type=" in we:
                    wetype = we.split('type="')[1].split('"')[0]
                if len(lemma.strip())>0:
                    res +=token +"\t"+lemma+"\t"+wetype+"\t"+subtype +"\n"
            else:
                with open("_ERROR.txt", "a", encoding="utf8") as errout:
                    errout.write(urn+" lemmatisierowasch unknown token "+token + "\n")
    print("\rOK                                       ")
    return res

    

def process(foldername):
    for yearfile in sorted(os.listdir(foldername+"peryear")):
        print("process "+foldername+":"+yearfile)
        wb = dict()
        with open (foldername+"peryear/"+yearfile, "r", encoding="utf8") as inf:
            for line in inf:
                token = line.replace("\n","")
                if token in wb:
                    wb[token] = wb[token] + 1
                else:
                    wb[token] = 1
        with open (foldername+"peryear/"+yearfile, "w", encoding="utf8") as outf:
            for token,value in sorted(wb.items(), key = lambda x:x[1], reverse=True):
                outf.write(token+"\t"+str(value)+"\n")
            
            
    wb = dict()
    for yearfile in sorted(os.listdir(foldername+"peryear")):
        print("Bagging "+foldername+":"+yearfile)
        with open (foldername+"peryear/"+yearfile, "r", encoding="utf8") as inf:
            for line in inf:
                linearr=line.split("\t")
                token_lemma = linearr[0]+"\t"+linearr[1]+"\t"+linearr[2]+"\t"+linearr[3]
                if token_lemma in wb:
                    wb[token_lemma] = wb[token_lemma] + int(linearr[4])
                else:
                    wb[token_lemma] = int(linearr[4])
    with open (foldername+"/_all.txt", "w", encoding="utf8") as outf:
        for token_lemma,value in sorted(wb.items(), key = lambda x:x[1], reverse=True):
            outf.write(token_lemma+"\t"+str(value)+"\n")

def reset():
    if not os.path.exists("data"):
        os.mkdir("data")
    if os.path.exists("data/lemmamapping"):
        shutil.rmtree("data/lemmamapping")
    os.mkdir("data/lemmamapping")
    if os.path.exists("data/lemmamappingperyear"):
        shutil.rmtree("data/lemmamappingperyear")
    os.mkdir("data/lemmamappingperyear")

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

        if (len(year)>1 and count>0):
            print(str(count)+" "+urn)
            count -= 1
            rs = lemmamapping(urn)
            if len(rs.strip())>0:
                with open ("data/lemmamapping/"+urn.replace(":","_#_")+".txt", "w",encoding="utf8") as outf,open ("data/lemmamappingperyear/"+year+".txt", "a",encoding="utf8") as outyf:
                    outf.write(rs)
                    outyf.write(rs)
            else:
                print("No Items")
                count+=1

    process("data/lemmamapping")
    with open ("data/lemmamapping/_lemmabag.txt", "w",encoding="utf8") as outf:
        for token,value in sorted(lemmabag.items(), key = lambda x:x[1], reverse=True):
            if len(token.strip())>0:
                outf.write(token+"\t"+str(value)+"\n")


def index():
    con = sqlite3.connect("data/lemmamapping.db")
    cursor = con.cursor()
    print("Indexing...")
    cursor.execute("CREATE INDEX tokenindextype ON tokenlemmatypesubtypefrequency(token);")
    cursor.execute("CREATE INDEX lemmaindextype ON tokenlemmatypesubtypefrequency(lemma);")
    cursor.execute("CREATE INDEX subtypeindextype ON tokenlemmatypesubtypefrequency(subtype);")
    cursor.execute("CREATE INDEX tokenindex ON tokenlemmatypesubtypedatefrequency(token);")
    cursor.execute("CREATE INDEX lemmaindex ON tokenlemmatypesubtypedatefrequency(lemma);")
    cursor.execute("CREATE INDEX typeindex ON tokenlemmatypesubtypedatefrequency(type);")
    cursor.execute("CREATE INDEX subtypeindex ON tokenlemmatypesubtypedatefrequency(subtype);")
    cursor.execute("CREATE INDEX dateindex ON tokenlemmatypesubtypedatefrequency(date);")
    cursor.execute("CREATE INDEX lemmafrequencyindex ON lemmafrequency(lemma);")
    cursor.execute("CREATE INDEX lemmatokenlemmaindex ON lemmatokenfrequency(lemma);")
    cursor.execute("CREATE INDEX lemmatokentokenindex ON lemmatokenfrequency(token);")
    cursor.execute("CREATE INDEX lemmaurnindex ON urndatelemmabag(urn);")
    cursor.execute("CREATE INDEX urnindex ON urndatelemmabag(lemmabag);")
    cursor.execute("CREATE INDEX urndateindex ON urndatelemmabag(date);")
    cursor.execute("CREATE INDEX lemmanonambiglemma ON lemmanonambig(lemma);")
    con.commit()
    con.close()
    
def initTables():
    if os.path.exists("data/lemmamapping.db"):
        os.remove("data/lemmamapping.db")
    con = sqlite3.connect("data/lemmamapping.db")
    cursor = con.cursor()
    cursor.execute("CREATE TABLE urndatelemmabag(urn VARCHAR (50),date DATE,lemmabag text);")
    cursor.execute("CREATE TABLE tokenlemmatypesubtypedatefrequency(token VARCHAR ("+str(tokenlength)+"),lemma VARCHAR (50),type VARCHAR (10),subtype VARCHAR (10),date DATE,frequency INTEGER);")
    cursor.execute("CREATE TABLE tokenlemmatypesubtypefrequency(token VARCHAR ("+str(tokenlength)+"),lemma VARCHAR (50),type VARCHAR (10),subtype VARCHAR (10),frequency INTEGER);")
    cursor.execute("CREATE TABLE lemmafrequency(lemma VARCHAR (50),frequency INTEGER);")
    cursor.execute("CREATE TABLE lemmatokenfrequency(lemma VARCHAR (50),token VARCHAR ("+str(tokenlength)+"),frequency INTEGER);")
    cursor.execute("CREATE TABLE lemmanonambig(lemma VARCHAR (50),frequency INTEGER);")
    con.commit()
    con.close()
    
def db():
    initTables()
    con = sqlite3.connect("data/lemmamapping.db")
    cursor = con.cursor()

    lemmatokenbag = {}
    lemmatokentypesubtypebag = {}
    doc_year = {}

    doclist = getdoclist(ctsns).split("\n")
    for line in doclist:
        urn_date = line.split("\t")
        doc_year[urn_date[0]] = urn_date[2]
        
    yearfiles = sorted(os.listdir("data/lemmamappingperyear"))
    for year in yearfiles:
        print("sql lemmamappingperyear:"+year)
        with open ("data/lemmamappingperyear/"+year, "r", encoding="utf8") as inf:
            for line in inf.readlines():
                if len(line.strip())>0:
                    linearr = line.split("\t")
                    toklem = linearr[0]+"\t"+linearr[1]
                    toklemtypesubtype = linearr[0]+"\t"+linearr[1]+"\t"+linearr[2]+"\t"+linearr[3]

                    if toklemtypesubtype in lemmatokentypesubtypebag:
                        lemmatokentypesubtypebag[toklemtypesubtype] = lemmatokentypesubtypebag[toklemtypesubtype]+int(linearr[4])
                    else:
                        lemmatokentypesubtypebag[toklemtypesubtype] = int(linearr[4])

                    if toklem in lemmatokenbag:
                        lemmatokenbag[toklem] = lemmatokenbag[toklem]+int(linearr[4])
                    else:
                        lemmatokenbag[toklem] = int(linearr[4])

                    vals = '"'+linearr[0]+'","'+linearr[1]+'","'+linearr[2]+'","'+linearr[3]+'",'+year.replace(".txt","")+','+linearr[4].strip()
                    query="INSERT INTO tokenlemmatypesubtypedatefrequency(token,lemma,type,subtype,date,frequency) VALUES("+vals+")"
                    cursor.execute(query)
        con.commit()
    with open ("data/lemmamapping/_lemmabag.txt", "r", encoding="utf8") as inf:
        for line in inf.readlines():
            if len(line.strip())>0:
                linearr = line.split("\t")
                vals = '"'+linearr[0]+'",'+linearr[1].strip()
                query="INSERT INTO lemmafrequency(lemma,frequency) VALUES("+vals+")"
                cursor.execute(query)
        con.commit()

    wb_nonambig = {}
    with open ("data/lemmamapping/_lemmabag.txt", "r", encoding="utf8") as inf:
        for line in inf.readlines():
            if len(line.strip())>0:
                linearr = line.split("\t")
                lemmaarr = linearr[0].split("|")
                for lemma in lemmaarr:
                    if lemma in wb_nonambig:
                        wb_nonambig[lemma] = wb_nonambig[lemma] + int(linearr[1])
                    else:
                        wb_nonambig[lemma] = int(linearr[1])
                    
    for lemma in wb_nonambig:
        vals = '"|'+lemma+'|",'+str(wb_nonambig[lemma])
        query="INSERT INTO lemmanonambig(lemma,frequency) VALUES("+vals+")"
        cursor.execute(query)
    con.commit()

    
    files = sorted(os.listdir("data/lemmamapping"))
    for file in files:
        if file.startswith("urn_#_"):
            print("sql lemmamappingperurn:"+file)
            with open ("data/lemmamapping/"+file, "r", encoding="utf8") as inf:
                lemmabag = "#"
                for line in inf.readlines():
                    if len(line.strip())>0:
                        lemmabag += line.split("\t")[1]+"#"
                while("#||#" in lemmabag):
                    lemmabag = lemmabag.replace("#||#","#")
                urn = file.replace(".txt","").replace("_#_",":")
                year = doc_year[urn]
                vals = '"'+urn+'","'+year+'","'+lemmabag+'"'
                query="INSERT INTO urndatelemmabag(urn,date,lemmabag) VALUES("+vals+")"
                cursor.execute(query)
        con.commit()
    
    for lemmatoken in lemmatokenbag:
        vals = '"'+lemmatoken.replace("\t",'","')+'",'+str(lemmatokenbag[lemmatoken])
        query = "INSERT INTO lemmatokenfrequency(token,lemma,frequency) VALUES("+vals+")"
        cursor.execute(query)
    con.commit()
    for toklemtypesubtype in lemmatokentypesubtypebag:
        vals = '"'+toklemtypesubtype.replace("\t",'","')+'",'+str(lemmatokentypesubtypebag[toklemtypesubtype])
        query = "INSERT INTO tokenlemmatypesubtypefrequency(token,lemma,type,subtype,frequency) VALUES("+vals+")"
        cursor.execute(query)
    con.commit()
    con.close()
    
    index()


if len(sys.argv)==2:
    if sys.argv[1] == "db":
        db()
    else:
        if sys.argv[1] == "collect":
            collect()
else:
    collect()
    db()
    
