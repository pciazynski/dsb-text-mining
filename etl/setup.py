from urllib.request import urlopen
from urllib.parse import urlencode
import os
import sys
import subprocess
import shutil

import settings


def run(cmdarr):
    print("\n#########" + str(cmdarr) + "###########")
    subprocess.run(cmdarr)


def main(argv=None):
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    if argv is None:
        argv = sys.argv[1:]
    ns = argv[0]
    count = argv[1] if len(argv) == 2 else -1
    print(str(count) + " documents from " + ns)
    error_log = settings.datadir + "_ERROR.txt"
    if os.path.exists(error_log):
        os.remove(error_log)
    passage_cache = os.path.join(settings.datadir, "passagecache")
    if os.path.exists(passage_cache):
        shutil.rmtree(passage_cache)

    with open("config_def.py", "r", encoding="utf8") as confdef:
        with open("config.py", "w", encoding="utf8") as conf:
            for line in confdef:
                if line.startswith("ctsns"):
                    line = 'ctsns="' + ns + '"\n'
                if line.startswith("count"):
                    line = "count=" + str(count) + "\n"
                conf.write(line)

    print(ns)
    run(["python3", "bagofwords.py"])
    run(["python3", "lemmatisierowasch.py"])
    run(["python3", "lemmaeval.py"])
    run(["python3", "normierowasch.py"])
    run(["python3", "normeval.py"])
    run(["python3", "psedcytas.py", "3"])
    run(["python3", "docu.py"])


if __name__ == "__main__":
    main()
