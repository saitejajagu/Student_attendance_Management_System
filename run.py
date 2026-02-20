import os
import sys

# Fix Windows console encoding
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pymysql
from app import create_app, db
from app.models import User, Student, Subject


def ensure_database():
    try:
        conn = pymysql.connect(host='localhost', user='root', password='root')
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS attendance_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit()
        cursor.close()
        conn.close()
        print("[OK] Database 'attendance_db' ready.")
    except Exception as e:
        print(f"[ERR] Could not connect to MySQL: {e}")
        raise


def migrate_schema():
    """Apply incremental schema changes to existing tables (safe to re-run)."""
    try:
        conn = pymysql.connect(host='localhost', user='root', password='root', database='attendance_db')
        cursor = conn.cursor()

        # 1. Add user_id FK column to students if missing
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA='attendance_db' AND TABLE_NAME='students' AND COLUMN_NAME='user_id'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute("ALTER TABLE students ADD COLUMN user_id INT NULL, ADD CONSTRAINT fk_students_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL")
            print("[OK] Added user_id column to students table.")

        # 2. Expand user_role enum to include 'student'
        cursor.execute("""
            SELECT COLUMN_TYPE FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA='attendance_db' AND TABLE_NAME='users' AND COLUMN_NAME='role'
        """)
        row = cursor.fetchone()
        if row and 'student' not in row[0]:
            cursor.execute("ALTER TABLE users MODIFY COLUMN role ENUM('admin','teacher','student') DEFAULT 'teacher'")
            print("[OK] Updated user_role enum to include 'student'.")

        # 3. Add password reset token columns to users
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA='attendance_db' AND TABLE_NAME='users' AND COLUMN_NAME='reset_token'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute("ALTER TABLE users ADD COLUMN reset_token VARCHAR(64) NULL UNIQUE, ADD COLUMN reset_token_expiry DATETIME NULL")
            print("[OK] Added reset_token columns to users table.")

        conn.commit()
        cursor.close()
        conn.close()
        print("[OK] Schema migration complete.")
    except Exception as e:
        print(f"[WARN] Schema migration issue (may be safe to ignore): {e}")


def seed_data(app):
    with app.app_context():
        db.create_all()
        print("[OK] Tables created.")

        # --- Staff users ---
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@attendms.com',
                         full_name='System Administrator', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            print("[OK] Admin user created: admin / admin123")

        if not User.query.filter_by(username='teacher').first():
            teacher = User(username='teacher', email='teacher@attendms.com',
                           full_name='John Teacher', role='teacher')
            teacher.set_password('teacher123')
            db.session.add(teacher)
            print("[OK] Teacher user created: teacher / teacher123")

        # --- Students ---
        sample_students = [
            ('STU001', 'Aarav Sharma',  'aarav@example.com',  '9876543201', '10th Grade', 'A', 'Male'),
            ('STU002', 'Priya Patel',   'priya@example.com',  '9876543202', '10th Grade', 'A', 'Female'),
            ('STU003', 'Rohan Mehta',   'rohan@example.com',  '9876543203', '10th Grade', 'B', 'Male'),
            ('STU004', 'Sneha Reddy',   'sneha@example.com',  '9876543204', '10th Grade', 'B', 'Female'),
            ('STU005', 'Arjun Kumar',   'arjun@example.com',  '9876543205', '11th Grade', 'A', 'Male'),
            ('STU006', 'Meera Singh',   'meera@example.com',  '9876543206', '11th Grade', 'A', 'Female'),
            ('STU007', 'Vikram Joshi',  'vikram@example.com', '9876543207', '11th Grade', 'B', 'Male'),
            ('STU008', 'Divya Nair',    'divya@example.com',  '9876543208', '11th Grade', 'B', 'Female'),
        ]
        for sid, name, email, phone, cls, sec, gender in sample_students:
            if not Student.query.filter_by(student_id=sid).first():
                db.session.add(Student(student_id=sid, full_name=name, email=email,
                                       phone=phone, class_name=cls, section=sec, gender=gender))

        # --- Subjects ---
        sample_subjects = [
            ('Mathematics',      'MATH101', 'Dr. Ramesh Gupta',  '10th Grade'),
            ('Science',          'SCI101',  'Mrs. Lata Sharma',  '10th Grade'),
            ('English Language', 'ENG101',  'Mr. Anil Verma',    '10th Grade'),
            ('Social Studies',   'SS101',   'Mrs. Sunita Roy',   '10th Grade'),
            ('Physics',          'PHY201',  'Mr. Deepak Mishra', '11th Grade'),
            ('Chemistry',        'CHEM201', 'Dr. Kavita Joshi',  '11th Grade'),
        ]
        for name, code, teacher, cls in sample_subjects:
            if not Subject.query.filter_by(code=code).first():
                db.session.add(Subject(name=name, code=code, teacher_name=teacher, class_name=cls))

        db.session.commit()

        # --- Student login accounts (seed 2 demo accounts) ---
        # Link stu001 (Aarav Sharma) → student login
        if not User.query.filter_by(username='aarav').first():
            stu_user = User(username='aarav', email='aarav.login@attendms.com',
                            full_name='Aarav Sharma', role='student')
            stu_user.set_password('student123')
            db.session.add(stu_user)
            db.session.flush()
            stu_record = Student.query.filter_by(student_id='STU001').first()
            if stu_record and not stu_record.user_id:
                stu_record.user_id = stu_user.id
            print("[OK] Student user created: aarav / student123  (linked to STU001 Aarav Sharma)")

        if not User.query.filter_by(username='priya').first():
            stu_user2 = User(username='priya', email='priya.login@attendms.com',
                             full_name='Priya Patel', role='student')
            stu_user2.set_password('student123')
            db.session.add(stu_user2)
            db.session.flush()
            stu_record2 = Student.query.filter_by(student_id='STU002').first()
            if stu_record2 and not stu_record2.user_id:
                stu_record2.user_id = stu_user2.id
            print("[OK] Student user created: priya / student123  (linked to STU002 Priya Patel)")

        db.session.commit()
        print("[OK] Sample data seeded.")
        print("")
        print("  App running at: http://127.0.0.1:5000")
        print("")
        print("  Admin   login:   admin   / admin123")
        print("  Teacher login:   teacher / teacher123")
        print("  Student login:   aarav   / student123")
        print("  Student login:   priya   / student123")
        print("")


if __name__ == '__main__':
    ensure_database()
    migrate_schema()
    app = create_app('development')
    seed_data(app)
    app.run(host='0.0.0.0', port=5000, debug=True)
