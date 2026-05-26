import sys
import os
import shutil
import sqlite3
from config import *
from pythoncts import *

normbag = {}
bagofwords = {}

with open("data/bagofwords/_all.txt", "r", encoding = "utf8") as bwin:
    for line in bwin:
        linearr = line.split("\t")
        bagofwords[linearr[0]] = int(linearr[1])

def tokencheck(token):
    if not token in bagofwords:
        return False
    return True


    
def normmapping(urn):
    global ctsurl
    global copyrighttoken
    res = cts_passage(urn,"&copyrighttoken="+copyrighttoken)

    
    wordelements = res.split("<w")
    wecount = 0
    insg = str(len(wordelements))
    res = ""
    for we in wordelements:
        if str(wecount).endswith("00"):
            print("\rItems:"+str(wecount)+"/"+insg, sep=' ', end='', flush=True)
        wecount+=1
        if("</w" in we):
            wetype = ""
            subtype=""
            norm=""
            token = we.split('>')[1].split('</')[0].replace('"',' ').replace("'"," ").replace(".","").strip().lower()
            if tokencheck(token):
                if 'norm="' in we:
                    norm = "|"+we.split('norm="')[1].split('"')[0].replace('"','')+"|"
                    #if len(norm) == 2:
                    #    norm=""
                    if norm in normbag:
                        normbag[norm] = normbag[norm]+1
                    else:
                        normbag[norm] = 1
                if "subtype=" in we:
                    subtype = we.split('subtype="')[1].split('"')[0]
                if "type=" in we:
                    wetype = we.split('type="')[1].split('"')[0]
                if len(norm.strip())>0:
                    res +=token +"\t"+norm+"\t"+wetype+"\t"+subtype +"\n"
            else:
                with open("_ERROR.txt", "a", encoding="utf8") as errout:
                    errout.write(urn+" normierowasch unknown token "+token + "\n")
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
        with open (foldername+"peryear/"+yearfile, "r", encoding="utf8") as inf:
            for line in inf:
                linearr=line.split("\t")
                token_norm = linearr[0]+"\t"+linearr[1]+"\t"+linearr[2]+"\t"+linearr[3]
                if token_norm in wb:
                    wb[token_norm] = wb[token_norm] + int(linearr[4])
                else:
                    wb[token_norm] = int(linearr[4])
    with open (foldername+"/_all.txt", "w", encoding="utf8") as outf:
        for token_norm,value in sorted(wb.items(), key = lambda x:x[1], reverse=True):
            outf.write(token_norm+"\t"+str(value)+"\n")

def reset():
    if not os.path.exists("data"):
        os.mkdir("data")
    if os.path.exists("data/normmapping"):
        shutil.rmtree("data/normmapping")
    os.mkdir("data/normmapping")
    if os.path.exists("data/normmappingperyear"):
        shutil.rmtree("data/normmappingperyear")
    os.mkdir("data/normmappingperyear")
    
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
            print(str(count)+" "+urn)
            count -= 1
            rs = normmapping(urn)
            if len(rs.strip())>0:
                with open ("data/normmapping/"+urn.replace(":","_#_")+".txt", "w",encoding="utf8") as outf,open ("data/normmappingperyear/"+year+".txt", "a",encoding="utf8") as outyf:
                    outf.write(rs)
                    outyf.write(rs)
            else:
                print("No Items")
                count+=1
    process("data/normmapping")
    with open ("data/normmapping/_normbag.txt", "w",encoding="utf8") as outf:
        for token,value in sorted(normbag.items(), key = lambda x:x[1], reverse=True):
            if len(token.strip())>0:
                outf.write(token+"\t"+str(value)+"\n")


def index():
    con = sqlite3.connect("data/normmapping.db")
    cursor = con.cursor()
    print("Indexing...")
    cursor.execute("CREATE INDEX tokenindextype ON tokennormtypesubtypefrequency(token);")
    cursor.execute("CREATE INDEX normindextype ON tokennormtypesubtypefrequency(norm);")
    cursor.execute("CREATE INDEX typeindextype ON tokennormtypesubtypefrequency(type);")
    cursor.execute("CREATE INDEX subtypeindextype ON tokennormtypesubtypefrequency(subtype);")
    cursor.execute("CREATE INDEX tokenindex ON tokennormtypesubtypedatefrequency(token);")
    cursor.execute("CREATE INDEX normindex ON tokennormtypesubtypedatefrequency(norm);")
    cursor.execute("CREATE INDEX typeindex ON tokennormtypesubtypedatefrequency(type);")
    cursor.execute("CREATE INDEX subtypeindex ON tokennormtypesubtypedatefrequency(subtype);")
    cursor.execute("CREATE INDEX dateindex ON tokennormtypesubtypedatefrequency(date);")
    cursor.execute("CREATE INDEX normfrequencyindex ON normfrequency(norm);")
    cursor.execute("CREATE INDEX normtokenindex ON normtokenfrequency(norm);")
    cursor.execute("CREATE INDEX normtokentokenindex ON normtokenfrequency(token);")
    cursor.execute("CREATE INDEX normurnindex ON urndatenormbag(urn);")
    cursor.execute("CREATE INDEX urnindex ON urndatenormbag(normbag);")
    cursor.execute("CREATE INDEX urndateindex ON urndatenormbag(date);")
    cursor.execute("CREATE INDEX normnonambignorm ON normnonambig(norm);")
    con.commit()
    con.close()
    
