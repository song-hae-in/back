from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Interview
from app.services.llm_service import generate_question
from app.services.llm_analysis import score_answer, analysisByLLM

bp = Blueprint('interview', __name__)

# Interview Question Test API
@bp.route('/api/interview', methods=['GET'])
@jwt_required()
def get_interview_question():
    question = generate_question()
    return jsonify({'result': 'ok', 'data': {'question': question}})

# Interview Question API
@bp.route('/api/interview/start', methods=['GET'])
@jwt_required()
def start_interview():
    '''
    generate a new interview question using the LLM service
    using Qwen or other LLMs to generate a question
    '''
    print("[Interview Start] Generating question...")
    user_id = get_jwt_identity()
    print("user_id : ", user_id)
    questionList = generate_question() # <- QustionList should contain keys like 'question', 'type'
    interview = Interview(
        user_id=user_id,
        question=questionList
    )
    db.session.add(interview)
    db.session.commit()
    question = interview.question
    if not question:
        return jsonify({'result': 'fail', 'code': '500', 'message': 'Failed to generate question'}), 500
    # print("[Generated Question]", question)
    return jsonify({'result': 'ok', 'data': {'questionList': questionList}})

# Next Question & request Analysis API
@bp.route('/api/interview/question', methods=['POST'])
@jwt_required()
def next_question():
    # request = {"question": "string","answer": "string","video": "video","type": "string",}
    # response = {"result" : "ok","data" : {"message": "ok"}
    data = request.get_json()
    if not data or 'question' not in data or 'useranswer' not in data or 'video' not in data or 'type' not in data:
        return jsonify({'result': 'fail', 'code': '400', 'message': 'Invalid input'}), 400
    user_id = get_jwt_identity()
    
    interview = Interview.query.filter_by(user_id=user_id, question=data['question']).first()
    
    if not interview:
        return jsonify({'result': 'fail', 'code': '404', 'message': 'Interview not found'}), 404
    interview.useranswer = data['useranswer']
    interview.video = data['video']
    interview.type = data['type']
    
    analysis = analysisByLLM(interview.useranswer)
    interview.LLM_gen_answer = analysis["LLM_gen_answer"]
    interview.analysis = analysis["analysis"]
    
    db.session.commit()
    return jsonify({'result': 'ok', 'data': {'message': 'ok'}})

@bp.route('/api/analysis/info', methods=['GET'])
@jwt_required()
def get_analysis():
    user_id = get_jwt_identity()
    interviews = Interview.query.filter_by(user_id=user_id).all()
    # data = InterviewList(question, useranswer, LLM_gen_answer, video, type, analysis)
    data = [{'question': i.question, 'useranswer': i.useranswer, 'LLM_gen_answer': i.LLM_gen_answer,
                'video': i.video, 'type': i.type, 'analysis': i.analysis} for i in interviews]
    if not data:
        return jsonify({'result': 'fail', 'code': '404', 'message': 'No interviews found'}), 404
    
    print("[Analysis Info]", data)

    return jsonify({'result': 'ok', 'data': {'interviews': data}})


#-------------------------------------------------#

# Interview Question API
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
