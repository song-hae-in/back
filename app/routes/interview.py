from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Interview
import uuid
from datetime import datetime

# 테스트용 인터뷰 Q,A 생성 함수
# from app.services.test_question import generate_question

# 실제 인터뷰 Q,A 생성 서비스
from app.services.llm_service import generate_question

from app.services.llm_analysis import analysisByLLM

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
    
    # 새로운 인터뷰 세션 ID 생성
    session_id = str(uuid.uuid4())
    print(f"[New Session] Session ID: {session_id}")
    
    questionList = generate_question() # <- QustionList should contain keys like 'question', 'type'
    print(f"[Question Count] Generated {len(questionList)} questions")
    
    # questionList의 모든 질문들을 같은 session_id로 저장
    for i, q in enumerate(questionList):
        interview = Interview(
            user_id=user_id,
            question=q['question'],
            LLM_gen_answer=q['answer'],
            type=q['type'],
            session_id=session_id,  # 세션 ID 추가
            question_order=i  # 질문 순서 추가
        )
        db.session.add(interview)
    
    db.session.commit()
    
    if not questionList:
        return jsonify({'result': 'fail', 'code': '500', 'message': 'Failed to generate question'}), 500
    
    return jsonify({
        'result': 'ok', 
        'data': {
            'questionList': questionList,
            'session_id': session_id  # 프론트엔드에 세션 ID 전달
        }
    })

@bp.route('/api/interview/answer', methods=['POST'])
@jwt_required()
def next_question():
    data = request.get_json()
    if not data or 'question' not in data or 'useranswer' not in data or 'video' not in data or 'type' not in data:
        print("[Error] Invalid input data:", data)
        return jsonify({'result': 'fail', 'code': '400', 'message': 'Invalid input'}), 400
    user_id = get_jwt_identity()
    
    # session_id가 있으면 사용, 없으면 question으로 찾기 (기존 호환성)
    if 'session_id' in data:
        interview = Interview.query.filter_by(
            user_id=user_id, 
            question=data['question'],
            session_id=data['session_id']
        ).first()
    else:
        interview = Interview.query.filter_by(user_id=user_id, question=data['question']).first()
    
    if not interview:
        return jsonify({'result': 'fail', 'code': '404', 'message': 'Interview not found'}), 404
    
    interview.useranswer = data['useranswer']
    interview.video = data['video']
    interview.type = data['type']
    
    # analysis = analysisByLLM(interview.useranswer)
    # interview.LLM_gen_answer = analysis["LLM_gen_answer"]
    # interview.analysis = analysis["analysis"]
    
    db.session.commit()
    return jsonify({'result': 'ok', 'data': {'message': 'ok'}})

@bp.route('/api/analysis/info', methods=['GET'])
@jwt_required()
def get_analysis():
    user_id = get_jwt_identity()
    
    # URL 파라미터에서 session_id 가져오기
    session_id = request.args.get('session_id')
    
    if session_id:
        # 특정 세션의 인터뷰만 조회
        interviews = Interview.query.filter_by(user_id=user_id, session_id=session_id).order_by(Interview.question_order).all()
        print(f"[Analysis] Analyzing specific session: {session_id}")
    else:
        # session_id가 없으면 가장 최근 세션 분석
        latest_session = db.session.query(Interview.session_id).filter_by(user_id=user_id).order_by(Interview.id.desc()).first()
        if latest_session:
            session_id = latest_session.session_id
            interviews = Interview.query.filter_by(user_id=user_id, session_id=session_id).order_by(Interview.question_order).all()
            print(f"[Analysis] Analyzing latest session: {session_id}")
        else:
            interviews = []
    
    if not interviews:
        return jsonify({'result': 'fail', 'code': '404', 'message': 'No interviews found for this session'}), 404
    
    # 해당 세션의 인터뷰 분석
    summary = analysisByLLM(user_id, session_id)
    
    interview_list = []
    for itv in interviews:
        interview_list.append({
            'question':        itv.question,
            'useranswer':      itv.useranswer,
            'LLM_gen_answer':  itv.LLM_gen_answer,
            'analysis':        itv.analysis,
            'score':           itv.score,
            'question_order':  itv.question_order
        })
    
    data = {
        "InterviewList": interview_list,
        "summary": summary,
        "session_id": session_id,
        "video": interviews[0].video if interviews and interviews[0].video else None
    }   
    
    print(f"[Analysis Info] Session {session_id}:", data)
    return jsonify({'result': 'ok', 'data': data})

