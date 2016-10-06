import app
import misc


from bs4 import BeautifulSoup
import os
import re
import time as time_module
import datetime

from config import FB_YEAR, MIN_VOTES, MAX_VOTES, DIARY_PAGE_ENCODING


# String storage
class VoteAux:
    def __init__(self, user, team, work, time_mark):
        self.time = time_mark
        self.user = user
        self.team = team
        self.work = work


def diary_str_to_datetime(string):
    parts = string.split(" ")
    date_parts = parts[0].split("-")
    time_parts = parts[2].split(":")
    return datetime.datetime(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]),
                             int(time_parts[0]), int(time_parts[1]) )


def get_votes_from_page(page_data):
    soup = BeautifulSoup(page_data, 'html.parser')
    comments = soup.find('div', {'id': 'commentsArea'})
    votes = comments.find_all('div', {'class': 'singleComment'})
    rePost = re.compile(r"<div style=['\"]min-height:40px['\"]>(.*)</div>")
    reSplit = re.compile("<br>")
    reExtractData = re.compile("^\s*(\d*)\.\s*fandom\s*([^\"]*)\s*" + FB_YEAR + "\s*([-—–―]\s*[\"“«](.+)[\"”»])?\s*$")

    votes_page = []

    for vote in votes:
        time_str = vote.find('div', {'class': 'postTitle'}).find('span').string
        post_time = diary_str_to_datetime(time_str)

        author = vote.find('div', {'class': 'authorName'}).find('strong').string

        contents = str(vote.find('div', {'class': 'postInner'}).find('div', {'style': 'min-height:40px'}))
        fixed_contents = contents.replace("</br>", "")  # BS4 adds closing br tags, we don't need them
        fixed_contents = misc.remove_cycles(fixed_contents)  # Remove cycles.
        res = rePost.search(fixed_contents)
        if res is None:
            print('HTML failure', author)
            continue
        team_votes = reSplit.split(res.group(1))
        post_votes = []
        for line in team_votes:
            if len(line.strip()) == 0:
                continue
            voteInfo = reExtractData.search(line)
            if voteInfo is None:
                print(author + ": некорректная строчка:", line)
                continue
            if voteInfo.group(3) is None:
                work_name = None
            else:
                work_name = misc.standardize(voteInfo.group(4))

            team = misc.standardize(voteInfo.group(2).strip())
            if team[-1] == ';':  # some bs4 magic
                team = team[0:-1]
            position = int(voteInfo.group(1))  # in the old times, this actually mattered...

            post_votes.append(VoteAux(author, team, work_name, post_time))

        # check if the amount of correct votes is right
        correct_lines = len(list(filter(lambda x: len(x.strip()) > 0, team_votes)))
        if correct_lines < MIN_VOTES or correct_lines > MAX_VOTES:
            print("Неправильное число команд:", author, correct_lines)
            continue
        # remove old votes, if they are present
        votes_page = list(filter(lambda x: x.user != author, votes_page))
        votes_page += post_votes
    return votes_page


def add_votes_to_db(votes, quest_prefix):
    quest = app.db.session.query(app.models.Quest).filter_by(prefix=quest_prefix).one()

    if app.db.session.query(app.models.Work).filter_by(quest_id=quest.id).count() > 0:
        works_present_in_quest = True
    else:
        works_present_in_quest = False

    # Create map of team's works to avoid many queries to DB
    work_data_db = app.db.session.query(app.models.Team, app.models.Work) \
        .filter(app.models.Work.quest_id == quest.id).filter(app.models.Team.id == app.models.Work.team_id).all()
    team_ids = {x.name: x.id for x in app.models.Team.query.all()}
    work_base = {x : [] for x in team_ids}
    work_ids = {}
    for entry in work_data_db:
        team = entry[0].name
        work = entry[1].name
        work_base[team].append(work)
        work_ids[(team, work)] = entry[1].id

    # add new users
    current_users = [x[0] for x in app.db.session.query(app.models.User.name).distinct(app.models.User.name).all()]
    voted_users = list(set([x.user for x in votes]))
    new_users_names = [x for x in voted_users if x not in current_users]
    print(len(current_users), "in base,", len(voted_users), "voted,", len(new_users_names), "were added")
    new_users = [app.models.User(name=x) for x in new_users_names]
    app.db.session.bulk_save_objects(new_users)

    user_ids = {x.name: x.id for x in app.db.session.query(app.models.User).distinct(app.models.User.name).all()}
    votes_to_add = []
    for vote in votes:
        user_id = user_ids[vote.user]
        if vote.team not in team_ids:
            print(vote.user + ": team not found: ", "{" + vote.team + "}")
            status = app.models.Vote.status_team_not_found()
            work_id = None
        elif works_present_in_quest:
            if vote.work not in work_base[vote.team]:
                print(vote.user + ": work not found: ", "{" + str(vote.work) + "}")  # 'work' may be None
                status = app.models.Vote.status_work_not_found()
                work_id = None
            else:
                status = app.models.Vote.status_valid()
                work_id = work_ids[(vote.team, vote.work)]
        else:  # works are not present in this quest
            work_id = None
            status = app.models.Vote.status_valid()

        #team_id = team_ids[vote.team]

        votes_to_add.append(app.models.Vote(quest_id=quest.id,
                                            user_id=user_id,
                                            work_id=work_id,
                                            status=status,
                                            time=vote.time))
    app.db.session.bulk_save_objects(votes_to_add)
    print("Added", len(votes_to_add), "votes")
    app.db.session.commit()




#
#   Script
#
quest_prefix = "L2_Q2"
download_folder = "downloaded"


q = app.db.session.query(app.models.Quest).filter_by(prefix=quest_prefix).one()

files = list(filter(lambda x: x.startswith(quest_prefix), os.listdir(download_folder)))

votes = []
t0 = time_module.time()

for file in files:
    print("Parsing", file)
    votes += get_votes_from_page(open(os.path.join(download_folder, file), "r", encoding=DIARY_PAGE_ENCODING).read())

add_votes_to_db(votes, quest_prefix)
t1 = time_module.time()
print("Done in", t1-t0)