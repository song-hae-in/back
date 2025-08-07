from app import db
import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Interview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    question = db.Column(db.Text, nullable=False)
    useranswer = db.Column(db.Text, nullable=False, default="응답 없음")
    LLM_gen_answer = db.Column(db.Text, nullable=False, default="응답 없음")
    video = db.Column(db.Text)
    type = db.Column(db.String(80), nullable=False, default="응답 없음")
    analysis = db.Column(db.Text, nullable=False, default="응답 없음")

    score = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