@bp.route('/api/interview/info', methods=['GET'])
@jwt_required()
def get_history():
    user_id = get_jwt_identity()
    
    # URL 파라미터에서 session_id 가져오기
    session_id = request.args.get('session_id')
    
    if session_id:
        # 특정 세션의 인터뷰만 조회
        interviews = Interview.query.filter_by(user_id=user_id, session_id=session_id).order_by(Interview.question_order).all()
    else:
        # 모든 인터뷰 조회 (기존 동작 유지)
        interviews = Interview.query.filter_by(user_id=user_id).all()
    
    if not interviews:
        return jsonify({'result': 'fail', 'code': '404', 'message': 'No interviews found'}), 404
    
    interview_list = []
    for itv in interviews:
        interview_list.append({
            'question':        itv.question,
            'useranswer':      itv.useranswer,
            'LLM_gen_answer':  itv.LLM_gen_answer,
            'analysis':        itv.analysis,
            'score':           itv.score,
            'session_id':      itv.session_id,
            'question_order':  getattr(itv, 'question_order', 0)
        })
    
    summary = "면접결과 summary"
    data = {
        "InterviewList": interview_list,
        "summary": summary,
        "session_id": session_id,
        "video": interviews[0].video if interviews and interviews[0].video else "interview_20250728_user1234.mp4"
    }   
    
    print("[Interview Info]", data)
    return jsonify({'result': 'ok', 'data': data})

# 사용자의 모든 인터뷰 세션 목록 조회
@bp.route('/api/interview/sessions', methods=['GET'])
@jwt_required()
def get_sessions():
    user_id = get_jwt_identity()
    
    # 세션별로 그룹화하여 조회
    sessions = db.session.query(
        Interview.session_id,
        db.func.min(Interview.id).label('first_interview_id'),
        db.func.count(Interview.id).label('question_count'),
        db.func.max(Interview.id).label('last_interview_id')
    ).filter_by(user_id=user_id).group_by(Interview.session_id).all()
    
    session_list = []
    for session in sessions:
        # 해당 세션의 모든 인터뷰 데이터 가져오기
        interviews = Interview.query.filter_by(
            user_id=user_id, 
            session_id=session.session_id
        ).order_by(Interview.question_order).all()
        
        # 각 세션의 인터뷰 리스트 구성
        interview_list = []
        for itv in interviews:
            interview_list.append({
                'question': itv.question,
                'useranswer': itv.useranswer,
                'LLM_gen_answer': itv.LLM_gen_answer,
                'analysis': itv.analysis,
                'score': itv.score,
                'question_order': itv.question_order
            })
        
        # 첫 번째 인터뷰 정보 가져오기
        first_interview = Interview.query.get(session.first_interview_id)
        
        session_list.append({
            'session_id': session.session_id,
            'question_count': session.question_count,
            'created_at': first_interview.timestamp if first_interview else None,
            'type': first_interview.type if first_interview else 'Unknown',
            'interviews': interview_list  # 모든 질문, 답변, 분석 정보 포함
        })
    
    return jsonify({'result': 'ok', 'data': {'sessions': session_list}})




