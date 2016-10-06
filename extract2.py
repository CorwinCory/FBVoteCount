import re
from bs4 import BeautifulSoup
import html
import misc

fname = "L2_Q1_1.html"


def get_votes(page_data):
    soup = BeautifulSoup(page_data, 'html.parser')
    comments = soup.find('div', {'id': 'commentsArea'})
    votes = comments.find_all('div', {'class': 'singleComment'})
    rePost  = re.compile(r"<div style=['\"]min-height:40px['\"]>(.*)</div>");
    reSplit = re.compile("<br>");
    reExtractData = re.compile("^\s*(\d*)\.\s*fandom\s*([^\"]*)\s*" + "2016" + "\s*([-—–―]\s*[\"“«](.+)[\"”»])?\s*$");

    for vote in votes:
        time = vote.find('div', {'class': 'postTitle'}).find('span').string
        author = vote.find('div', {'class': 'authorName'}).find('strong').string
        contents = str(vote.find('div', {'class': 'postInner'}).find('div', {'style':'min-height:40px'}))
        fixed_contents = contents.replace("</br>", "") # BS4 adds closing br tags, we don't need them
        fixed_contents = misc.remove_cycles(fixed_contents) # Remove cycles.
        res = rePost.search(fixed_contents)
        if res is None:
            print('HTML failure', author)
            continue
        teamVotes = reSplit.split(res.group(1))
        correctLines = 0
        for line in teamVotes:
            if len(line.strip()) == 0:
                continue
            voteInfo = reExtractData.search(line)
            if voteInfo is None:
                print(author + ": некорректная строчка:", line)
                continue
            if res.group(3) is None:
                workName = None
            else:
                workName = misc.standardize(res.group(4));
            team = misc.standardize(res.group(2).strip());
            position = int(res.group(1));

            correctLines += 1 #one more correct vote
  
        # check if the amount of correct votes is right
        
    print("Found ", len(votes))

data = open(fname, "r", encoding='cp1251').read();

get_votes(data)
