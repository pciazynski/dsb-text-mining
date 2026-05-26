import os

bw = {}
bl = {}
incons = 0
with open ("data/normmapping/_all.txt", "r", encoding="utf8") as bwin, open ("data/normmapping/_inconsistencies.txt", "w", encoding="utf8") as incout:
    for line in bwin:
        linearr = line.split("\t")
        if linearr[0] in bl:
            incout.write(linearr[0]+"\n")
            incons+=1
        bl[linearr[0]] = 1

yay = 0
nay = 0
progress = {}
with open ("data/bagofwords/_all.txt", "r", encoding="utf8") as bwin, open ("data/normmapping/_yay.txt", "w", encoding="utf8") as outyay,open ("data/normmapping/_nay.txt", "w", encoding="utf8") as outnay:
    for line in bwin:
        linearr = line.split("\t")
        if linearr[0] in bl:
            outyay.write(line)
            yay += 1
            progress[line.strip()] = 1
        else:
            nay += 1
            progress[line.strip()] = 0
            outnay.write(line)

with open ("data/normmapping/_progress.txt", "w", encoding="utf8") as outlemprogress:
    for line,value in sorted(progress.items(), key = lambda x:x[1], reverse=True):
        outlemprogress.write(line+"\t"+str(progress[line]) + "\n")
    
    
unsortedlist = {}
sortedlist =  {}

sortedtypecount = 0
unsortedtypecount = 0

with open("data/normmapping/_normbag.txt","r", encoding="utf8") as inf:
    for line in inf:
        count = int(line.split("\t")[1])
        line = line.split("\t")[0]
        linearr = line.split("|")
        if(len(linearr)>3):
            unsortedtypecount += count
            unsortedlist["|".join(linearr)] = 1
            linearr = sorted(linearr)
            if not "|".join(linearr) in sortedlist:
                sortedtypecount += count
            sortedlist["|".join(linearr)] = 1

with open ("data/normmapping/_stats.txt", "w", encoding="utf8") as out:
    out.write("Normiert / Alle: "+str(yay)+" / "+str(yay+nay)+"\n")
    out.write("Inkonsistent: "+str(incons)+"\n")
    out.write("Sortierungsredundanz (ambige Einträge sortiert / ambige Einträge unsortiert / Betroffene Token ) : "+str(len(sortedlist))+" / "+str(len(unsortedlist))+" / "+str(unsortedtypecount-sortedtypecount)+"\n")

    
normbag = {}
normambiquebag = {}
normgroupbag = {}
normuniquebag = {}

with open ("data/normmapping/_all.txt", "r", encoding="utf8") as inf:
    for line in inf:
        linearr = line.split("\t")
        norm = linearr[1]
        norm = norm[1:-1]
        if len(norm) > 0:
            normarr = norm.split("|")
            if(len(normarr)>1):
                if norm in normgroupbag:
                    normgroupbag[norm] = normgroupbag[norm]+1
                else:
                    normgroupbag[norm] = 1
                for key in normarr:
                    if key in normambiquebag:
                        normambiquebag[key] = normambiquebag[key]+1
                    else:
                        normambiquebag[key] = 1
                    
            for key in normarr:
                if key in normbag:
                    normbag[key] = normbag[key]+1
                else:
                    normbag[key] = 1

normuniquenessbag = {}
normunique = {}

for norm in normbag:
    insg = normbag[norm]
    if norm in normambiquebag:
        ambique = normambiquebag[norm]
    else:
        normambiquebag[norm] = 0
        ambique = 0
    unique = insg - ambique
    normunique[norm] = unique
    normuniquenessbag[norm] = unique / insg
with open("data/normmapping/_normuniqueness.txt", "w", encoding="utf8") as outf:
    for norm,value in sorted(normuniquenessbag.items(), key = lambda x:x[1], reverse=True):
        outf.write(norm+"\t"+str(normuniquenessbag[norm]) + "\t" + str(normunique[norm]) +"\t" + str(normambiquebag[norm]) + "\n")
        
