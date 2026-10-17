import os
from flask import Flask, send_from_directory
from extensions import db, ma, jwt, cors
from routes.events import events_bp
from routes.auth import auth_bp
from routes.assignments import assignments_bp
from routes.files import files_bp
from routes.payments import payments_bp  
from routes.users import users_bp
from routes.admin import admin_bp

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Use /tmp on Vercel (read-only filesystem workaround)
if os.environ.get('VERCEL'):
    UPLOAD_FOLDER = os.path.join('/tmp', 'uploads')
else:
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'frontend'))

def create_app():
    app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
    
    # Load cloud database URL or fallback to local SQLite
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(BASE_DIR, 'calendar_tracking.db'))
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'super-secret-change-this-in-production')
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  
    
    # Safely handle folder creation on read-only environments
    try:
        os.makedirs(os.path.join(UPLOAD_FOLDER, 'assignments'), exist_ok=True)
        os.makedirs(os.path.join(UPLOAD_FOLDER, 'payments'), exist_ok=True)
        os.makedirs(os.path.join(UPLOAD_FOLDER, 'registrations'), exist_ok=True)
    except OSError:
        pass

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

    @app.route('/')
    def index():
        return send_from_directory(FRONTEND_DIR, 'index.html')

    with app.app_context():
        import models
        try:
            db.create_all()
        except Exception as e:
            print(f"Database initialization deferred: {e}")

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)