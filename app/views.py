from flask import render_template, url_for
from app import app, db, models
from sqlalchemy import func


class Link:
    def __init__(self, text, url):

        self.text = text
        self.url = url


class PagesPerQuest:
    def __init__(self, title, links):
        self.title = title
        self.links = links


class NavBarInfo:
    def __init__(self):

        self.main_page = Link("Домашняя страница", url_for('index'))
        self.total_rating = Link("Общий рейтинг", url_for('total_rating'))

        quests = db.session.query(models.Quest).all()
        self.last_update = db.session.query(func.max(models.Vote.time)).one()[0]

        self.quest_ratings_links = PagesPerQuest("Рейтинг по квестам",
                                           [Link(x.name, url_for('quest_rating', quest_prefix=x.prefix)) for x in quests])
        self.work_ratings_links = PagesPerQuest("Рейтинг по работам",
                                          [Link(x.name, url_for('work_rating', quest_prefix=x.prefix)) for x in quests])
        self.error_ratings_links = PagesPerQuest("Ошибки в голосах",
                                                [Link(x.name, url_for('error_rating', quest_prefix=x.prefix)) for x in
                                                 quests])



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
    rating = db.session.query(models.Work.name, models.Work.url, models.Team.name, func.count(models.Vote.id)).\
        filter(models.Vote.status == models.Vote.status_valid()). \
        filter(models.Vote.work_id == models.Work.id). \
        filter(models.Work.team_id == models.Team.id). \
        filter(models.Vote.quest_id == quest.id).group_by(models.Work.name).all()

    rating.sort(key=lambda x: -x[3])
    return render_template('work_rating.html',
                           rating=rating,
                           page_title="Рейтинг работ за " + quest.name,
                           navbar_info=NavBarInfo())



@app.route('/errors/<quest_prefix>')
def error_rating(quest_prefix):
    quest = db.session.query(models.Quest).filter_by(prefix=quest_prefix).first()
    if quest is None:
        return render_template('basic_rating.html',
                               rating=[],
                               page_title="Квест не найден: " + quest_prefix,
                               navbar_info=NavBarInfo())
    errors = db.session.query(models.Vote, models.User.name).\
        filter(models.Vote.status != models.Vote.status_valid()).\
        filter(models.Vote.quest_id == quest.id). \
        filter(models.Vote.user_id == models.User.id).all()

    class ErrorDescr:
        def __init__(self, time, user, msg):
            self.time = time
            self.user = user
            self.msg = msg

    def status_to_msg(vote):
        if vote.status == models.Vote.status_invalid_num_teams():
            return "Неверное число команд: " + vote.err_line
        if vote.status == models.Vote.status_invalid_line():
            return "Некорректная строчка: " + vote.err_line
        if vote.status == models.Vote.status_team_not_found():
            return "Команда не найдена: " + vote.err_line
        if vote.status == models.Vote.status_work_not_found():
            return "Работа не найдена: " + vote.err_line
        return "Неизвестная ошибка: " + str(vote.status)

    error_ratings = [ErrorDescr(x[0].time, x[1], status_to_msg(x[0])) for x in errors]

    return render_template('error_rating.html',
                           errors=error_ratings,
                           page_title="Ошибки в голосах за " + quest.name,
                           navbar_info=NavBarInfo())