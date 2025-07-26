from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import random
import datetime
from flask_cors import CORS, cross_origin
'''
API 명세서
# 공통 응답 객체
- 성공
{
  "result": "ok",
  "data" : {
     "(key)": {
		   "(value)"
	   }			
  }
}
- 실패
{
  "result": "fail",
  "code": "(에러 코드)",
  "message": "(에러 메세지)"
}

# 회원가입
- POST /login: 사용자 정보 저장

# 사용자
- GET /info: 서버 정보 조회


# 면접
- GET /generated_question: 면접 질문 제공
- POST /answer: 면접 답변 저장 및 채점
- GET /score: 면접 답변 채점결과 제공
'''

dummy_data = {
        "username": "test_user",
        "email" : "test@gmail.com",
        "password": "1234"
    }
 
app = Flask(__name__)

# username, email, password
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or 'username' not in data or 'email' not in data or 'password' not in data:
        return jsonify({'result': 'fail',
                        'code': '400',
                        'message': 'Invalid input'})
    username = data['username']
    email = data['email']
    password = data['password']
    return jsonify({'result': "ok", 
                    "data" : {
                        "username" : username,
                        "email" : email,
                        "password" : password
                        }})

# User Info 조회
@app.route("/get_info", methods=["GET"])
def get_info():
    return jsonify({'result': "ok", 
                    "data" : {
                        "username" : dummy_data['username'],
                        "email" : dummy_data['email'],
                        "password" : dummy_data['password']
                        }})

### 면접 관련 API
# Interview 시작
@app.route("/api/interview", methods=["GET"])
def get_interview_questions():
    questions = [
        {"question": "기본간호학에서 가장 중요한 개념은 무엇인가요?",
         "type": "전공"},
        {"question": "환자와의 의사소통에서 주의할 점은?",
         "type": "전공"},
        {"question": "감염 예방을 위한 간호사의 역할은?",
         "type": "전공"},
        {"question": "환자의 안전을 보장하기 위한 기본 간호 기술은 무엇인가요?",
          "type": "전공"},
    ]
    return jsonify({'result': "ok", 
                    "data" : {
                        "questionList" : questions
                        }})

if __name__ == '__main__':
    app.run(debug=True)