#-------------------------------------------------#
sampleData = {
"InterviewList": [
    {
    "question": "API Test.",
    "useranswer": "안녕하세요, 저는 책임감 있고 소통을 중요하게 생각하는 지원자 홍길동입니다. 대학 시절 여러 프로젝트에 참여하며 개발뿐 아니라 기획과 협업 경험을 쌓았고, 현재는 풀스택 개발자로 성장 중입니다.",
    "LLM gen answer": "지원자는 자신을 명확하게 표현하고 핵심 역량을 잘 언급했습니다. 다만 '프로젝트'에 대한 구체적인 사례가 없고, 강점을 뒷받침하는 경험이 부족해 설득력이 떨어집니다.",
    "analysis": "분석내용: 어조는 침착하고 시선도 안정적이었음. 표정에서 긴장감은 있었으나 과도하지 않았음. \n미흡한점: 구체적인 프로젝트 사례가 없어 실제 경험 기반의 자기소개로 보기엔 아쉬움.\n개선점: 예시를 하나 넣어 신뢰도를 높이면 좋음.\n수정된 답변: 안녕하세요, 저는 책임감을 기반으로 협업을 중시하는 홍길동입니다. 대학 시절 팀 프로젝트에서 팀장을 맡아 React와 Firebase로 웹앱을 개발했으며, 일정과 소통을 총괄하며 프로젝트를 성공적으로 완수했습니다. 이런 경험을 통해 실무 중심의 커뮤니케이션 능력을 키웠습니다.",
    "score": 85
    },
    {
    "question": "최근 사용한 기술 스택은?",
    "useranswer": "최근에는 React와 Flask를 이용해서 예약 시스템을 개발했습니다. 프론트엔드는 React로 구성했고, Flask로 API 서버를 구축했습니다. MongoDB를 데이터베이스로 사용했습니다.",
    "LLM gen answer": "기술 스택에 대한 설명은 명확하나, 기술을 선택한 이유나 해결한 문제에 대한 언급이 없어 실무 역량이 충분히 드러나지 않습니다.",
    "analysis": "분석내용: 말은 또렷하고 전달력은 좋았음. 다만 내용은 나열식으로 기술되어 면접관의 관심을 끌기엔 부족했음.\n미흡한점: 단순한 기술 나열. 해당 기술이 사용된 배경과 결과가 빠짐.\n개선점: 기술 선택 이유와 구현 성과 또는 문제 해결 경험을 추가.\n수정된 답변: 최근에는 React와 Flask를 사용해 병원 예약 시스템을 개발했습니다. 프론트엔드는 사용자 친화적인 UI를 구현하기 위해 React를, 백엔드는 빠른 REST API 개발을 위해 Flask를 사용했습니다. 인증은 JWT를, DB는 MongoDB로 구성해 빠른 검색이 가능하도록 최적화했습니다.",
    "score": 78
    },
    {
    "question": "협업 중 갈등 해결 사례는?",
    "useranswer": "프로젝트 중 디자이너와 기능 우선순위를 두고 의견 충돌이 있었는데, 각자의 입장을 정리해 회의에서 공유하고 사용자 피드백을 기반으로 의사결정을 내렸습니다.",
    "LLM gen answer": "협업 상황을 명확히 설명하고 해결 과정도 논리적이지만, 감정적 갈등의 디테일이나 리더십 요소는 부족해 인상 깊지 않음.",
    "analysis": "분석내용: 침착한 어조와 중립적인 시선 처리로 긍정적인 인상. 논리 전개는 좋았으나 구체적 상황 묘사가 부족했음.\n미흡한점: ‘의견 충돌’의 강도나 해결의 주도성 부족. 본인의 역할이 불명확함.\n개선점: 자신이 어떻게 조율했는지를 강조하면 리더십 어필 가능.\n수정된 답변: 프로젝트 중 디자이너는 사용성, 저는 개발 난이도를 우선시해 우선순위 충돌이 있었습니다. 저는 두 입장을 문서화해 정리한 뒤 사용자 대상 테스트를 통해 우선순위를 조정했고, 결과적으로 일정과 품질을 모두 지킬 수 있었습니다.",
    "score": 82
    }
],
"summary": "지원자는 전반적으로 명확한 어조와 침착한 태도를 유지하며 좋은 인상을 주었습니다. 특히 협업에 있어 논리적인 문제 해결 접근을 보였고, 기술 스택에 대한 이해도도 기본 이상이었습니다. 다만 전반적으로 '구체성'이 부족해 실무 능력을 강조하기에는 설득력이 다소 약했습니다. 이후에는 경험 중심의 답변 구성과 수치·성과 중심의 표현 연습이 필요합니다.",
"video": "interview_20250728_user1234.mp4"
}
    
# Interview Question API (deprecated - 기존 호환성용)
@bp.route('/api/answer', methods=['POST'])
@jwt_required()
def save_answer():
    user_id = get_jwt_identity()
    data = request.get_json()
    interview = Interview(
        user_id=user_id,
        question=data['question'],
        useranswer=data['answer']  # answer -> useranswer로 수정
    )
    interview.score = 0  # 기본값 설정 (score_answer 함수 대신)
    db.session.add(interview)
    db.session.commit()
    return jsonify({'result': 'ok', 'data': {'score': interview.score}})

@bp.route('/api/score', methods=['GET'])
@jwt_required()
def get_scores():
    user_id = get_jwt_identity()
    interviews = Interview.query.filter_by(user_id=user_id).all()
    data = [{'question': i.question, 'useranswer': i.useranswer, 'score': i.score} for i in interviews]
    return jsonify({'result': 'ok', 'data': {'interviews': data}})

# @bp.route('/api/analysis/info', methods=['GET'])
# @jwt_required()
# def get_analysis():
#     user_id = get_jwt_identity()
#     interviews = Interview.query.filter_by(user_id=user_id).all()
#     # data = InterviewList(question, useranswer, LLM_gen_answer, video, type, analysis)
#     data = [{'question': i.question, 'useranswer': i.useranswer, 'LLM_gen_answer': i.LLM_gen_answer,
#                 'video': i.video, 'type': i.type, 'analysis': i.analysis} for i in interviews]
#     if not data:
#         return jsonify({'result': 'fail', 'code': '404', 'message': 'No interviews found'}), 404
    
#     print("[Analysis Info]", data)

#     return jsonify({'result': 'ok', 'data': {'interviews': data}})