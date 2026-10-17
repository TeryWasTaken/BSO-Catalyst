import os
from app import create_app
from extensions import db
from models import User, Assignment, Payment, Event, Recruitment
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash

app = create_app()

ADMIN_ID = "H1D026052"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")  # change this!

with app.app_context():
    # Admin account (login uses User ID + password)
    admin = User.query.get(ADMIN_ID)
    if not admin:
        admin = User(
            User_ID=ADMIN_ID,
            User_Name="Mahatma Grand Austin Kasandi",
            User_Email=f"{ADMIN_ID}@mhs.unsoed.ac.id".lower(),
            User_Authority="admin",
        )
        db.session.add(admin)
    admin.Password_Hash = generate_password_hash(ADMIN_PASSWORD)

    # Sample calendar data (only when the tables are empty, so re-running is safe)
    now = datetime.now(timezone.utc)

    if Assignment.query.count() == 0:
        db.session.add(Assignment(
            Assignment_Name="Database Systems 3NF Normalization",
            Target_StudentYear="026",
            Assignment_TimeDateStart=now,
            Assignment_TimeDateEnd=now + timedelta(days=3),
            Assignment_Desc="Submit the SQLite schema and ERD up to the 3rd Normal Form."
        ))

    if Payment.query.count() == 0:
        db.session.add(Payment(
            Payment_Name="UKM SRT Robotics Registration Fee",
            Target_StudentYear="026",
            Payment_TimeDateStart=now,
            Payment_TimeDateEnd=now + timedelta(days=14),
            Payment_Desc="Initial fee for the KRAI-Programmer division equipment.",
            Budget_Spreadsheet_ID="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"  # Standard Google dev test sheet
        ))

    if Event.query.count() == 0:
        db.session.add(Event(
            Event_Name="Faculty Open Day",
            Event_TimeDateStart=now + timedelta(days=5, hours=2),
            Event_TimeDateEnd=now + timedelta(days=5, hours=8),
            Event_Desc="Campus tour and booth exhibition for new students."
        ))

    if Recruitment.query.count() == 0:
        db.session.add(Recruitment(
            Recr_Name="UKM SRT Robotics Recruitment",
            Recr_TimeDateStart=now,
            Recr_TimeDateEnd=now + timedelta(days=10),
            Recr_Desc="Open recruitment for the KRAI-Programmer division. Upload your registration form."
        ))

    db.session.commit()

    print("Database seeded successfully!")
    print(f"Admin login -> User ID: {ADMIN_ID} | Password: {ADMIN_PASSWORD}")
