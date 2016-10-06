from flask import render_template, url_for
from app import app, db, models
from sqlalchemy import func


class Link:
    def __init__(self, text, url):

        self.text = text
        self.url = url


class NavBarInfo:
    def __init__(self):
        self.main_page = Link("Домашняя страница", url_for('index'))
        self.total_rating = Link("Общий рейтинг", url_for('total_rating'))

        quests = db.session.query(models.Quest).all()
        self.quest_ratings = [Link(x.name, url_for('quest_rating', quest_prefix=x.prefix)) for x in quests]
        self.work_ratings = [Link(x.name, url_for('work_rating', quest_prefix=x.prefix)) for x in quests]


@app.route('/')
def index():
    return render_template('base.html', page_title="Brazilian laboratories: статистика ФБ-2016", navbar_info=NavBarInfo())


@app.route('/totalrating')
def total_rating():
    rating = db.session.query(models.Team.name, func.count(models.Vote.id)).\
        filter(models.Vote.status == models.Vote.status_valid()).\
        filter(models.Vote.team_id == models.Team.id).group_by(models.Team.name).all()
    rating.sort(key=lambda x: -x[1])
    return render_template('basic_rating.html',
                           rating=rating,
                           page_title="Общий рейтинг по всем квестам",
                           navbar_info=NavBarInfo())

@app.route('/rating/<quest_prefix>')
def quest_rating(quest_prefix):
    quest = db.session.query(models.Quest).filter_by(prefix=quest_prefix).first()
    if quest is None:
        return render_template('basic_rating.html',
                               rating=[],
                               page_title="Квест не найден: " + quest_prefix,
                               navbar_info=NavBarInfo())
    rating = db.session.query(models.Team.name, func.count(models.Vote.id)).\
        filter(models.Vote.status == models.Vote.status_valid()). \
        filter(models.Vote.quest_id == quest.id). \
        filter(models.Vote.team_id == models.Team.id).group_by(models.Team.name).all()
    rating.sort(key=lambda x: -x[1])
    return render_template('basic_rating.html',
                           rating=rating,
                           page_title="Рейтинг за " + quest.name,
                           navbar_info=NavBarInfo())

@app.route('/works/<quest_prefix>')
def work_rating(quest_prefix):
    quest = db.session.query(models.Quest).filter_by(prefix=quest_prefix).first()
    if quest is None:
        return render_template('basic_rating.html',
                               rating=[],
                               page_title="Квест не найден: " + quest_prefix,
                               navbar_info=NavBarInfo())
    rating = db.session.query(models.Work.name, models.Team.name, func.count(models.Vote.id)).\
        filter(models.Vote.status == models.Vote.status_valid()). \
        filter(models.Vote.work_id == models.Work.id). \
        filter(models.Work.team_id == models.Team.id). \
        filter(models.Vote.quest_id == quest.id).group_by(models.Work.name).all()
    print(rating)
    rating.sort(key=lambda x: -x[2])
    return render_template('work_rating.html',
                           rating=rating,
                           page_title="Рейтинг работ за " + quest.name,
                           navbar_info=NavBarInfo())