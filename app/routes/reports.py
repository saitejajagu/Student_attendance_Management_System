import csv
import io
from flask import Blueprint, render_template, request, flash, make_response
from flask_login import login_required
from app import db
from app.models import Attendance, Student, Subject
from datetime import datetime, date

reports = Blueprint('reports', __name__)


@reports.route('/reports')
@login_required
def view_reports():
    students_list = Student.query.filter_by(is_active=True).order_by(Student.full_name).all()
    subjects_list = Subject.query.filter_by(is_active=True).order_by(Subject.name).all()

    # Filters
    student_id = request.args.get('student_id', '')
    subject_id = request.args.get('subject_id', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    status_filter = request.args.get('status', '')

    query = db.session.query(Attendance, Student, Subject).join(
        Student, Attendance.student_id == Student.id
    ).join(
        Subject, Attendance.subject_id == Subject.id
    ).filter(Student.is_active == True)

    if student_id:
        query = query.filter(Attendance.student_id == int(student_id))
    if subject_id:
        query = query.filter(Attendance.subject_id == int(subject_id))
    if date_from:
        try:
            query = query.filter(Attendance.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
        except ValueError:
            pass
    if date_to:
        try:
            query = query.filter(Attendance.date <= datetime.strptime(date_to, '%Y-%m-%d').date())
        except ValueError:
            pass
    if status_filter:
        query = query.filter(Attendance.status == status_filter)

    records = query.order_by(Attendance.date.desc()).all()

    # Per-student summary
    summary = {}
    for att, stu, sub in records:
        key = stu.id
        if key not in summary:
            summary[key] = {
                'student': stu,
                'total': 0,
                'present': 0,
                'absent': 0,
                'late': 0,
                'excused': 0,
            }
        summary[key]['total'] += 1
        s = att.status.lower()
        if s == 'present':
            summary[key]['present'] += 1
        elif s == 'absent':
            summary[key]['absent'] += 1
        elif s == 'late':
            summary[key]['late'] += 1
        elif s == 'excused':
            summary[key]['excused'] += 1

    for key in summary:
        total = summary[key]['total']
        present = summary[key]['present'] + summary[key]['late']
        summary[key]['percentage'] = round((present / total * 100) if total > 0 else 0, 1)

    summary_list = sorted(summary.values(), key=lambda x: x['percentage'])

    return render_template('reports.html',
                           records=records,
                           summary=summary_list,
                           students=students_list,
                           subjects=subjects_list,
                           filters={
                               'student_id': student_id,
                               'subject_id': subject_id,
                               'date_from': date_from,
                               'date_to': date_to,
                               'status': status_filter,
                           })


@reports.route('/reports/export')
@login_required
def export_csv():
    student_id = request.args.get('student_id', '')
    subject_id = request.args.get('subject_id', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    status_filter = request.args.get('status', '')

    query = db.session.query(Attendance, Student, Subject).join(
        Student, Attendance.student_id == Student.id
    ).join(
        Subject, Attendance.subject_id == Subject.id
    ).filter(Student.is_active == True)

    if student_id:
        query = query.filter(Attendance.student_id == int(student_id))
    if subject_id:
        query = query.filter(Attendance.subject_id == int(subject_id))
    if date_from:
        try:
            query = query.filter(Attendance.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
        except ValueError:
            pass
    if date_to:
        try:
            query = query.filter(Attendance.date <= datetime.strptime(date_to, '%Y-%m-%d').date())
        except ValueError:
            pass
    if status_filter:
        query = query.filter(Attendance.status == status_filter)

    records = query.order_by(Attendance.date.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Student ID', 'Student Name', 'Class', 'Subject', 'Subject Code', 'Status', 'Remarks'])
    for att, stu, sub in records:
        writer.writerow([
            att.date.strftime('%Y-%m-%d'),
            stu.student_id,
            stu.full_name,
            stu.class_name or '',
            sub.name,
            sub.code,
            att.status,
            att.remarks or ''
        ])

    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename=attendance_{date.today().strftime("%Y%m%d")}.csv'
    response.headers['Content-type'] = 'text/csv'
    return response
