import app

import os
import yaml


def add_works_to_db(data, quest_prefix):
    quest = app.db.session.query(app.models.Quest).filter_by(prefix=quest_prefix).one()

    for team_name in data:
        team = app.db.session.query(app.models.Team).filter_by(name=team_name).first()
        if team is None:
            print("Team not found:", team_name)
            continue
        for work in data[team_name]:
            work = app.models.Work(quest_id=quest.id,
                                   team_id=team.id,
                                   name=work["name"],
                                   url=work["url"])
            app.db.session.add(work)
    app.db.session.commit()


quests = app.db.session.query(app.models.Quest).filter(app.models.Quest.catalog_url != None).all()
for quest in quests:
    fname = "data/" + quest.prefix + "_WORKS.yaml"
    print("Loading ", fname)
    if not os.path.isfile(fname):
        continue
    data = yaml.load(open(fname, "r", encoding="utf8").read())
    add_works_to_db(data, quest.prefix)
