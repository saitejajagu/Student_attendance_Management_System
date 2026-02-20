from datetime import datetime
import secrets
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum('admin', 'teacher', 'student', name='user_role'), default='teacher')
    full_name = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active_user = db.Column(db.Boolean, default=True)
    reset_token = db.Column(db.String(64), nullable=True, unique=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self):
        self.reset_token = secrets.token_urlsafe(32)
        from datetime import timedelta
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=2)
        return self.reset_token

    def is_reset_token_valid(self, token):
        return (
            self.reset_token == token and
            self.reset_token_expiry is not None and
            datetime.utcnow() < self.reset_token_expiry
        )

    def __repr__(self):
        return f'<User {self.username}>'


class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    class_name = db.Column(db.String(50), nullable=True)
    section = db.Column(db.String(10), nullable=True)
    gender = db.Column(db.Enum('Male', 'Female', 'Other', name='gender_enum'), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    address = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    # Link to a login user account
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    attendances = db.relationship('Attendance', backref='student', lazy=True, cascade='all, delete-orphan')
    leave_requests = db.relationship('LeaveRequest', backref='student', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Student {self.student_id} - {self.full_name}>'


class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    teacher_name = db.Column(db.String(120), nullable=True)
    class_name = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    attendances = db.relationship('Attendance', backref='subject', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Subject {self.code} - {self.name}>'


class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    status = db.Column(db.Enum('Present', 'Absent', 'Late', 'Excused', name='status_enum'), nullable=False, default='Present')
    remarks = db.Column(db.String(255), nullable=True)
    marked_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    marked_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('student_id', 'subject_id', 'date', name='unique_attendance'),
    )

    def __repr__(self):
        return f'<Attendance {self.student_id} - {self.date} - {self.status}>'


class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    from_date = db.Column(db.Date, nullable=False)
    to_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum('Pending', 'Approved', 'Rejected', name='leave_status'), default='Pending')
    admin_note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<LeaveRequest {self.student_id} {self.from_date}~{self.to_date} {self.status}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
