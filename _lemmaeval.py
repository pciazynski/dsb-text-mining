import os

bw = {}
bl = {}
incons = 0 
with open ("data/lemmamapping/_all.txt", "r", encoding="utf8") as bwin, open ("data/lemmamapping/_inconsistencies.txt", "w", encoding="utf8") as incout:
    for line in bwin:
        linearr = line.split("\t")
        if linearr[0] in bl:
            incout.write(linearr[0]+"\n")
            incons+=1
            bl[linearr[0]] = bl[linearr[0]] +1
            if bl[linearr[0]] > 2:
                print(linearr[0])

        bl[linearr[0]] = 1

unlem = 0
lem = 0
progress = {}

with open ("data/bagofwords/_all.txt", "r", encoding="utf8") as bwin, open ("data/lemmamapping/_yay.txt", "w", encoding="utf8") as outlem,open ("data/lemmamapping/_nay.txt", "w", encoding="utf8") as outunlem:
    for line in bwin:
        linearr = line.split("\t")
        if linearr[0] in bl:
            outlem.write(line)
            progress[line.strip()] = 1
            lem += 1
        else:
            unlem += 1
            outunlem.write(line)
            progress[line.strip()] = 0

with open ("data/lemmamapping/_progress.txt", "w", encoding="utf8") as outlemprogress:
    for line,value in sorted(progress.items(), key = lambda x:x[1], reverse=True):
        outlemprogress.write(line+"\t"+str(progress[line]) + "\n")
    
unsortedlist = {}
sortedlist =  {}

sortedtypecount = 0
unsortedtypecount = 0

with open("data/lemmamapping/_lemmabag.txt","r", encoding="utf8") as inf:
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
#            else:
#                handle sorting-redundancies    
#                print(line+"->"+"|".join(linearr))
            sortedlist["|".join(linearr)] = 1


with open ("data/lemmamapping/_stats.txt", "w", encoding="utf8") as out:
    out.write("Lemmatisiert / Alle: "+str(lem)+" / "+str(lem+unlem)+"\n")
    out.write("Inkonsistent: "+str(incons)+"\n")
    out.write("Sortierungsredundanz (ambige Einträge sortiert / ambige Einträge unsortiert / Betroffene Token ) : "+str(len(sortedlist))+" / "+str(len(unsortedlist))+" / "+str(unsortedtypecount-sortedtypecount)+"\n")

lemmabag = {}
lemmaambiquebag = {}
lemmagroupbag = {}
lemmauniquebag = {}

with open ("data/lemmamapping/_all.txt", "r", encoding="utf8") as inf:
    for line in inf:
        linearr = line.split("\t")
        lemma = linearr[1]
        lemma = lemma[1:-1]
        if len(lemma) > 0:
            lemmaarr = lemma.split("|")
            if(len(lemmaarr)>1):
                if lemma in lemmagroupbag:
                    lemmagroupbag[lemma] = lemmagroupbag[lemma]+1
                else:
                    lemmagroupbag[lemma] = 1
                for key in lemmaarr:
                    if key in lemmaambiquebag:
                        lemmaambiquebag[key] = lemmaambiquebag[key]+1
                    else:
                        lemmaambiquebag[key] = 1
                    
            for key in lemmaarr:
                if key in lemmabag:
                    lemmabag[key] = lemmabag[key]+1
                else:
                    lemmabag[key] = 1

lemmauniquenessbag = {}
lemmaunique = {}

for lemma in lemmabag:
    insg = lemmabag[lemma]
    if lemma in lemmaambiquebag:
        ambique = lemmaambiquebag[lemma]
    else:
        lemmaambiquebag[lemma] = 0
        ambique = 0
    unique = insg - ambique
    lemmaunique[lemma] = unique
    lemmauniquenessbag[lemma] = unique / insg
with open("data/lemmamapping/_lemmauniqueness.txt", "w", encoding="utf8") as outf:
    for lemma,value in sorted(lemmauniquenessbag.items(), key = lambda x:x[1], reverse=True):
        outf.write(lemma+"\t"+str(lemmauniquenessbag[lemma]) + "\t" + str(lemmaunique[lemma]) +"\t" + str(lemmaambiquebag[lemma]) + "\n")
        


        

