from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required
from app import db
from app.models import Subject

subjects = Blueprint('subjects', __name__)


@subjects.route('/subjects')
@login_required
def list_subjects():
    search = request.args.get('search', '')
    query = Subject.query.filter_by(is_active=True)
    if search:
        query = query.filter(
            db.or_(
                Subject.name.ilike(f'%{search}%'),
                Subject.code.ilike(f'%{search}%'),
                Subject.teacher_name.ilike(f'%{search}%')
            )
        )
    all_subjects = query.order_by(Subject.name).all()
    return render_template('subjects.html', subjects=all_subjects, search=search)


@subjects.route('/subjects/add', methods=['POST'])
@login_required
def add_subject():
    try:
        subject = Subject(
            name=request.form['name'].strip(),
            code=request.form['code'].strip().upper(),
            teacher_name=request.form.get('teacher_name', '').strip() or None,
            class_name=request.form.get('class_name', '').strip() or None,
            description=request.form.get('description', '').strip() or None,
        )
        db.session.add(subject)
        db.session.commit()
        flash(f'Subject "{subject.name}" added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding subject: {str(e)}', 'danger')
    return redirect(url_for('subjects.list_subjects'))


@subjects.route('/subjects/edit/<int:subject_id>', methods=['POST'])
@login_required
def edit_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    try:
        subject.name = request.form['name'].strip()
        subject.code = request.form['code'].strip().upper()
        subject.teacher_name = request.form.get('teacher_name', '').strip() or None
        subject.class_name = request.form.get('class_name', '').strip() or None
        subject.description = request.form.get('description', '').strip() or None
        db.session.commit()
        flash(f'Subject "{subject.name}" updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating subject: {str(e)}', 'danger')
    return redirect(url_for('subjects.list_subjects'))


@subjects.route('/subjects/delete/<int:subject_id>', methods=['POST'])
@login_required
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    try:
        subject.is_active = False
        db.session.commit()
        flash(f'Subject "{subject.name}" removed successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error removing subject: {str(e)}', 'danger')
    return redirect(url_for('subjects.list_subjects'))


@subjects.route('/subjects/get/<int:subject_id>')
@login_required
def get_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    return jsonify({
        'id': subject.id,
        'name': subject.name,
        'code': subject.code,
        'teacher_name': subject.teacher_name or '',
        'class_name': subject.class_name or '',
        'description': subject.description or '',
    })
