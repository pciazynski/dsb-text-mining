import os
import shutil


if os.path.exists("data/stats"):
    shutil.rmtree("data/stats")
os.mkdir("data/stats")

shutil.copy("data/bagofwords/_tokensumperyear.txt","data/stats/_tokensumperyear.txt")
shutil.copy("data/bagofwords/_typesumperyear.txt","data/stats/_typesumperyear.txt")
shutil.copy("data/bagofwords/_typetokenratioperyear.txt","data/stats/_typetokenratioperyear.txt")

toksum = 0
typesum = 0
wordlensum=0
wordlenmax=0
wordlenmin = 1000000
charcount = {}
tokenlencount = {}

tb = "\t"
nl = "\n"

with open ("data/bagofwords/_all.txt", "r", encoding="utf8") as f:
    for line in f:
        linearr = line.split("\t")
        toksum += 1
        typesum += int(linearr[1])
        token = linearr[0]
        toklen = len(token)
        wordlensum += toklen
        if wordlenmax<toklen:
            wordlenmax=toklen
        if wordlenmin>toklen:
            wordlenmin=toklen
        if toklen in tokenlencount:
            tokenlencount[toklen] = tokenlencount[toklen] +1
        else:
            tokenlencount[toklen] = 1

toklenstr = ""
for token,value in sorted(tokenlencount.items(), key = lambda x:x[1], reverse=True):
    toklenstr += str(token)+":"+str(value)+","
        
res = ""
res += "Type Count\t"+str(toksum)+"\n"
res += "Token Count\t"+str(typesum)+"\n"
res += "Token length avg\t"+str(wordlensum/toksum)+"\n"
res += "Token length min\t"+str(wordlenmin)+"\n"
res += "Token length max\t"+str(wordlenmax)+"\n"
res += "Token length Count\t"+str(toklenstr[:-1])+"\n"


with open ("data/stats.txt", "w", encoding="utf8") as f:
    f.write(res)
    
with open ("data/stats/tokenlength.txt", "w", encoding="utf8") as f:
    for token,value in sorted(tokenlencount.items(), key = lambda x:x[0], reverse=False):
        f.write(str(token)+tb+str(value)+nl)


