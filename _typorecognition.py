from datetime import datetime
import os
import sys
import shutil

if not os.path.exists("data"):
    os.mkdir("data")
if os.path.exists("data/typorecognition"):
    shutil.rmtree("data/typorecognition")
os.mkdir("data/typorecognition")

    
    
tab = "\t"
nl = "\n"
sumtoklen = 0
checkedwords = {}
singleusewords = {}
alreadyseen = {}

bw = dict()
with open ("data/bagofwords/_all.txt","r",encoding="utf8") as bwin:
    for line in bwin:
        linearr = line.split(tab)
        bw[linearr[0]] = int(linearr[1])
        sumtoklen += len(linearr[0].strip())

with open ("data/bagofwords/_singleusewords.txt","r",encoding="utf8") as bwin:
    for line in bwin:
        linearr = line.split(tab)
        singleusewords[linearr[0]] = int(linearr[1])
        
        
#Source https://www.python-kurs.eu/levenshtein_distanz.php
def iterative_levenshtein(s, t):
    rows = len(s)+1
    cols = len(t)+1
    dist = [[0 for x in range(cols)] for x in range(rows)]
    for i in range(1, rows):
        dist[i][0] = i
    for i in range(1, cols):
        dist[0][i] = i
    for col in range(1, cols):
        for row in range(1, rows):
            if s[row-1] == t[col-1]:
                cost = 0
            else:
                cost = 1
            dist[row][col] = min(dist[row-1][col] + 1,      # deletion
                                 dist[row][col-1] + 1,      # insertion
                                 dist[row-1][col-1] + cost) # substitution
    return dist[row][col]

counter = -1
if len(sys.argv) >1:
    counter = int(sys.argv[1].split(" ")[0])

maxls = 1

start = datetime.now()
avgtoklen = int(sumtoklen / len(bw))
res = {}
typofrequency = 100

print("Start " +start.strftime("%m/%d/%Y, %H:%M:%S")+" avgtoklen: "+str(avgtoklen))
with open ("data/typorecognition/typos.txt", "w", encoding="utf8") as outf, open ("data/typorecognition/typowords.txt", "a", encoding="utf8") as outfwords:
    for token1,tokencount in sorted(bw.items(),key = lambda x:x[1], reverse=True):
        if counter != 0:
            if len(token1)>=avgtoklen and not token1 in checkedwords and not token1 in res and int(bw[token1])>typofrequency:
                for token2 in bw:
                    if int(bw[token2]) == 1:
                        if token1 != token2 and not abs(len(token1)-len(token2)) > maxls :
                            ls = iterative_levenshtein(token1, token2)
                            if(ls<=maxls and ls < len(token1) and ls < len(token2)):
                                #token2 is a typo candiadte 
                                res[token2] = token1
                                if counter>0:
                                    counter -= 1
                                outf.write(token2+tab+token1+":"+str(bw[token1])+nl)
                                if not token2 in alreadyseen:
                                    outfwords.write(token2+tab+str(singleusewords[token2])+nl)
                                    alreadyseen[token2] = 1
                                print(token1+":"+token2+tab+str(bw[token1])+":"+str(bw[token2])+tab+str(ls)+tab+str(counter))
end = datetime.now()
#    for typo,token in sorted(res.items(),key = lambda x:x[1], reverse=False):

print(str(end-start))

