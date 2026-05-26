python3 versionize.py
set /p "msg=Kommentar: "
git pull
git add *
git commit -a -m "%msg%"
git push
timeout 5