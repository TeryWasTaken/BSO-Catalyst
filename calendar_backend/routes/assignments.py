from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from models import Assignment
from schemas import assignments_schema
from utils.pagination import get_pagination_params

assignments_bp = Blueprint('assignments', __name__, url_prefix='/api/assignments')

@assignments_bp.route('/', methods=['GET'])
@jwt_required()
def get_assignments():
    page, per_page = get_pagination_params()
    
    # Query ordered by newest first
    pagination_obj = Assignment.query.order_by(Assignment.Created_At.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        "items": assignments_schema.dump(pagination_obj.items),
        "total": pagination_obj.total,
        "page": pagination_obj.page,
        "pages": pagination_obj.pages
    }), 200