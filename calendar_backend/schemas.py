from extensions import ma
from models import User, Assignment, AssignmentSubmission, Payment

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        exclude = ("Password_Hash", "Device_Token")

class AssignmentSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Assignment
        load_instance = True

# NEW: Add the Payment schema here
class PaymentSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Payment
        load_instance = True

# Initialize single and multiple item serializers
user_schema = UserSchema()
users_schema = UserSchema(many=True)

assignment_schema = AssignmentSchema()
assignments_schema = AssignmentSchema(many=True)

# NEW: Initialize the payment serializers here
payment_schema = PaymentSchema()
payments_schema = PaymentSchema(many=True)

from models import Event, Recruitment

class EventSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Event
        load_instance = True

class RecruitmentSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Recruitment
        load_instance = True

events_schema = EventSchema(many=True)
recruitments_schema = RecruitmentSchema(many=True)