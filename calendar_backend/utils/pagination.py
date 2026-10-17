from flask import request

def get_pagination_params():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('limit', 10, type=int)
    return page, per_page