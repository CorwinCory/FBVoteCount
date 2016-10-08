import yaml
import downloader
import bs4
import re
import misc
from app import db, models
from config import  DIARY_LOGIN, DIARY_PASSWORD, DIARY_PAGE_ENCODING, FB_YEAR

class OfResultAux:
    def __init__(self, team, points):
        self.team = team
        self.points = points

def extract_of_results(page):
    soup = bs4.BeautifulSoup(page, 'html.parser')
    table = soup.find("table")
    if table is None:
        raise Exception("No table in of results!")
    rows = table.find_all("tr")
    results = []
    for row in rows:
        columns = row.find_all("td")
        if len(columns) == 0:  # header contains th instead of td
            continue
        team_full = columns[1].text # with 'fandom' and year
        team_name = re.search("fandom\s*(.*)\s*" + FB_YEAR, team_full).groups()[0]
        team_name = misc.standardize(team_name)
        if team_name[-1] == ';':
            team_name = team_name[0:-1]
        result = int(columns[2].text)

        results.append(OfResultAux(team_name, result))
    return results


#
#   The script
#
fname = "data/questDescription.yaml"

quests = yaml.load(open(fname, encoding="utf8").read())
loader = downloader.PostDownloader(DIARY_LOGIN, DIARY_PASSWORD)

teams = db.session.query(models.Team).all()

team_ids = {x.name: x.id for x in teams}

for prefix in quests:
    print("Adding", prefix)
    name = quests[prefix]["name"]
    catalog = quests[prefix]["catalogURL"]
    if catalog == "None":
        catalog = None
    nPages = int(quests[prefix]["catalogPages"])
    urls = quests[prefix]["votePages"]
    quest = db.session.query(models.Quest).filter_by(prefix=prefix).first()
    if quest is None:
        quest = models.Quest(prefix=prefix, name=name, catalog_url=catalog, catalog_pages=nPages)
        db.session.add(quest)
        db.session.commit()
    for url in urls:
        page = models.VotePage(url=url, quest=quest, parsed=False)
        db.session.add(page)
    if "officialResults" in quests[prefix]:
        off_url = quests[prefix]["officialResults"]
        data = loader.GetPageAsString(off_url).decode(DIARY_PAGE_ENCODING)
        results = extract_of_results(data)
        to_add = [models.OfficialResult(quest_id=quest.id, team_id=team_ids[x.team], result=x.points) for x in results]
        db.session.bulk_save_objects(to_add)


    db.session.commit()
