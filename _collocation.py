import sys
import os
import shutil
import sqlite3
import math

from config import *

def initTables():
    if os.path.exists("data/collocation.db"):
        os.remove("data/collocation.db")
    con = sqlite3.connect("data/collocation.db")
    cursor = con.cursor()
    cursor.execute("CREATE TABLE collocation(left VARCHAR (50),right VARCHAR (50),frequency INTEGER,logdice INTEGER);")
    cursor.execute("CREATE INDEX leftcollocationindex ON collocation(left);")
    cursor.execute("CREATE INDEX rightcollocationindex ON collocation(right);")
    cursor.execute("CREATE TABLE collocationperyear(left VARCHAR (50),right VARCHAR (50),date DATE,frequency INTEGER);")
    cursor.execute("CREATE INDEX leftcollocationperyearindex ON collocationperyear(left);")
    cursor.execute("CREATE INDEX rightcollocationperyearindex ON collocationperyear(right);")
    cursor.execute("CREATE INDEX datecollocationperyearindex ON collocationperyear(date);")
    con.commit()
    con.close()


initTables()
con = sqlite3.connect("data/collocation.db")
cursor = con.cursor()

bw = dict()
with open ("data/bagofwords/_all.txt","r",encoding="utf8") as bwin:
    for line in bwin:
        linearr = line.split("\t")
        bw[linearr[0]] = int(linearr[1])

#for file in sorted(os.listdir("data")):
#    if(file.startswith("ngram") and not ".db" in file and not file.endswith("peryear")):
with open ("data/ngram2/_all.txt", "r", encoding="utf8") as inf:
    for line in inf.readlines():
        if len(line.strip())>0:
            linearr = line.split("\t")
            ngramarr = linearr[0].split(" ")
            freq = int(linearr[1])
            logdice = 14 + math.log ((2*freq)/(bw[ngramarr[0]] + bw[ngramarr[1]]),2)
            vals = '"'+ngramarr[0]+'",'+'"'+ngramarr[1]+'",'+str(freq)+','+str(logdice)
            query="INSERT INTO collocation(left,right,frequency,logdice) VALUES("+vals+")"
            cursor.execute(query)
con.commit()

#for file in sorted(os.listdir("data")):
#    if(file.startswith("ngram")  and not ".db" in file and file.endswith("peryear")):
for year in sorted(os.listdir("data/ngram2peryear")):
    #print("sql collocation:"+year)
    with open ("data/ngram2peryear/"+year, "r", encoding="utf8") as inf:
        for line in inf.readlines():
            if len(line.strip())>0:
                linearr = line.split("\t")
                bigramarr = linearr[0].split(" ")
                vals = '"'+bigramarr[0]+'",'+'"'+bigramarr[1]+'",'+year.replace(".txt","")+','+linearr[1].strip()
                query="INSERT INTO collocationperyear(left,right,date,frequency) VALUES("+vals+")"
                cursor.execute(query)
            
con.commit()
con.close()

