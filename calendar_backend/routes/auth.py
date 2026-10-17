from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from models import User

from extensions import db

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

MIN_PASSWORD_LENGTH = 6


def _clean_id(value):
    return (value or '').strip().upper()


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    user_id = _clean_id(data.get('user_id'))
    name = (data.get('name') or '').strip()
    password = data.get('password') or ''
    device_token = data.get('device_token')

    if not user_id or len(user_id) > 20:
        return jsonify({"error": "User ID is required (max 20 characters)"}), 400
    if not name:
        return jsonify({"error": "Name is required"}), 400
    if len(password) < MIN_PASSWORD_LENGTH:
        return jsonify({"error": f"Password must be at least {MIN_PASSWORD_LENGTH} characters"}), 400
    if User.query.get(user_id):
        return jsonify({"error": "This User ID is already registered"}), 409

    # Self-registration always creates a student; admins are created via seed.py
    user = User(
        User_ID=user_id,
        User_Name=name,
        User_Email=f"{user_id}@mhs.unsoed.ac.id".lower(),
        User_Authority="student",
        Password_Hash=generate_password_hash(password),
        Device_Token=device_token,
    )
    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=user.User_ID)
    return jsonify({"access_token": access_token, "user_id": user.User_ID}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    user_id = _clean_id(data.get('user_id'))
    password = data.get('password') or ''
    device_token = data.get('device_token')

    user = User.query.get(user_id) if user_id else None
    if not user or not user.Password_Hash or not check_password_hash(user.Password_Hash, password):
        return jsonify({"error": "Invalid User ID or password"}), 401

    if device_token:
        user.Device_Token = device_token
        db.session.commit()

    access_token = create_access_token(identity=user.User_ID)
    return jsonify({"access_token": access_token, "user_id": user.User_ID}), 200
