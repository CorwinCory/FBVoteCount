import os
basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

# Prog settings
DIARY_LOGIN = "Minion of Doc"
DIARY_PASSWORD = "111111"
DIARY_POSTS_PER_PAGE = 20
DIARY_PAGE_ENCODING = "cp1251"
FB_YEAR = "2016"

MIN_VOTES = 3
MAX_VOTES = 10
