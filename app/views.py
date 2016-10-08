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

        quests = db.session.query(models.Quest).order_by(models.Quest.prefix).all()
        self.last_update = db.session.query(func.max(models.Vote.time)).one()[0]

        self.quest_ratings_links = PagesPerQuest("Рейтинг по квестам",
                                           [Link(x.name, url_for('quest_rating', quest_prefix=x.prefix)) for x in quests])
        self.work_ratings_links = PagesPerQuest("Рейтинг по работам",
                                          [Link(x.name, url_for('work_rating', quest_prefix=x.prefix)) for x in quests])
        self.error_ratings_links = PagesPerQuest("Ошибки в голосах",
                                                [Link(x.name, url_for('error_rating', quest_prefix=x.prefix)) for x in
                                                 quests])
        self.team_select = Link("Работы по командам", url_for('select_team'))


@app.route('/')
def index():
    return render_template('base.html', page_title="Brazilian laboratories: статистика ФБ-2016", navbar_info=NavBarInfo())


@app.route('/totalrating')
def total_rating():
    rating = db.session.query(models.Team.name, models.Team.id, func.count(models.Vote.id)).\
        filter(models.Vote.status == models.Vote.status_valid()).\
        filter(models.Vote.team_id == models.Team.id).group_by(models.Team.name).all()
    rating.sort(key=lambda x: -x[2])
    rated = [(Link(x[0], url_for('team_info', team_id=x[1])), x[2]) for x in rating]
    return render_template('basic_rating.html',
                           rating=rated,
                           page_title="Общий рейтинг по всем квестам",
                           navbar_info=NavBarInfo())

@app.route('/totalratingdetailed')
def total_rating_detalied():
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
    of_results = db.session.query(models.OfficialResult).filter_by(quest_id=quest.id).all()
    if len(of_results) == 0:
        rating = db.session.query(models.Team.name, models.Team.id, func.count(models.Vote.id)).\
            filter(models.Vote.status == models.Vote.status_valid()). \
            filter(models.Vote.quest_id == quest.id). \
            filter(models.Vote.team_id == models.Team.id).group_by(models.Team.name).all()
        rating.sort(key=lambda x: -x[2])
        rated = [(Link(x[0], url_for('team_info', team_id=x[1])), x[2]) for x in rating]
        descr = "Предварительный рейтинг"
    else:
        of_results.sort(key=lambda x: -x.result)
        rated = [(Link(x.team.name, url_for('team_info', team_id=x.team.id)), x.result) for x in of_results]
        descr = "Официальные результаты"

    return render_template('basic_rating.html',
                           rating=rated,
                           description=descr,
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

@app.route('/team/<team_id>')
def team_info(team_id):
    team = db.session.query(models.Team.name).filter_by(id=team_id).first()
    if team is None:
        return render_template('team_info.html',
                               works=None,
                               page_title= "Команда не найдена: " + str(team_id),
                               navbar_info=NavBarInfo())
    data = db.session.query(models.Quest.name, models.Work.name, models.Work.url, func.count(models.Vote.id)). \
        filter(models.Vote.status == models.Vote.status_valid()). \
        filter(models.Vote.work_id == models.Work.id). \
        filter(models.Work.team_id == team_id). \
        filter(models.Vote.quest_id == models.Quest.id).group_by(models.Work.name).all()

    class WorkAux:
        def __init__(self, work, points):
            self.work = work
            self.points = points
    works = {}
    for work in data:
        quest = work[0]
        if quest not in works:
            works[quest] = []
        works[quest].append(WorkAux(Link(work[1], work[2]), work[3]))

    return render_template('team_info.html',
                           works=works,
                           page_title="Работы команды " + team.name,
                           navbar_info=NavBarInfo())


@app.route('/selectteam/')
def select_team():
    teams = db.session.query(models.Team).order_by(models.Team.name).all()
    team_table = [Link(x.name, url_for('team_info', team_id = x.id)) for x in teams]
    return render_template('team_select.html',
                           page_title="Выбор команды",
                           teams=team_table,
                           navbar_info=NavBarInfo())
