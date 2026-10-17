from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User
from schemas import user_schema

users_bp = Blueprint('users', __name__, url_prefix='/api/users')

@users_bp.route('/me', methods=['GET'])
@jwt_required()
def get_my_dashboard():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    
    # Dump the user data. Since we defined relationships in models.py, 
    # Marshmallow can easily be configured to include them, but for safety, 
    # we will explicitly query their statuses.
    
    dashboard_data = {
        "profile": user_schema.dump(user),
        "my_assignments": [
            {
                "assignment_name": sub.assignment.Assignment_Name,
                "status": sub.Review_Status,
                "grade": sub.Grade,
                "feedback": sub.Admin_Feedback,
                "submitted_at": sub.Created_At.isoformat() if sub.Created_At else None
            } for sub in user.submissions
        ],
        "my_payments": [
            {
                "payment_name": pay.payment.Payment_Name,
                "status": pay.Verification_Status,
                "feedback": pay.Admin_Feedback
            } for pay in user.payments
        ],
        "my_recruitments": [
            {
                "recruitment_name": rec.recruitment.Recr_Name,
                "status": rec.Acceptance_Status,
                "feedback": rec.Admin_Feedback
            } for rec in user.applications
        ]
    }
    
    return jsonify(dashboard_data), 200