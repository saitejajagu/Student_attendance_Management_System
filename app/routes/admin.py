from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import User, Student

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('attendance.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/admin/users')
@login_required
@admin_required
def list_users():
    role_filter = request.args.get('role', '')
    query = User.query
    if role_filter:
        query = query.filter_by(role=role_filter)
    users = query.order_by(User.created_at.desc()).all()
    students_unlinked = Student.query.filter(
        Student.is_active == True,
        Student.user_id == None
    ).order_by(Student.full_name).all()
    return render_template('admin/users.html',
                           users=users,
                           role_filter=role_filter,
                           students_unlinked=students_unlinked)


@admin_bp.route('/admin/users/create', methods=['POST'])
@login_required
@admin_required
def create_user():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip() or None
    full_name = request.form.get('full_name', '').strip()
    role = request.form.get('role', 'teacher')
    password = request.form.get('password', '')
    student_link_id = request.form.get('student_link_id', '')

    if not username or not password:
        flash('Username and password are required.', 'danger')
        return redirect(url_for('admin.list_users'))

    if User.query.filter_by(username=username).first():
        flash(f'Username "{username}" already exists.', 'danger')
        return redirect(url_for('admin.list_users'))

    try:
        user = User(username=username, email=email, full_name=full_name, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # get user.id

        # Link to student record if provided
        if role == 'student' and student_link_id:
            student = Student.query.get(int(student_link_id))
            if student:
                student.user_id = user.id

        db.session.commit()
        flash(f'User "{username}" created successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating user: {str(e)}', 'danger')

    return redirect(url_for('admin.list_users'))


@admin_bp.route('/admin/users/edit/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    try:
        user.full_name = request.form.get('full_name', '').strip()
        user.email = request.form.get('email', '').strip() or None
        user.role = request.form.get('role', user.role)

        new_password = request.form.get('password', '').strip()
        if new_password:
            user.set_password(new_password)

        db.session.commit()
        flash(f'User "{user.username}" updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating user: {str(e)}', 'danger')
    return redirect(url_for('admin.list_users'))


@admin_bp.route('/admin/users/toggle/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'warning')
        return redirect(url_for('admin.list_users'))
    try:
        user.is_active_user = not user.is_active_user
        db.session.commit()
        status = 'activated' if user.is_active_user else 'deactivated'
        flash(f'User "{user.username}" {status}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('admin.list_users'))


@admin_bp.route('/admin/users/get/<int:user_id>')
@login_required
@admin_required
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email or '',
        'full_name': user.full_name or '',
        'role': user.role,
        'is_active_user': user.is_active_user,
    })


@admin_bp.route('/admin/leave')
@login_required
@admin_required
def leave_requests():
    from app.models import LeaveRequest
    status_filter = request.args.get('status', '')
    query = db.session.query(LeaveRequest, Student).join(
        Student, LeaveRequest.student_id == Student.id
    )
    if status_filter:
        query = query.filter(LeaveRequest.status == status_filter)
    requests_list = query.order_by(LeaveRequest.created_at.desc()).all()
    return render_template('admin/leave.html',
                           requests_list=requests_list,
                           status_filter=status_filter)


@admin_bp.route('/admin/leave/review/<int:req_id>', methods=['POST'])
@login_required
@admin_required
def review_leave(req_id):
    from app.models import LeaveRequest
    from datetime import datetime
    leave = LeaveRequest.query.get_or_404(req_id)
    action = request.form.get('action')
    admin_note = request.form.get('admin_note', '').strip()
    if action in ('Approved', 'Rejected'):
        leave.status = action
        leave.admin_note = admin_note
        leave.reviewed_by = current_user.id
        leave.reviewed_at = datetime.utcnow()
        db.session.commit()
        flash(f'Leave request {action.lower()}.', 'success')
    return redirect(url_for('admin.leave_requests'))
