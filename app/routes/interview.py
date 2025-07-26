from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Interview
from app.services.llm_service import generate_question
from app.services.score_service import score_answer

bp = Blueprint('interview', __name__)

@bp.route('/api/interview', methods=['GET'])
@jwt_required()
def get_interview_question():
    question = generate_question()
    return jsonify({'result': 'ok', 'data': {'question': question}})

@bp.route('/api/answer', methods=['POST'])
@jwt_required()
def save_answer():
    user_id = get_jwt_identity()
    data = request.get_json()
    interview = Interview(
        user_id=user_id,
        question=data['question'],
        answer=data['answer']
    )
    interview.score = score_answer(interview.answer)
    db.session.add(interview)
    db.session.commit()
    return jsonify({'result': 'ok', 'data': {'score': interview.score}})

@bp.route('/api/score', methods=['GET'])
@jwt_required()
def get_scores():
    user_id = get_jwt_identity()
    interviews = Interview.query.filter_by(user_id=user_id).all()
    data = [{'question': i.question, 'answer': i.answer, 'score': i.score} for i in interviews]
    return jsonify({'result': 'ok', 'data': {'interviews': data}})
