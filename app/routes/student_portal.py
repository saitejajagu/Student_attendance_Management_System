from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import Attendance, Student, Subject, LeaveRequest
from datetime import datetime, date

student_portal = Blueprint('student_portal', __name__)


def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            flash('Access denied. Student account required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_student():
    """Get the Student record linked to the current logged-in user."""
    return Student.query.filter_by(user_id=current_user.id, is_active=True).first()


@student_portal.route('/student/dashboard')
@login_required
@student_required
def dashboard():
    student = get_current_student()
    if not student:
        flash('No student record linked to your account. Please contact admin.', 'warning')
        return redirect(url_for('auth.logout'))

    today = date.today()
    total_records = Attendance.query.filter_by(student_id=student.id).count()
    present_count = Attendance.query.filter_by(student_id=student.id, status='Present').count()
    absent_count = Attendance.query.filter_by(student_id=student.id, status='Absent').count()
    late_count = Attendance.query.filter_by(student_id=student.id, status='Late').count()
    attendance_rate = round((present_count / total_records * 100) if total_records > 0 else 0, 1)

    # Recent 10 attendance records
    recent = db.session.query(Attendance, Subject).join(
        Subject, Attendance.subject_id == Subject.id
    ).filter(
        Attendance.student_id == student.id
    ).order_by(Attendance.date.desc()).limit(10).all()

    # Pending leave requests
    pending_leaves = LeaveRequest.query.filter_by(
        student_id=student.id, status='Pending'
    ).count()

    # Subject-wise attendance summary
    subjects_summary = []
    subjects = Subject.query.filter_by(is_active=True).all()
    for subj in subjects:
        total = Attendance.query.filter_by(student_id=student.id, subject_id=subj.id).count()
        if total > 0:
            pres = Attendance.query.filter_by(student_id=student.id, subject_id=subj.id, status='Present').count()
            rate = round(pres / total * 100, 1)
            subjects_summary.append({
                'name': subj.name,
                'code': subj.code,
                'total': total,
                'present': pres,
                'rate': rate
            })

    return render_template('student/dashboard.html',
                           student=student,
                           total_records=total_records,
                           present_count=present_count,
                           absent_count=absent_count,
                           late_count=late_count,
                           attendance_rate=attendance_rate,
                           recent=recent,
                           pending_leaves=pending_leaves,
                           subjects_summary=subjects_summary,
                           today=today.strftime('%B %d, %Y'))


@student_portal.route('/student/attendance')
@login_required
@student_required
def my_attendance():
    student = get_current_student()
    if not student:
        return redirect(url_for('auth.logout'))

    subject_filter = request.args.get('subject_id', '')
    status_filter = request.args.get('status', '')
    from_date_str = request.args.get('from_date', '')
    to_date_str = request.args.get('to_date', '')

    query = db.session.query(Attendance, Subject).join(
        Subject, Attendance.subject_id == Subject.id
    ).filter(Attendance.student_id == student.id)

    if subject_filter:
        query = query.filter(Attendance.subject_id == int(subject_filter))
    if status_filter:
        query = query.filter(Attendance.status == status_filter)
    if from_date_str:
        try:
            fd = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            query = query.filter(Attendance.date >= fd)
        except ValueError:
            pass
    if to_date_str:
        try:
            td = datetime.strptime(to_date_str, '%Y-%m-%d').date()
            query = query.filter(Attendance.date <= td)
        except ValueError:
            pass

    records = query.order_by(Attendance.date.desc()).all()
    subjects = Subject.query.filter_by(is_active=True).order_by(Subject.name).all()

    return render_template('student/attendance.html',
                           student=student,
                           records=records,
                           subjects=subjects,
                           subject_filter=subject_filter,
                           status_filter=status_filter,
                           from_date=from_date_str,
                           to_date=to_date_str)


@student_portal.route('/student/leave')
@login_required
@student_required
def leave():
    student = get_current_student()
    if not student:
        return redirect(url_for('auth.logout'))
    leaves = LeaveRequest.query.filter_by(
        student_id=student.id
    ).order_by(LeaveRequest.created_at.desc()).all()
    return render_template('student/leave.html', student=student, leaves=leaves)


@student_portal.route('/student/leave/request', methods=['POST'])
@login_required
@student_required
def submit_leave():
    student = get_current_student()
    if not student:
        return redirect(url_for('auth.logout'))

    from_date_str = request.form.get('from_date', '')
    to_date_str = request.form.get('to_date', '')
    reason = request.form.get('reason', '').strip()

    if not from_date_str or not to_date_str or not reason:
        flash('All fields are required for a leave request.', 'danger')
        return redirect(url_for('student_portal.leave'))

    try:
        from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
        to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
        if to_date < from_date:
            flash('End date cannot be before start date.', 'danger')
            return redirect(url_for('student_portal.leave'))

        leave_req = LeaveRequest(
            student_id=student.id,
            from_date=from_date,
            to_date=to_date,
            reason=reason,
            status='Pending'
        )
        db.session.add(leave_req)
        db.session.commit()
        flash('Leave request submitted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting leave request: {str(e)}', 'danger')

    return redirect(url_for('student_portal.leave'))
