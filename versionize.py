import datetime

with open("version.txt", "w", encoding="utf8") as outf:
    outf.write(str(datetime.datetime.now()))