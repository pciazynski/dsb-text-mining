import os
import shutil

word_lemma = {}
lemma_wordbag = {}
coords = {}
lemmacoords = {}

counter = 0
#Funktioniert nicht wegen Orten, die aus mehreren Token bestehen wie Adamowa Kjarcma und Alt-Zauche

def reset():
    if not os.path.exists("data"):
        os.mkdir("data")
    if os.path.exists("data/mjenjoweda"):
        shutil.rmtree("data/mjenjoweda")
    os.mkdir("data/mjenjoweda")
reset()

print("Reading coord")
#lese ortsliste mit koordinaten als coords
with open ("learn/ortsliste.txt","r",encoding="utf8") as oin:
    for line in oin:
        linearr = line.split("\t")
        tmp = linearr[0].lower()
        coords[tmp] = linearr[1].replace("PLACE_","").strip()

print("finding relevant lemma")
#wenn token in coords, erzeuge lemmawordbag für lemma und uebertrage tokencoord in lemmacoord
with open ("data/lemmamapping/_all.txt", "r", encoding="utf8") as bwin:
    for line in bwin:
        linearr = line.split("\t")
        if linearr[0] in coords:
            lemma_wordbag[linearr[1]] = {}
            lemmacoords[linearr[1]] = coords[linearr[0]]

print("mapping lemma to token")
#für jedes lemma in lemmawordbag...
with open ("data/lemmamapping/_all.txt", "r", encoding="utf8") as bwin:
    for line in bwin:
        linearr = line.split("\t")
        if linearr[1] in lemma_wordbag:
#, wenn ein wort nicht damit verknüpft ist, verknüpfe es
            if not (linearr[0]) in lemma_wordbag[linearr[1]]:
                tmp = lemma_wordbag[linearr[1]]
                tmp[linearr[0]] = 1
                lemma_wordbag[linearr[1]] = tmp

print("writing")
with open("data/mjenjoweda/ortsliste.txt", "w", encoding="utf8") as ortslisteout,open("data/mjenjoweda/ortsinfo.txt", "w", encoding="utf8") as ortsinfoout:
    for lemma in sorted(lemma_wordbag):
        tmp = "|"
        for word in lemma_wordbag[lemma]:
            tmp+=word+"|"
        ortslisteout.write(lemma+"\t"+tmp+"\n")
        ortsinfoout.write(lemma+"\t"+lemmacoords[lemma]+"\n")
    
print("Done")
