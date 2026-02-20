from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Attendance, Student, Subject
from datetime import datetime, date

attendance = Blueprint('attendance', __name__)


@attendance.route('/dashboard')
@login_required
def dashboard():
    from sqlalchemy import func
    total_students = Student.query.filter_by(is_active=True).count()
    total_subjects = Subject.query.filter_by(is_active=True).count()
    today = date.today()
    today_records = Attendance.query.filter_by(date=today).count()
    today_present = Attendance.query.filter_by(date=today, status='Present').count()
    today_rate = round((today_present / today_records * 100) if today_records > 0 else 0, 1)

    # Weekly attendance data for chart (last 7 days)
    from datetime import timedelta
    weekly_data = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        total = Attendance.query.filter_by(date=d).count()
        present = Attendance.query.filter_by(date=d, status='Present').count()
        weekly_data.append({
            'date': d.strftime('%a %d'),
            'present': present,
            'absent': total - present,
            'total': total
        })

    # Recent attendance records
    recent = db.session.query(Attendance, Student, Subject).join(
        Student, Attendance.student_id == Student.id
    ).join(
        Subject, Attendance.subject_id == Subject.id
    ).order_by(Attendance.marked_at.desc()).limit(10).all()

    return render_template('dashboard.html',
                           total_students=total_students,
                           total_subjects=total_subjects,
                           today_records=today_records,
                           today_rate=today_rate,
                           weekly_data=weekly_data,
                           recent=recent,
                           today=today.strftime('%B %d, %Y'))


@attendance.route('/attendance', methods=['GET', 'POST'])
@login_required
def mark_attendance():
    subjects_list = Subject.query.filter_by(is_active=True).order_by(Subject.name).all()
    students_list = []
    selected_subject = None
    selected_date = date.today().strftime('%Y-%m-%d')
    existing_map = {}

    if request.method == 'GET' and (request.args.get('subject_id') or request.args.get('date')):
        subject_id = request.args.get('subject_id')
        att_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))
        selected_date = att_date
        if subject_id:
            selected_subject = Subject.query.get(subject_id)
            students_list = Student.query.filter_by(is_active=True).order_by(Student.full_name).all()
            try:
                d = datetime.strptime(att_date, '%Y-%m-%d').date()
                existing = Attendance.query.filter_by(subject_id=subject_id, date=d).all()
                existing_map = {e.student_id: e for e in existing}
            except ValueError:
                pass

    if request.method == 'POST':
        subject_id = request.form.get('subject_id')
        att_date_str = request.form.get('attendance_date')
        try:
            att_date = datetime.strptime(att_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            flash('Invalid date format.', 'danger')
            return redirect(url_for('attendance.mark_attendance'))

        all_students = Student.query.filter_by(is_active=True).all()
        saved = 0
        for student in all_students:
            status = request.form.get(f'status_{student.id}', 'Absent')
            remarks = request.form.get(f'remarks_{student.id}', '')
            # Upsert attendance
            existing = Attendance.query.filter_by(
                student_id=student.id,
                subject_id=subject_id,
                date=att_date
            ).first()
            if existing:
                existing.status = status
                existing.remarks = remarks
                existing.marked_by = current_user.id
                existing.marked_at = datetime.utcnow()
            else:
                record = Attendance(
                    student_id=student.id,
                    subject_id=subject_id,
                    date=att_date,
                    status=status,
                    remarks=remarks,
                    marked_by=current_user.id
                )
                db.session.add(record)
            saved += 1
        try:
            db.session.commit()
            flash(f'Attendance saved for {saved} students!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving attendance: {str(e)}', 'danger')
        return redirect(url_for('attendance.mark_attendance',
                                subject_id=subject_id,
                                date=att_date_str))

    return render_template('attendance.html',
                           subjects=subjects_list,
                           students=students_list,
                           selected_subject=selected_subject,
                           selected_date=selected_date,
                           existing_map=existing_map)
