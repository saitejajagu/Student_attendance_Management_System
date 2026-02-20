from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    login_manager.init_app(app)

    from app.routes.auth import auth as auth_bp
    from app.routes.students import students as students_bp
    from app.routes.subjects import subjects as subjects_bp
    from app.routes.attendance import attendance as attendance_bp
    from app.routes.reports import reports as reports_bp
    from app.routes.admin import admin_bp
    from app.routes.student_portal import student_portal as student_portal_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(subjects_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(student_portal_bp)

    return app
