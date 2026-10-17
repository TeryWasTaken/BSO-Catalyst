from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from dateutil import parser
from extensions import db
from models import User, Assignment, Event, Recruitment, Payment, AssignmentSubmission, PaymentRecord

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

def is_admin(user_id):
    user = User.query.get(user_id)
    return user and user.User_Authority == 'admin'

# ---------------------------------------------------------
# CREATION ROUTES
# ---------------------------------------------------------
@admin_bp.route('/assignments', methods=['POST'])
@jwt_required()
def create_assignment():
    if not is_admin(get_jwt_identity()): return jsonify({"error": "Unauthorized"}), 403
    data = request.get_json()
    new_task = Assignment(
        Assignment_Name=data['name'], Target_StudentYear=data.get('target_year'),
        Assignment_TimeDateStart=parser.parse(data['start_date']),
        Assignment_TimeDateEnd=parser.parse(data['end_date']), Assignment_Desc=data.get('description')
    )
    db.session.add(new_task)
    db.session.commit()
    return jsonify({"message": "Assignment created", "id": new_task.Assignment_ID}), 201

@admin_bp.route('/payments', methods=['POST'])
@jwt_required()
def create_payment():
    if not is_admin(get_jwt_identity()): return jsonify({"error": "Unauthorized"}), 403
    data = request.get_json()
    new_task = Payment(
        Payment_Name=data['name'], Target_StudentYear=data.get('target_year'),
        Payment_TimeDateStart=parser.parse(data['start_date']),
        Payment_TimeDateEnd=parser.parse(data['end_date']), Payment_Desc=data.get('description'),
        Budget_Spreadsheet_ID=data.get('spreadsheet_id')
    )
    db.session.add(new_task)
    db.session.commit()
    return jsonify({"message": "Payment created", "id": new_task.Payment_ID}), 201

def _parse_window(data):
    """Validate name/start_date/end_date. Returns (name, start, end, error_response)."""
    name = (data.get('name') or '').strip()
    if not name or not data.get('start_date') or not data.get('end_date'):
        return None, None, None, (jsonify({"error": "name, start_date and end_date are required"}), 400)
    try:
        start = parser.parse(data['start_date'])
        end = parser.parse(data['end_date'])
    except (ValueError, OverflowError):
        return None, None, None, (jsonify({"error": "Invalid date format"}), 400)
    if end < start:
        return None, None, None, (jsonify({"error": "end_date must not be before start_date"}), 400)
    return name, start, end, None

@admin_bp.route('/events', methods=['POST'])
@jwt_required()
def create_event():
    if not is_admin(get_jwt_identity()): return jsonify({"error": "Unauthorized"}), 403
    data = request.get_json(silent=True) or {}
    name, start, end, err = _parse_window(data)
    if err: return err
    new_event = Event(
        Event_Name=name, Event_TimeDateStart=start,
        Event_TimeDateEnd=end, Event_Desc=data.get('description')
    )
    db.session.add(new_event)
    db.session.commit()
    return jsonify({"message": "Event created", "id": new_event.Event_ID}), 201

@admin_bp.route('/recruitments', methods=['POST'])
@jwt_required()
def create_recruitment():
    if not is_admin(get_jwt_identity()): return jsonify({"error": "Unauthorized"}), 403
    data = request.get_json(silent=True) or {}
    name, start, end, err = _parse_window(data)
    if err: return err
    new_recr = Recruitment(
        Recr_Name=name, Recr_TimeDateStart=start,
        Recr_TimeDateEnd=end, Recr_Desc=data.get('description')
    )
    db.session.add(new_recr)
    db.session.commit()
    return jsonify({"message": "Recruitment created", "id": new_recr.Recr_ID}), 201

# ---------------------------------------------------------
# GRADING & VERIFICATION ROUTES
# ---------------------------------------------------------
@admin_bp.route('/submissions/assignments/<int:submission_id>/grade', methods=['PATCH'])
@jwt_required()
def grade_assignment(submission_id):
    if not is_admin(get_jwt_identity()): return jsonify({"error": "Unauthorized"}), 403
    
    data = request.get_json()
    submission = AssignmentSubmission.query.get_or_404(submission_id)
    
    submission.Grade = data.get('grade')
    submission.Review_Status = data.get('status', 'Graded')
    submission.Admin_Feedback = data.get('feedback', '')
    
    db.session.commit()
    return jsonify({"message": "Assignment graded successfully"}), 200

@admin_bp.route('/submissions/payments/<int:record_id>/verify', methods=['PATCH'])
@jwt_required()
def verify_payment(record_id):
    if not is_admin(get_jwt_identity()): return jsonify({"error": "Unauthorized"}), 403
    
    data = request.get_json()
    record = PaymentRecord.query.get_or_404(record_id)
    
    # Expected status: 'Verified' or 'Rejected'
    record.Verification_Status = data.get('status')
    record.Admin_Feedback = data.get('feedback', '')
    
    db.session.commit()
    return jsonify({"message": "Payment record updated"}), 200