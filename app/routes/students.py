from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Student
from datetime import datetime

students = Blueprint('students', __name__)


@students.route('/students')
@login_required
def list_students():
    search = request.args.get('search', '')
    class_filter = request.args.get('class_name', '')
    query = Student.query.filter_by(is_active=True)
    if search:
        query = query.filter(
            db.or_(
                Student.full_name.ilike(f'%{search}%'),
                Student.student_id.ilike(f'%{search}%'),
                Student.email.ilike(f'%{search}%')
            )
        )
    if class_filter:
        query = query.filter_by(class_name=class_filter)
    all_students = query.order_by(Student.full_name).all()
    classes = db.session.query(Student.class_name).filter(Student.class_name.isnot(None)).distinct().all()
    classes = [c[0] for c in classes if c[0]]
    return render_template('students.html', students=all_students, classes=classes,
                           search=search, class_filter=class_filter)


@students.route('/students/add', methods=['POST'])
@login_required
def add_student():
    try:
        dob_str = request.form.get('date_of_birth', '')
        dob = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None
        student = Student(
            student_id=request.form['student_id'].strip(),
            full_name=request.form['full_name'].strip(),
            email=request.form.get('email', '').strip() or None,
            phone=request.form.get('phone', '').strip() or None,
            class_name=request.form.get('class_name', '').strip() or None,
            section=request.form.get('section', '').strip() or None,
            gender=request.form.get('gender') or None,
            date_of_birth=dob,
            address=request.form.get('address', '').strip() or None,
        )
        db.session.add(student)
        db.session.commit()
        flash(f'Student "{student.full_name}" added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding student: {str(e)}', 'danger')
    return redirect(url_for('students.list_students'))


@students.route('/students/edit/<int:student_id>', methods=['POST'])
@login_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    try:
        dob_str = request.form.get('date_of_birth', '')
        student.student_id = request.form['student_id'].strip()
        student.full_name = request.form['full_name'].strip()
        student.email = request.form.get('email', '').strip() or None
        student.phone = request.form.get('phone', '').strip() or None
        student.class_name = request.form.get('class_name', '').strip() or None
        student.section = request.form.get('section', '').strip() or None
        student.gender = request.form.get('gender') or None
        student.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None
        student.address = request.form.get('address', '').strip() or None
        db.session.commit()
        flash(f'Student "{student.full_name}" updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating student: {str(e)}', 'danger')
    return redirect(url_for('students.list_students'))


@students.route('/students/delete/<int:student_id>', methods=['POST'])
@login_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    try:
        student.is_active = False
        db.session.commit()
        flash(f'Student "{student.full_name}" removed successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error removing student: {str(e)}', 'danger')
    return redirect(url_for('students.list_students'))


@students.route('/students/get/<int:student_id>')
@login_required
def get_student(student_id):
    student = Student.query.get_or_404(student_id)
    return jsonify({
        'id': student.id,
        'student_id': student.student_id,
        'full_name': student.full_name,
        'email': student.email or '',
        'phone': student.phone or '',
        'class_name': student.class_name or '',
        'section': student.section or '',
        'gender': student.gender or '',
        'date_of_birth': student.date_of_birth.strftime('%Y-%m-%d') if student.date_of_birth else '',
        'address': student.address or '',
    })
