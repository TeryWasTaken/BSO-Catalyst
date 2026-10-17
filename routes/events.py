from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from models import Event, Recruitment, Assignment, Payment
from schemas import events_schema, recruitments_schema, assignments_schema, payments_schema

events_bp = Blueprint('events', __name__, url_prefix='/api/events')

@events_bp.route('/calendar', methods=['GET'])
@jwt_required()
def get_calendar_feed():
    # Fetch all records
    events = Event.query.all()
    recruitments = Recruitment.query.all()
    assignments = Assignment.query.all()
    payments = Payment.query.all()

    # Package them into one unified JSON response
    return jsonify({
        "events": events_schema.dump(events),
        "recruitments": recruitments_schema.dump(recruitments),
        "assignments": assignments_schema.dump(assignments),
        "payments": payments_schema.dump(payments)
    }), 200