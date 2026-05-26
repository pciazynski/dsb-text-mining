import os

tab = "\t"
nl = "\n"

bwonetime = dict()
bwonetimeyear = dict()
with open ("data/bagofwords/_all.txt","r",encoding="utf8") as bwin:
    for line in bwin:
        linearr = line.split(tab)
        if int(linearr[1]) == 1:
            bwonetime[linearr[0]] = 1

for file in os.listdir("data/bagofwordsperyear"):
    with open("data/bagofwordsperyear/"+file, "r", encoding="utf8") as inf:
        for line in inf:
            linearr = line.split(tab)
            if linearr[0] in bwonetime:
                bwonetimeyear[linearr[0]] = file.split(".")[0]

with open("data/bagofwords/_singleusewords.txt", "w", encoding="utf8") as outf:
    for token,value in sorted(bwonetimeyear.items(), key = lambda x:x[1], reverse=False):
        outf.write(token+tab + str(value)+nl)
