import re
from app import db, models
from config import FB_YEAR
import misc

fname = "data/call_post.txt"

data = open(fname, "r").readlines()

for line in data:
    res = re.search(r"fandom\s*(.+)\s*" + FB_YEAR, line)
    if res is None:
        if len(line.strip()) > 0:
            print("invalid line", line)
        continue
    name = misc.standardize(res.group(1))
    #print(name)
    t = models.Team(name=name)
    db.session.add(t)
db.session.commit()


