from flask import Blueprint, request, jsonify, redirect
from flask_jwt_extended import create_access_token
from app import db
from app.models import User
import requests
from flask import current_app

bp = Blueprint('auth', __name__)

@bp.route('/api/auth/join', methods=['POST'])
def join():
    data = request.get_json()
    if not data or 'username' not in data or 'email' not in data or 'password' not in data:
        return jsonify({'result': 'fail', 'code': '400', 'message': 'Invalid input'}), 400

    user = User.query.filter_by(email=data['email']).first()
    if user:
        return jsonify({'result': 'fail', 'code': '409', 'message': 'User already exists'}), 409

    user = User(username=data['username'], email=data['email'], password=data['password'])
    db.session.add(user)
    db.session.commit()

    # token = create_access_token(identity=user.id)
    token = create_access_token(identity=str(user.id))
    print("[User Joined]", user.username, user.email, token)
    return jsonify({'result': 'ok', 'data': {'token': token, 'username': user.username, 'email': user.email}})


@bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'result': 'fail', 'code': '400', 'message': 'Invalid input'})

    user = User.query.filter_by(email=data['email'], password=data['password']).first()
    if not user:
        return jsonify({'result': 'fail', 'code': '401', 'message': 'Invalid credentials'}), 401

    # token = create_access_token(identity=user.id)
    token = create_access_token(identity=str(user.id))
    return jsonify({'result': 'ok', 'data': {'token': token, 'username': user.username, 'email': user.email}})

@bp.route('/api/auth/verify', methods=['POST'])
def verify():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'result': 'fail', 'code': '400', 'message': 'Email is required'}), 400

    exists = User.query.filter_by(email=email).first() is not None
    return jsonify({'result': 'ok', 'data': {'exists': exists}})

@bp.route('/kakao/login', methods=['GET', 'POST'])
def kakao_login():
    kakao_oauth_url = (
        f"https://kauth.kakao.com/oauth/authorize?response_type=code"
        f"&client_id={current_app.config['KAKAO_CLIENT_ID']}"
        f"&redirect_uri={current_app.config['KAKAO_REDIRECT_URI']}"
    )
    return redirect(kakao_oauth_url)

@bp.route('/kakao/callback')    
def kakao_callback():
    try:
        code = request.args.get('code')
        if not code:
            return jsonify({'result': 'fail', 'message': 'Missing code'}), 400
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': current_app.config['KAKAO_CLIENT_ID'],
            'client_secret': current_app.config['KAKAO_CLIENT_SECRET'],
            'redirect_uri': current_app.config['KAKAO_REDIRECT_URI'],
            'code': code
        }

        token_res = requests.post('https://kauth.kakao.com/oauth/token', data=token_data)
        token_json = token_res.json()
        # print("[🔑 token response]", token_json)

        if 'access_token' not in token_json:
            return jsonify({'result': 'fail', 'message': 'Kakao token 발급 실패', 'detail': token_json}), 400

        access_token = token_json['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        user_info_res = requests.get('https://kapi.kakao.com/v2/user/me', headers=headers)
        user_info = user_info_res.json()
        # print("[🔍 user_info response]", user_info)

        if 'id' not in user_info:
            return jsonify({'result': 'fail', 'message': 'Kakao 사용자 정보 조회 실패', 'detail': user_info}), 400

        kakao_id = user_info['id']
        kakao_account = user_info.get('kakao_account', {})
        email = kakao_account.get('email', f"{kakao_id}@kakao.com")
        nickname = kakao_account.get('profile', {}).get('nickname', f"user_{kakao_id}")
        print("[Kakao 사용자 정보]", user_info)
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(username=nickname, email=email, password='kakao')
            db.session.add(user)
            db.session.commit()
            
        # token = create_access_token(identity=user.id)
        token = create_access_token(identity=str(user.id))
        print("[Kakao 로그인 성공]", user.username, user.email)
        
        # 메인 페이지로 바로 리다이렉트하면서 토큰과 사용자 정보 전달
        frontend_url = f"http://localhost:3000/?kakao_login=success&token={token}&username={user.username}&email={user.email}"
        return redirect(frontend_url)

    except Exception as e:
        print("Exception:", e)
        return jsonify({'result': 'fail', 'message': 'Internal Server Error', 'detail': str(e)}), 500

