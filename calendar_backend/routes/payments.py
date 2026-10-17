import csv
import requests
from io import StringIO
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from models import Payment

payments_bp = Blueprint('payments', __name__, url_prefix='/api/payments')

@payments_bp.route('/<int:payment_id>/budget', methods=['GET'])
@jwt_required()
def get_payment_budget(payment_id):
    # 1. Find the payment in the database
    payment = Payment.query.get_or_404(payment_id)
    
    if not payment.Budget_Spreadsheet_ID:
        return jsonify({"message": "No budget spreadsheet linked to this payment."}), 404
        
    # 2. Use the Google Sheets CSV Export Trick
    sheet_id = payment.Budget_Spreadsheet_ID
    csv_export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    
    try:
        # 3. Fetch the data from Google
        response = requests.get(csv_export_url)
        response.raise_for_status() # Check for errors (like 404 if the sheet isn't public)
        
        # 4. Parse the CSV data into a list of dictionaries (JSON)
        csv_data = StringIO(response.text)
        reader = csv.DictReader(csv_data)
        
        budget_items = []
        for row in reader:
            budget_items.append(row)
            
        # 5. Send clean JSON to the mobile app!
        return jsonify({
            "payment_name": payment.Payment_Name,
            "budget_breakdown": budget_items
        }), 200
        
    except Exception as e:
        return jsonify({"error": "Failed to fetch spreadsheet data", "details": str(e)}), 500