from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import random
import datetime
from flask_cors import CORS, cross_origin

app = Flask(__name__)
CORS(app)  # CORS 설정 추가

user_storage = {}

items = [{"ID": 1, "name": "Item 1"},
         {"ID": 2, "name": "Item 2"}]

@app.route("/generate_question", methods=["GET"])
def hello():
    return jsonify({"message": "Hello, World!"})

@app.route('/user', methods=['POST'])
def receive_user_info():
    data = request.get_json()

    if not data or 'username' not in data or 'email' not in data:
        return jsonify({'error': 'Invalid input'}), 400

    username = data['username']
    email = data['email']

    # 저장 (key는 username)
    user_storage[username] = {'email': email}

    return jsonify({'message': f'User {username} saved successfully.'}), 201

@app.route('/info', methods=['GET'])
def send_server_info():
    server_data = {
        'status': 'running',
        'message': 'This is server-generated data.',
        'user_count': len(user_storage)
    }
    return jsonify(server_data), 200
if __name__ == '__main__':
    app.run(debug=True)