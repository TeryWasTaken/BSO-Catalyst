from datetime import datetime, timezone
from extensions import db

class User(db.Model):
    __tablename__ = 'User'
    
    User_ID = db.Column(db.String(20), primary_key=True) 
    User_Name = db.Column(db.String(100), nullable=False)
    User_Email = db.Column(db.String(120), unique=True, nullable=False)
    User_Authority = db.Column(db.String(50), nullable=False)
    Password_Hash = db.Column(db.String(255), nullable=True)
    Device_Token = db.Column(db.String(255), nullable=True) # For Mobile Push Notifications

    applications = db.relationship('RecruitmentApplication', backref='user', lazy=True, cascade="all, delete-orphan")
    submissions = db.relationship('AssignmentSubmission', backref='user', lazy=True, cascade="all, delete-orphan")
    payments = db.relationship('PaymentRecord', backref='user', lazy=True, cascade="all, delete-orphan")

class Event(db.Model):
    __tablename__ = 'Event'
    Event_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Event_Name = db.Column(db.String(150), nullable=False)
    Event_TimeDateStart = db.Column(db.DateTime, nullable=False)
    Event_TimeDateEnd = db.Column(db.DateTime, nullable=False)
    Event_Desc = db.Column(db.Text, nullable=True)
    Created_At = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Recruitment(db.Model):
    __tablename__ = 'Recruitment'
    Recr_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Recr_Name = db.Column(db.String(150), nullable=False)
    Recr_TimeDateStart = db.Column(db.DateTime, nullable=False)
    Recr_TimeDateEnd = db.Column(db.DateTime, nullable=False)
    Recr_Desc = db.Column(db.Text, nullable=True)
    Created_At = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Assignment(db.Model):
    __tablename__ = 'Assignment'
    Assignment_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Assignment_Name = db.Column(db.String(150), nullable=False)
    Target_StudentYear = db.Column(db.String(10), nullable=True)
    Assignment_TimeDateStart = db.Column(db.DateTime, nullable=False)
    Assignment_TimeDateEnd = db.Column(db.DateTime, nullable=False)
    Assignment_Desc = db.Column(db.Text, nullable=True)
    Created_At = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Payment(db.Model):
    __tablename__ = 'Payment'
    Payment_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Payment_Name = db.Column(db.String(150), nullable=False)
    Target_StudentYear = db.Column(db.String(10), nullable=True) 
    Payment_TimeDateStart = db.Column(db.DateTime, nullable=False)
    Payment_TimeDateEnd = db.Column(db.DateTime, nullable=False)
    Payment_Desc = db.Column(db.Text, nullable=True)
    
    # NEW: Store the ID of the Google Sheet (e.g., "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms")
    Budget_Spreadsheet_ID = db.Column(db.String(100), nullable=True) 
    
    Created_At = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    records = db.relationship('PaymentRecord', backref='payment', lazy=True, cascade="all, delete-orphan")

class RecruitmentApplication(db.Model):
    __tablename__ = 'Recruitment_Application'
    Application_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    User_ID = db.Column(db.String(20), db.ForeignKey('User.User_ID', ondelete='CASCADE'), nullable=False)
    Recr_ID = db.Column(db.Integer, db.ForeignKey('Recruitment.Recr_ID', ondelete='CASCADE'), nullable=False)
    Registration_File_Path = db.Column(db.String(255), nullable=True)
    Original_File_Name = db.Column(db.String(255), nullable=True)
    Acceptance_Status = db.Column(db.String(20), default='Pending') 
    Admin_Feedback = db.Column(db.Text, nullable=True)
    Created_At = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    __table_args__ = (db.UniqueConstraint('User_ID', 'Recr_ID', name='_user_recr_uc'),)

class AssignmentSubmission(db.Model):
    __tablename__ = 'Assignment_Submission'
    Submission_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    User_ID = db.Column(db.String(20), db.ForeignKey('User.User_ID', ondelete='CASCADE'), nullable=False)
    Assignment_ID = db.Column(db.Integer, db.ForeignKey('Assignment.Assignment_ID', ondelete='CASCADE'), nullable=False)
    Submission_File_Path = db.Column(db.String(255), nullable=False)
    Original_File_Name = db.Column(db.String(255), nullable=False)
    Review_Status = db.Column(db.String(20), default='Submitted') 
    Grade = db.Column(db.Integer, nullable=True) 
    Admin_Feedback = db.Column(db.Text, nullable=True)
    Created_At = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    __table_args__ = (db.UniqueConstraint('User_ID', 'Assignment_ID', name='_user_assignment_uc'),)

class PaymentRecord(db.Model):
    __tablename__ = 'Payment_Record'
    Record_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    User_ID = db.Column(db.String(20), db.ForeignKey('User.User_ID', ondelete='CASCADE'), nullable=False)
    Payment_ID = db.Column(db.Integer, db.ForeignKey('Payment.Payment_ID', ondelete='CASCADE'), nullable=False)
    Payment_File_Path = db.Column(db.String(255), nullable=False)
    Original_File_Name = db.Column(db.String(255), nullable=False)
    Verification_Status = db.Column(db.String(20), default='Pending')
    Admin_Feedback = db.Column(db.Text, nullable=True)
    Created_At = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    __table_args__ = (db.UniqueConstraint('User_ID', 'Payment_ID', name='_user_payment_uc'),)