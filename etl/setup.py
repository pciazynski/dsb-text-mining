from urllib.request import urlopen
from urllib.parse import urlencode
import os
import sys
import subprocess

os.chdir(os.path.dirname(os.path.abspath(__file__)))

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
    
run(["python3","bagofwords.py"])
run(["python3","lemmatisierowasch.py"])
run(["python3","lemmaeval.py"])
run(["python3","normierowasch.py"])
run(["python3","normeval.py"])
run(["python3","psedcytas.py","3"])
run(["python3","docu.py"]) 


