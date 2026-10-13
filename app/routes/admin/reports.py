"""
Admin Reports Routes.
Handles generating print-friendly HTML and CSV exports.
"""

import csv
import io
from flask import Blueprint, render_template, request, make_response, flash, redirect, url_for
from app.routes.admin_routes import admin_required
from app.database import get_db_connection
from app.database.admin_queries import get_all_exams

reports_bp = Blueprint('admin_reports', __name__, url_prefix='/admin/reports')


def get_exam_summary_report():
    """Fetch data from the vw_exam_summary view."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM vw_exam_summary ORDER BY exam_date DESC")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_attendance_report(exam_id):
    """Fetch attendance data for a specific exam."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT st.registration_no, st.name AS student_name, 
                   se.seat_number, a.status AS attendance_status, 
                   a.check_in_time, auth.method, auth.verification_status
            FROM SeatAllocation sa
            JOIN Student st ON sa.student_id = st.student_id
            JOIN Seat se ON sa.seat_id = se.seat_id
            LEFT JOIN Attendance a ON sa.allocation_id = a.allocation_id
            LEFT JOIN Authentication auth ON sa.allocation_id = auth.allocation_id
            WHERE sa.exam_id = %s AND sa.allocation_status = 'Allocated'
            ORDER BY se.seat_number
        ''', (exam_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


@reports_bp.route('/')
@admin_required
def index():
    """Reports Dashboard."""
    exams = get_all_exams()
    return render_template('admin/reports/index.html', exams=exams)


@reports_bp.route('/exam_summary')
@admin_required
def exam_summary():
    """View Exam Summary Report."""
    data = get_exam_summary_report()
    
    if request.args.get('export') == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Exam ID', 'Subject Code', 'Subject Name', 'Type', 'Date', 'Room', 'Total Allocated', 'Total Alerts'])
        for row in data:
            writer.writerow([
                row['exam_id'], row['subject_code'], row['subject_name'], 
                row['exam_type'], row['exam_date'], f"{row['building']} {row['room_number']}", 
                row['total_allocated'], row['total_alerts']
            ])
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = 'attachment; filename=exam_summary_report.csv'
        response.headers['Content-Type'] = 'text/csv'
        return response

    return render_template('admin/reports/exam_summary.html', data=data)


@reports_bp.route('/attendance')
@admin_required
def attendance():
    """View Attendance Sheet for a specific exam."""
    exam_id = request.args.get('exam_id')
    if not exam_id:
        flash('Please select an exam first.', 'warning')
        return redirect(url_for('admin_reports.index'))
    
    exams = get_all_exams()
    selected_exam = next((e for e in exams if str(e['exam_id']) == str(exam_id)), None)
    
    if not selected_exam:
        flash('Exam not found.', 'danger')
        return redirect(url_for('admin_reports.index'))

    data = get_attendance_report(exam_id)

    if request.args.get('export') == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Registration No', 'Student Name', 'Seat Number', 'Attendance Status', 'Check-in Time', 'Auth Method', 'Auth Status'])
        for row in data:
            writer.writerow([
                row['registration_no'], row['student_name'], row['seat_number'],
                row['attendance_status'] or 'Pending', row['check_in_time'] or '-', 
                row['method'] or '-', row['verification_status'] or '-'
            ])
        response = make_response(output.getvalue())
        filename = f"attendance_report_{selected_exam['subject_code']}_{selected_exam['exam_type']}.csv"
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        response.headers['Content-Type'] = 'text/csv'
        return response

    return render_template('admin/reports/attendance.html', data=data, exam=selected_exam)
