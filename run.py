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
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        print("[INFO] Running on Railway. Skipping manual database creation. Database should be provisioned via Railway.")
        return

    try:
        conn = pymysql.connect(host=os.environ.get('DB_HOST', 'localhost'), 
                               user=os.environ.get('DB_USER', 'root'), 
                               password=os.environ.get('DB_PASSWORD', 'root'))
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {os.environ.get('DB_NAME', 'attendance_db')} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit()
        cursor.close()
        conn.close()
        print(f"[OK] Database '{os.environ.get('DB_NAME', 'attendance_db')}' ready.")
    except Exception as e:
        print(f"[ERR] Could not connect to MySQL: {e}")
        # On Railway, we don't want to crash if the DB isn't ready yet during build/start if SQLAlchemy handles it
        if not os.environ.get('RAILWAY_ENVIRONMENT'):
            raise

def migrate_schema():
    """Apply incremental schema changes to existing tables (safe to re-run)."""
    if os.environ.get('RAILWAY_ENVIRONMENT'):
         print("[INFO] Skipping manual migration script on Railway. SQLAlchemy db.create_all() will be used.")
         return
    
    try:
        db_name = os.environ.get('DB_NAME', 'attendance_db')
        conn = pymysql.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'root'),
            password=os.environ.get('DB_PASSWORD', 'root'),
            database=db_name
        )
        cursor = conn.cursor()

        # 1. Add user_id FK column to students if missing
        cursor.execute(f"""
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA='{db_name}' AND TABLE_NAME='students' AND COLUMN_NAME='user_id'
        """)
        if cursor.fetchone()[0] == 0:
            cursor.execute("ALTER TABLE students ADD COLUMN user_id INT NULL, ADD CONSTRAINT fk_students_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL")
            print("[OK] Added user_id column to students table.")

        # 2. Expand user_role enum to include 'student'
        cursor.execute(f"""
            SELECT COLUMN_TYPE FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA='{db_name}' AND TABLE_NAME='users' AND COLUMN_NAME='role'
        """)
        row = cursor.fetchone()
        if row and 'student' not in row[0]:
            cursor.execute("ALTER TABLE users MODIFY COLUMN role ENUM('admin','teacher','student') DEFAULT 'teacher'")
            print("[OK] Updated user_role enum to include 'student'.")

        # 3. Add password reset token columns to users
        cursor.execute(f"""
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA='{db_name}' AND TABLE_NAME='users' AND COLUMN_NAME='reset_token'
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

# ... (seed_data function remains the same)

app = create_app(os.environ.get('FLASK_CONFIG', 'production'))

if __name__ == '__main__':
    ensure_database()
    migrate_schema()
    with app.app_context():
        seed_data(app)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=os.environ.get('FLASK_DEBUG', 'False') == 'True')
