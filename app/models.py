from app import db


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)

    # Back refs
    works = db.relationship('Work', backref='team', lazy='dynamic')


class Quest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prefix = db.Column(db.String(10), unique=True)
    name = db.Column(db.String(64), index=True, unique=True)

    catalog_url = db.Column(db.String(256), default=None)
    catalog_pages = db.Column(db.Integer,  default=None)

    # Back refs
    vote_pages = db.relationship('VotePage', backref='quest', lazy='dynamic')
    votes = db.relationship('Vote', backref='quest', lazy='dynamic')


class VotePage(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    quest_id = db.Column(db.Integer, db.ForeignKey('quest.id'), nullable=False)

    url = db.Column(db.String(1024))
    parsed = db.Column(db.Boolean, default=False)


class Work(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    quest_id = db.Column(db.Integer, db.ForeignKey('quest.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))

    name = db.Column(db.String(256))
    url = db.Column(db.String(1024))

    # back refs
    votes = db.relationship('Vote', backref='vote', lazy='dynamic')


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True)


class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    quest_id = db.Column(db.Integer, db.ForeignKey('quest.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    work_id = db.Column(db.Integer, db.ForeignKey('work.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))

    status = db.Column(db.Integer)
    err_line = db.Column(db.String(128), default=None)
    time = db.Column(db.DateTime)

    @staticmethod
    def status_valid():
        return 0

    @staticmethod
    def status_invalid_num_teams():
        return 1

    @staticmethod
    def status_invalid_line():
        return 2

    @staticmethod
    def status_team_not_found():
        return 3

    @staticmethod
    def status_work_not_found():
        return 4

