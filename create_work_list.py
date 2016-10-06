import re
from bs4 import BeautifulSoup
import downloader
import app
import misc
import sys
import html
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


def parse_works(data, quest_prefix):
    global err_page_num
    soup = BeautifulSoup(data, 'html.parser')
    posts = soup.find_all('div', {'class': 'singlePost'})
    urls = [x.find('a')['href']
            for x in soup.find_all('div', {'class': 'postLinksBackg'})]
    #print("Found posts:", len(posts))
    if len(posts) != len(urls):
        raise Exception('Content type mismatch' + str(len(posts)) + str(len(urls)))
    q = app.db.session.query(app.models.Quest).filter_by(prefix=quest_prefix).one()
    error_written = False
    for post in posts:
        header = post.find('div', {'class': 'postTitle'}).find('h2').text  # post header. For debug, really.
        post_str = str(post)
        works = extract_works(post_str)
        for work in works:
            team_name = misc.standardize(work[0])
            if team_name[-1] == ';':  # those appear mystically when the team name have a '&' in its name
                team_name = team_name[0:-1]
            name = misc.standardize(re.sub("\s+", ' ', work[1]))

            team = app.db.session.query(app.models.Team).filter_by(name=team_name).first()
            if team is None:
                print("Team not found", "{" + team_name + "}", " for work", work[1] )
                if not error_written:
                    #print(str(post))

                    #file = open(team_name + work[1], "w",  encoding="utf8")
                    #file.write(str(post))
                    #file.close()

                    err_page_num += 1
                    error_written = True
                continue

            work = app.models.Work(quest_id=q.id, team_id=team.id, name=name)
            app.db.session.add(work)
    app.db.session.commit()

#
#   The Script
#

quest_prefix = "L2_Q1"

sys.setrecursionlimit(1500)  # Some posts are freakin' deep!

q = app.db.session.query(app.models.Quest).filter_by(prefix=quest_prefix).one()

baseUrl = q.catalog_url + "&from="
nPages = q.catalog_pages


loader = downloader.PostDownloader(DIARY_LOGIN, DIARY_PASSWORD)

for i in range(nPages):
    print("Downloading ", i + 1, " out of ", nPages)
    n = i * DIARY_POSTS_PER_PAGE
    url = baseUrl + str(n)
    page = loader.GetPageAsString(url)
    print("Parsing...")
    parse_works(page.decode(DIARY_PAGE_ENCODING), quest_prefix)
