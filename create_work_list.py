import re
from bs4 import BeautifulSoup
import downloader
import app
import misc
import sys
import os
import yaml
from config import FB_YEAR, DIARY_LOGIN, DIARY_PASSWORD, DIARY_POSTS_PER_PAGE, DIARY_PAGE_ENCODING

extracter1 = re.compile("#.\s*fandom\s*([^\"«“]*)\s*" + FB_YEAR + "\s*[-—–―]\s*\"([^\"]+)\"")
extracter2 = re.compile("#.\s*fandom\s*([^\"«“]*)\s*" + FB_YEAR + "\s*[-—–―]\s*«([^»]+)»")
extracter3 = re.compile("#.\s*fandom\s*([^\"«“]*)\s*" + FB_YEAR + "\s*[-—–―]\s*“([^”]+)”")


def extract_works(string):
    works1 = re.findall(extracter1, string)
    works2 = re.findall(extracter2, string)
    works3 = re.findall(extracter3, string)
    works = works1 + works2 + works3
    return works

err_page_num = 0


class WorkAux:
    def __init__(self, quest, name, url):
        self.quest = quest
        self.name = name
        self.url = url


def parse_works(data, quest_prefix, result):
    global err_page_num
    soup = BeautifulSoup(data, 'html.parser')
    posts = soup.find_all('div', {'class': 'singlePost'})
    urls = [x.find('a')['href']
            for x in soup.find_all('div', {'class': 'postLinksBackg'})]
    # print("Found posts:", len(posts))
    if len(posts) != len(urls):
        raise Exception('Content type mismatch' + str(len(posts)) + str(len(urls)))
    for post, url in zip(posts, urls):
        header = post.find('div', {'class': 'postTitle'}).find('h2').text  # post header. For debug, really.
        post_str = str(post)
        works = extract_works(post_str) # a list of RE results
        for work in works:
            team_name = misc.standardize(work[0])
            if team_name[-1] == ';':  # those appear mystically when the team name have a '&' in its name
                team_name = team_name[0:-1]
            name = misc.standardize(re.sub("\s+", ' ', work[1]))

            work = WorkAux(quest_prefix, name, url)
            if team_name not in result:
                result[team_name] = []
            result[team_name].append(work)


def write_work_list(quest_prefix):
    q = app.db.session.query(app.models.Quest).filter_by(prefix=quest_prefix).one()

    baseUrl = q.catalog_url + "&from="
    nPages = q.catalog_pages

    loader = downloader.PostDownloader(DIARY_LOGIN, DIARY_PASSWORD)

    total_works = {}

    for i in range(nPages):
        print("Downloading ", i + 1, " out of ", nPages)
        n = i * DIARY_POSTS_PER_PAGE
        url = baseUrl + str(n)
        page = loader.GetPageAsString(url)
        print("Parsing...")
        parse_works(page.decode(DIARY_PAGE_ENCODING), quest_prefix, total_works)

    fname = "data/" + quest_prefix + "_WORKS.yaml"

    fp = open(fname, "w", encoding="utf8")

    for team in total_works:
        fp.write("\"" + team + "\":\n")
        for work in total_works[team]:
            work_escaped = re.sub("\"", "\\\"", work.name)
            fp.write("  - name: \"" + work_escaped + "\"\n")
            fp.write("    url: " + work.url + "\n")

    fp.close()
#
#   The Script
#
sys.setrecursionlimit(10000)  # Some posts are freakin' deep!
quests = app.db.session.query(app.models.Quest).filter(app.models.Quest.catalog_url != None).all()
for quest in quests:
    if os.path.isfile("data/" + quest.prefix + "_WORKS.yaml"):
        continue
    write_work_list(quest.prefix)



