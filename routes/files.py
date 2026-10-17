import os
import time
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from models import AssignmentSubmission, RecruitmentApplication, PaymentRecord
from extensions import db
from utils.file_validators import allowed_file

files_bp = Blueprint('files', __name__, url_prefix='/api/files')

# ---------------------------------------------------------
# FILE DOWNLOAD ROUTE
# ---------------------------------------------------------
@files_bp.route('/download/<category>/<filename>', methods=['GET'])
@jwt_required()
def download_file(category, filename):
    allowed_categories = {'assignments', 'payments', 'registrations'}
    if category not in allowed_categories:
        return jsonify({"error": "Invalid folder category"}), 400
    
    directory = os.path.join(current_app.config['UPLOAD_FOLDER'], category)
    return send_from_directory(directory, filename)

# ---------------------------------------------------------
# UPLOAD ROUTES
# ---------------------------------------------------------
def save_and_get_unique_path(file, category, user_id):
    original_name = secure_filename(file.filename)
    unique_name = f"{user_id}_{int(time.time())}_{original_name}"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], category, unique_name)
    file.save(filepath)
    return original_name, unique_name

@files_bp.route('/assignments/<int:assignment_id>/submit', methods=['POST'])
@jwt_required()
def submit_assignment(assignment_id):
    user_id = get_jwt_identity()
    if 'file' not in request.files or request.files['file'].filename == '' or not allowed_file(request.files['file'].filename):
        return jsonify({"error": "Invalid or missing file"}), 400
        
    original_name, unique_name = save_and_get_unique_path(request.files['file'], 'assignments', user_id)
    
    submission = AssignmentSubmission.query.filter_by(User_ID=user_id, Assignment_ID=assignment_id).first()
    if submission:
        submission.Submission_File_Path = unique_name
        submission.Original_File_Name = original_name
        submission.Review_Status = 'Resubmitted'
    else:
        submission = AssignmentSubmission(User_ID=user_id, Assignment_ID=assignment_id, Submission_File_Path=unique_name, Original_File_Name=original_name)
        db.session.add(submission)
        
    db.session.commit()
    return jsonify({"message": "Assignment uploaded successfully"}), 201

@files_bp.route('/recruitments/<int:recr_id>/submit', methods=['POST'])
@jwt_required()
def submit_recruitment(recr_id):
    user_id = get_jwt_identity()
    if 'file' not in request.files or request.files['file'].filename == '' or not allowed_file(request.files['file'].filename):
        return jsonify({"error": "Invalid or missing file"}), 400
        
    original_name, unique_name = save_and_get_unique_path(request.files['file'], 'registrations', user_id)
    
    application = RecruitmentApplication.query.filter_by(User_ID=user_id, Recr_ID=recr_id).first()
    if application:
        application.Registration_File_Path = unique_name
        application.Original_File_Name = original_name
    else:
        application = RecruitmentApplication(User_ID=user_id, Recr_ID=recr_id, Registration_File_Path=unique_name, Original_File_Name=original_name)
        db.session.add(application)
        
    db.session.commit()
    return jsonify({"message": "Recruitment application submitted successfully"}), 201

@files_bp.route('/payments/<int:payment_id>/submit', methods=['POST'])
@jwt_required()
def submit_payment(payment_id):
    user_id = get_jwt_identity()
    if 'file' not in request.files or request.files['file'].filename == '' or not allowed_file(request.files['file'].filename):
        return jsonify({"error": "Invalid or missing file"}), 400
        
    original_name, unique_name = save_and_get_unique_path(request.files['file'], 'payments', user_id)
    
    record = PaymentRecord.query.filter_by(User_ID=user_id, Payment_ID=payment_id).first()
    if record:
        record.Payment_File_Path = unique_name
        record.Original_File_Name = original_name
        record.Verification_Status = 'Pending Update'
    else:
        record = PaymentRecord(User_ID=user_id, Payment_ID=payment_id, Payment_File_Path=unique_name, Original_File_Name=original_name)
        db.session.add(record)
        
    db.session.commit()
    return jsonify({"message": "Payment proof uploaded successfully"}), 201