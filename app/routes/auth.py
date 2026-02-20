from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app import db

auth = Blueprint('auth', __name__)


@auth.route('/')
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'student':
            return redirect(url_for('student_portal.dashboard'))
        return redirect(url_for('attendance.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password) and user.is_active_user:
            login_user(user, remember=bool(remember))
            flash(f'Welcome back, {user.full_name or user.username}!', 'success')
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            if user.role == 'student':
                return redirect(url_for('student_portal.dashboard'))
            return redirect(url_for('attendance.dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template('login.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('attendance.dashboard'))

    reset_link = None
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).filter_by(is_active_user=True).first()

        if user:
            token = user.generate_reset_token()
            db.session.commit()
            reset_link = url_for('auth.reset_password', token=token, _external=True)
        else:
            flash('No active account found with that username or email.', 'danger')

    return render_template('forgot_password.html', reset_link=reset_link)


@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('attendance.dashboard'))

    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.is_reset_token_valid(token):
        flash('This reset link is invalid or has expired. Please request a new one.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')
        if len(new_password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
        elif new_password != confirm:
            flash('Passwords do not match.', 'danger')
        else:
            user.set_password(new_password)
            user.reset_token = None
            user.reset_token_expiry = None
            db.session.commit()
            flash('Password reset successfully! You can now login.', 'success')
            return redirect(url_for('auth.login'))

    return render_template('reset_password.html', token=token, username=user.username)
