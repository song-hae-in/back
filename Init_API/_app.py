from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import random
import datetime
from flask_cors import CORS, cross_origin

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, allow_headers="*", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///interview.db'
db = SQLAlchemy(app)

# DB 모델
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    email = db.Column(db.String(120), unique=True)

class InterviewResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    question = db.Column(db.Text)
    answer = db.Column(db.Text)
    score = db.Column(db.Float)
    date = db.Column(db.String(20))

# 테스트용 질문/답변 예시
TEST_QUESTIONS = [
    "기본간호학에서 가장 중요한 개념은 무엇인가요?",
    "환자와의 의사소통에서 주의할 점은?",
    "감염 예방을 위한 간호사의 역할은?"
]
TEST_ANSWERS = [
    "환자의 안전과 건강을 최우선으로 생각하는 것입니다.",
    "경청과 공감이 중요합니다.",
    "손씻기와 위생 관리가 필수적입니다."
]

@app.route('/generate-question', methods=['POST'])
@cross_origin()
def generate_question():
    print("generate_question called")  # 함수 진입 확인용
    question = random.choice(TEST_QUESTIONS)
    return jsonify({'question': question})

@app.route('/score-answer', methods=['POST'])
@cross_origin()
def score_answer():
    answer = request.json.get('answer', '')
    # 답변 길이와 키워드 포함 여부로 점수 산출(예시)
    score = 50 + len(answer) // 5
    if any(keyword in answer for keyword in ['안전', '경청', '공감', '위생  ₩', '손씻기']):
        score += 20
    score = min(score, 100)
    return jsonify({'score': score})

@app.route('/save-result', methods=['POST'])
@cross_origin()
def save_result():
    user_id = request.json.get('user_id')
    question = request.json.get('question')
    answer = request.json.get('answer')
    score = request.json.get('score')
    date = request.json.get('date', datetime.date.today().isoformat())
    result = InterviewResult(user_id=user_id, question=question, answer=answer, score=score, date=date)
    db.session.add(result)
    db.session.commit()
    return jsonify({'status': 'saved'})

@app.route('/user-results/<int:user_id>', methods=['GET'])
@cross_origin()
def user_results(user_id):
    results = InterviewResult.query.filter_by(user_id=user_id).all()
    return jsonify([{
        'question': r.question,
        'answer': r.answer,
        'score': r.score,
        'date': r.date
    } for r in results])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)