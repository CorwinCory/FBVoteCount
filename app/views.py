from flask import render_template
from app import app, db, models
from sqlalchemy import func

@app.route('/')
def index():
    return render_template('base.html')


@app.route('/totalrating')
def total_rating():
    rating = db.session.query(models.Team.name, func.count(models.Vote.id)).\
        filter(models.Vote.work_id == models.Work.id). \
        filter(models.Work.team_id == models.Team.id).group_by(models.Team.name).all()
    rating.sort(key=lambda x: -x[1])
    print(rating)
    return render_template('total_rating.html', rating=rating)