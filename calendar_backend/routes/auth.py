from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from models import User

from extensions import db

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user_id = data.get('user_id', 'H1D026052')
    device_token = data.get('device_token')

    user = User.query.get(user_id)
    if not user:
        # Fallback dummy user creation for immediate local testing
        default_name = "Mahatma Grand Austin Kasandi" if user_id == "H1D026052" else "Test User"
        
        authority = "admin" if user_id == "H1D026052" else "student"
        
        user = User(
            User_ID=user_id, 
            User_Name=default_name, 
            User_Email=f"{user_id}@mhs.unsoed.ac.id", 
            User_Authority=authority
        )
        
        db.session.add(user)
    
    if device_token:
        user.Device_Token = device_token
        
    db.session.commit()

    access_token = create_access_token(identity=user_id)
    return jsonify({"access_token": access_token, "user_id": user.User_ID}), 200