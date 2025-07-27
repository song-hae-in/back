from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User

bp = Blueprint('info', __name__)

# Test API
@bp.route('/info', methods=['GET'])
def get_info():
    return jsonify({'result': 'ok', 'data': {'service': 'LLM Interview API', 'status': 'running'}})

# User Information API
@bp.route('/api/user/info', methods=['GET'])
@jwt_required()
def get_user_info():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'result': 'fail', 'code': '404', 'message': 'User not found'}), 404

    return jsonify({
        'result': 'ok',
        'data': {
            'username': user.username,
            'email': user.email
        }
    })
