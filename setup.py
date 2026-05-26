from urllib.request import urlopen
from urllib.parse import urlencode
import os
import sys
import subprocess

ns = sys.argv[1]

if (len(sys.argv)==3):
    count = sys.argv[2]
else:
    count = -1
print(str(count)+" documents from " +ns)
if os.path.exists("_error.txt"):
    os.remove("_error.txt")
    
with open("config_def.py", "r", encoding="utf8") as confdef:
    with open("config.py", "w", encoding="utf8") as conf:
        for line in confdef:
            if line.startswith("ctsns"):
                line = 'ctsns="'+ns+'"\n'
            if line.startswith("count"):
                line = 'count='+str(count)+'\n'
            conf.write(line)
            
confstr = ""

print(ns)

def run(cmdarr):
    print("\n#########"+str(cmdarr)+"###########")
    subprocess.run(cmdarr)
    
run(["python3","_bagofwords.py"])
run(["python3","_charmix.py"])
run(["python3","_singleusewords.py"])
run(["python3","_metadata.py"])
run(["python3","_authors.py"])
run(["python3","_characters.py"])
run(["python3","_lemmatisierowasch.py"])
run(["python3","_lemmaeval.py"])
run(["python3","_normierowasch.py"])
run(["python3","_normeval.py"])
run(["python3","_ngram.py","2"])
run(["python3","_ngram.py","3"])
run(["python3","_ngram.py","5"])
run(["python3","_collocation.py"])
run(["python3","_spoznajrec.py","3"])
run(["python3","_psedcytas.py","3"])
#subprocess.run(["python3","_zelenjerec.py","3"])
run(["python3","_stats.py"]) 
run(["python3","_typorecognition.py"]) 
run(["python3","_docu.py"]) 


