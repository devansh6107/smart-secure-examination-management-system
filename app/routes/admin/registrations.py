from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.routes.admin_routes import admin_required
from app.database.admin_queries import get_exam_registrations, register_student_for_exam, cancel_registration, get_all_exams
from app.database.queries import get_all_students
from mysql.connector import Error

registrations_bp = Blueprint('admin_registrations', __name__, url_prefix='/admin/exams/<int:exam_id>/registrations')

@registrations_bp.route('/')
@admin_required
def index(exam_id):
    exams = get_all_exams()
    exam = next((e for e in exams if e['exam_id'] == exam_id), None)
    if not exam:
        flash('Exam not found.', 'danger')
        return redirect(url_for('admin_exams.index'))

    registrations = get_exam_registrations(exam_id)
    students = get_all_students()
    
    return render_template('admin/registrations/index.html', exam=exam, registrations=registrations, students=students)

@registrations_bp.route('/add', methods=['POST'])
@admin_required
def add(exam_id):
    student_id = int(request.form.get('student_id'))
    try:
        register_student_for_exam(student_id, exam_id)
        flash('Student registered for exam successfully.', 'success')
    except Error as e:
        # Check for duplicate entry error (1062)
        if e.errno == 1062:
            flash('Error: Student is already registered for this exam.', 'danger')
        else:
            flash(f'Database error: {e}', 'danger')
            
    return redirect(url_for('admin_registrations.index', exam_id=exam_id))

@registrations_bp.route('/<int:registration_id>/cancel', methods=['POST'])
@admin_required
def cancel(exam_id, registration_id):
    try:
        cancel_registration(registration_id)
        flash('Registration cancelled successfully.', 'success')
    except Error as e:
        flash(f'Database error: {e}', 'danger')
        
    return redirect(url_for('admin_registrations.index', exam_id=exam_id))
