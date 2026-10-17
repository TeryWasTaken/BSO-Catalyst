from app import create_app
from extensions import db
from models import Assignment, Payment
from datetime import datetime, timedelta, timezone

app = create_app()

with app.app_context():
    # Create an Assignment
    assignment = Assignment(
        Assignment_Name="Database Systems 3NF Normalization",
        Target_StudentYear="026", 
        Assignment_TimeDateStart=datetime.now(timezone.utc),
        Assignment_TimeDateEnd=datetime.now(timezone.utc) + timedelta(days=3),
        Assignment_Desc="Submit the SQLite schema and ERD up to the 3rd Normal Form."
    )
    
    # Create a Payment requirement with a public dummy Google Sheet ID
    payment = Payment(
        Payment_Name="UKM SRT Robotics Registration Fee",
        Target_StudentYear="026",
        Payment_TimeDateStart=datetime.now(timezone.utc),
        Payment_TimeDateEnd=datetime.now(timezone.utc) + timedelta(days=14),
        Payment_Desc="Initial fee for the KRAI-Programmer division equipment.",
        Budget_Spreadsheet_ID="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms" # Standard Google dev test sheet
    )
    
    db.session.add(assignment)
    db.session.add(payment)
    db.session.commit()
    
    print("Database seeded successfully!")