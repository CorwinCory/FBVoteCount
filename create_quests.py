import re
from app import db, models

fname = "data/questDescription.txt"

quests = re.split("\n\n", open(fname, encoding="utf8").read())
for quest in quests:
    lines = quest.split("\n")
    ind = lines[0].find(' ')
    prefix = lines[0][0:ind]
    name = lines[0][ind+1:]
    catalog = lines[1]
    if catalog == "None":
        catalog = None
    nPages = int(lines[2])
    urls = lines[3:]
    print(prefix, name, urls)
    q = db.session.query(models.Quest).filter_by(prefix=prefix).first()
    if q is None:
        q = models.Quest(prefix=prefix, name=name, catalog_url=catalog, catalog_pages=nPages)
        db.session.add(q)
        db.session.commit()
    for url in urls:
        page = models.VotePage(url=url, quest=q, parsed=False)
        db.session.add(page)
    db.session.commit()
