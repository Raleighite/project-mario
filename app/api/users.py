from flask import jsonify
from flask_login import login_required, current_user
from app.api import api_bp
from app.models import User
from app.extensions import db


@api_bp.route('/users/me', methods=['GET'])
@login_required
def get_current_user():
    return jsonify(current_user.to_dict()), 200


@api_bp.route('/users/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user.to_dict()), 200
