import os
from flask import Flask
from extensions import db, ma, jwt, cors
from routes.events import events_bp

from routes.auth import auth_bp
from routes.assignments import assignments_bp
from routes.files import files_bp
from routes.payments import payments_bp  
from routes.users import users_bp
from routes.admin import admin_bp

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

def create_app():
    app = Flask(__name__)
    
    # Configurations
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///calendar_tracking.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['JWT_SECRET_KEY'] = 'super-secret-change-this-in-production'
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  
    
    # Create necessary folders
    os.makedirs(os.path.join(UPLOAD_FOLDER, 'assignments'), exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_FOLDER, 'payments'), exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_FOLDER, 'registrations'), exist_ok=True)

    # Initialize Extensions
    db.init_app(app)
    ma.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(assignments_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(payments_bp)  
    app.register_blueprint(events_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(admin_bp)  

    with app.app_context():
        import models
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)