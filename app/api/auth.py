from flask import request, jsonify
from flask_login import login_user, logout_user, login_required
from app.api import api_bp
from app.extensions import db
from app.models import User


@api_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request must be JSON'}), 400

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not all([username, email, password]):
        return jsonify({'error': 'Missing required fields: username, email, password'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already taken'}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 409

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify(user.to_dict()), 201


@api_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request must be JSON'}), 400

    username = data.get('username')
    password = data.get('password')

    if not all([username, password]):
        return jsonify({'error': 'Missing required fields: username, password'}), 400

    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        return jsonify({'error': 'Invalid username or password'}), 401

    login_user(user)
    return jsonify(user.to_dict()), 200


@api_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out'}), 200