def initTables():
    if os.path.exists("data/normmapping.db"):
        os.remove("data/normmapping.db")
    con = sqlite3.connect("data/normmapping.db")
    cursor = con.cursor()
    cursor.execute("CREATE TABLE urndatenormbag(urn VARCHAR (50),date DATE,normbag text);")
    cursor.execute("CREATE TABLE tokennormtypesubtypedatefrequency(token VARCHAR ("+str(tokenlength)+"),norm VARCHAR (50),type VARCHAR (10),subtype VARCHAR (10),date DATE,frequency INTEGER);")
    cursor.execute("CREATE TABLE tokennormtypesubtypefrequency(token VARCHAR ("+str(tokenlength)+"),norm VARCHAR (50),type VARCHAR (10),subtype VARCHAR (10),frequency INTEGER);")
    cursor.execute("CREATE TABLE normfrequency(norm VARCHAR (50),frequency INTEGER);")
    cursor.execute("CREATE TABLE normtokenfrequency(norm VARCHAR (50),token VARCHAR ("+str(tokenlength)+"),frequency INTEGER);")
    cursor.execute("CREATE TABLE normnonambig(norm VARCHAR (50),frequency INTEGER);")
    con.commit()
    con.close()
    
def db():
    initTables()
    con = sqlite3.connect("data/normmapping.db")
    cursor = con.cursor()

    normtokenbag = {}
    tokennormtypesubtypebag = {}
    doc_year = {}
    doclist = getdoclist(ctsns).split("\n")
    for line in doclist:
        urn_date = line.split("\t")
        doc_year[urn_date[0]] = urn_date[2]
        

    yearfiles = sorted(os.listdir("data/normmappingperyear"))
    for year in yearfiles:
        print("sql normmappingperyear:"+year)
        with open ("data/normmappingperyear/"+year, "r", encoding="utf8") as inf:
            for line in inf.readlines():
                if len(line.strip())>0:
                    linearr = line.split("\t")
                    toknorm = linearr[0]+"\t"+linearr[1]
                    toknormtypesubtype = linearr[0]+"\t"+linearr[1]+"\t"+linearr[2]+"\t"+linearr[3]

                    if toknormtypesubtype in tokennormtypesubtypebag:
                        tokennormtypesubtypebag[toknormtypesubtype] = tokennormtypesubtypebag[toknormtypesubtype]+int(linearr[4])
                    else:
                        tokennormtypesubtypebag[toknormtypesubtype] = int(linearr[4])

                    if toknorm in normtokenbag:
                        normtokenbag[toknorm] = normtokenbag[toknorm]+int(linearr[4])
                    else:
                        normtokenbag[toknorm] = int(linearr[4])

                    vals = '"'+linearr[0]+'","'+linearr[1]+'","'+linearr[2]+'","'+linearr[3]+'",'+year.replace(".txt","")+','+linearr[4].strip()
                    query="INSERT INTO tokennormtypesubtypedatefrequency(token,norm,type,subtype,date,frequency) VALUES("+vals+")"
                    cursor.execute(query)
        con.commit()
    with open ("data/normmapping/_normbag.txt", "r", encoding="utf8") as inf:
        for line in inf.readlines():
            if len(line.strip())>0:
                linearr = line.split("\t")
                vals = '"'+linearr[0]+'",'+linearr[1].strip()
                query="INSERT INTO normfrequency(norm,frequency) VALUES("+vals+")"
                cursor.execute(query)
        con.commit()
    files = sorted(os.listdir("data/normmapping"))

    wb_nonambig = {}
    with open ("data/normmapping/_normbag.txt", "r", encoding="utf8") as inf:
        for line in inf.readlines():
            if len(line.strip())>0:
                linearr = line.split("\t")
                normarr = linearr[0].split("|")
                for norm in normarr:
                    if norm in wb_nonambig:
                        wb_nonambig[norm] = wb_nonambig[norm] + int(linearr[1])
                    else:
                        wb_nonambig[norm] = int(linearr[1])
                    
    for norm in wb_nonambig:
        vals = '"|'+norm+'|",'+str(wb_nonambig[norm])
        query="INSERT INTO normnonambig(norm,frequency) VALUES("+vals+")"
        cursor.execute(query)
    con.commit()

    for file in files:
        if file.startswith("urn_#_"):
            with open ("data/normmapping/"+file, "r", encoding="utf8") as inf:
                normbag = "#"
                for line in inf.readlines():
                    if len(line.strip())>0:
                        normbag += line.split("\t")[1]+"#"
                while("#||#" in normbag):
                    normbag = normbag.replace("#||#","#")
                urn = file.replace(".txt","").replace("_#_",":")
                year = doc_year[urn]
                vals = '"'+urn+'","'+year+'","'+normbag+'"'
                query="INSERT INTO urndatenormbag(urn,date,normbag) VALUES("+vals+")"
                cursor.execute(query)
        con.commit()
    for normtoken in normtokenbag:
        vals = '"'+normtoken.replace("\t",'","')+'",'+str(normtokenbag[normtoken])
        query = "INSERT INTO normtokenfrequency(token,norm,frequency) VALUES("+vals+")"
        cursor.execute(query)
    con.commit()
    for toktypesubtypenorm in tokennormtypesubtypebag:
        vals = '"'+toktypesubtypenorm.replace("\t",'","')+'",'+str(tokennormtypesubtypebag[toktypesubtypenorm])
        query = "INSERT INTO tokennormtypesubtypefrequency(token,norm,type,subtype,frequency) VALUES("+vals+")"
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
    
