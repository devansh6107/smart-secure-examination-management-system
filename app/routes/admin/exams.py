from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.routes.admin_routes import admin_required
from app.database.admin_queries import (
    get_all_exams, create_exam, update_exam, cancel_exam,
    get_all_subjects, get_all_rooms, get_all_invigilators
)
from mysql.connector import Error

exams_bp = Blueprint('admin_exams', __name__, url_prefix='/admin/exams')

@exams_bp.route('/')
@admin_required
def index():
    exams = get_all_exams()
    return render_template('admin/exams/index.html', exams=exams)

@exams_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add():
    subjects = get_all_subjects()
    rooms = get_all_rooms()
    invigilators = get_all_invigilators()
    form_data = {}
    
    if request.method == 'POST':
        form_data = request.form
        subject_id_raw = request.form.get('subject_id')
        room_id_raw = request.form.get('room_id')
        invigilator_id_raw = request.form.get('invigilator_id')
        exam_date = request.form.get('exam_date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        semester = request.form.get('semester', 'Fall')
        academic_year_raw = request.form.get('academic_year', '2026')
        exam_type = request.form.get('exam_type')
        status = request.form.get('status', 'Scheduled')
        
        if not subject_id_raw or not room_id_raw or not invigilator_id_raw or not exam_date or not start_time or not end_time or not exam_type:
            flash('Please fill in all required fields.', 'danger')
            return render_template('admin/exams/form.html', exam=None, form_data=form_data, subjects=subjects, rooms=rooms, invigilators=invigilators)

        if end_time <= start_time:
            flash('Invalid exam schedule: End time must be strictly after start time.', 'danger')
            return render_template('admin/exams/form.html', exam=None, form_data=form_data, subjects=subjects, rooms=rooms, invigilators=invigilators)

        try:
            subject_id = int(subject_id_raw)
            room_id = int(room_id_raw)
            invigilator_id = int(invigilator_id_raw)
            academic_year = int(academic_year_raw)
            create_exam(subject_id, room_id, invigilator_id, exam_date, start_time, end_time, semester, academic_year, exam_type, status)
            flash(f"Exam for subject ID {subject_id} ({exam_type}) scheduled successfully.", 'success')
            return redirect(url_for('admin_exams.index'))
        except Error as e:
            if getattr(e, 'errno', None) == 1062 or 'Duplicate entry' in str(e):
                flash('An exam conflict occurred: This room or schedule is already booked.', 'danger')
            else:
                flash('Unable to schedule exam due to a database constraint error.', 'danger')
            return render_template('admin/exams/form.html', exam=None, form_data=form_data, subjects=subjects, rooms=rooms, invigilators=invigilators)
        except Exception:
            flash('An unexpected error occurred while scheduling the examination.', 'danger')
            return render_template('admin/exams/form.html', exam=None, form_data=form_data, subjects=subjects, rooms=rooms, invigilators=invigilators)
                
    return render_template('admin/exams/form.html', exam=None, form_data=None, subjects=subjects, rooms=rooms, invigilators=invigilators)

@exams_bp.route('/<int:exam_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit(exam_id):
    exams = get_all_exams()
    exam = next((e for e in exams if e['exam_id'] == exam_id), None)
    if not exam:
        flash('Exam record not found.', 'danger')
        return redirect(url_for('admin_exams.index'))

    subjects = get_all_subjects()
    rooms = get_all_rooms()
    invigilators = get_all_invigilators()
    
    if request.method == 'POST':
        subject_id_raw = request.form.get('subject_id')
        room_id_raw = request.form.get('room_id')
        invigilator_id_raw = request.form.get('invigilator_id')
        exam_date = request.form.get('exam_date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        semester = request.form.get('semester')
        academic_year_raw = request.form.get('academic_year')
        exam_type = request.form.get('exam_type')
        status = request.form.get('status')
        
        if not subject_id_raw or not room_id_raw or not invigilator_id_raw or not exam_date or not start_time or not end_time or not exam_type:
            flash('Please fill in all required fields.', 'danger')
            return render_template('admin/exams/form.html', exam=exam, form_data=request.form, subjects=subjects, rooms=rooms, invigilators=invigilators)

        if end_time <= start_time:
            flash('Invalid exam schedule: End time must be strictly after start time.', 'danger')
            return render_template('admin/exams/form.html', exam=exam, form_data=request.form, subjects=subjects, rooms=rooms, invigilators=invigilators)

        try:
            subject_id = int(subject_id_raw)
            room_id = int(room_id_raw)
            invigilator_id = int(invigilator_id_raw)
            academic_year = int(academic_year_raw)
            update_exam(exam_id, subject_id, room_id, invigilator_id, exam_date, start_time, end_time, semester, academic_year, exam_type, status)
            flash(f"Exam #{exam_id} updated successfully.", 'success')
            return redirect(url_for('admin_exams.index'))
        except Error as e:
            if getattr(e, 'errno', None) == 1062 or 'Duplicate entry' in str(e):
                flash('An exam conflict occurred: Room or invigilator conflict detected.', 'danger')
            else:
                flash('Unable to update exam due to a database constraint error.', 'danger')
            return render_template('admin/exams/form.html', exam=exam, form_data=request.form, subjects=subjects, rooms=rooms, invigilators=invigilators)
        except Exception:
            flash('An unexpected error occurred while updating the examination.', 'danger')
            return render_template('admin/exams/form.html', exam=exam, form_data=request.form, subjects=subjects, rooms=rooms, invigilators=invigilators)
                
    return render_template('admin/exams/form.html', exam=exam, form_data=None, subjects=subjects, rooms=rooms, invigilators=invigilators)

@exams_bp.route('/<int:exam_id>/cancel', methods=['POST'])
@admin_required
def cancel(exam_id):
    try:
        cancel_exam(exam_id)
        flash('Exam cancelled successfully.', 'success')
    except Error as e:
        flash(f'Database error: {e}', 'danger')
    return redirect(url_for('admin_exams.index'))

@exams_bp.route('/<int:exam_id>/allocate', methods=['POST'])
@admin_required
def allocate_seats(exam_id):
    from app.database.operational_queries import allocate_seats_for_exam
    try:
        count = allocate_seats_for_exam(exam_id)
        if count == 0:
            flash('No new students to allocate.', 'info')
        else:
            flash(f'Successfully allocated seats for {count} students.', 'success')
    except Exception as e:
        flash(f'Allocation failed: {str(e)}', 'danger')
    return redirect(url_for('admin_exams.seating_chart', exam_id=exam_id))

@exams_bp.route('/<int:exam_id>/seating')
@admin_required
def seating_chart(exam_id):
    from app.database.operational_queries import get_seating_chart
    exams = get_all_exams()
    exam = next((e for e in exams if e['exam_id'] == exam_id), None)
    if not exam:
        flash('Exam not found.', 'danger')
        return redirect(url_for('admin_exams.index'))
        
    chart_data = get_seating_chart(exam_id)
    configured_seats = len(chart_data)
    allocated_count = sum(1 for s in chart_data if s.get('allocation_status') in ('Allocated', 'Reallocated'))
    registered_count = exam.get('registered_students', 0)
    unassigned_count = max(0, registered_count - allocated_count)
    available_seats = max(0, configured_seats - allocated_count)
    num_columns = max((s.get('column_no', 1) for s in chart_data), default=1) if chart_data else 1
    
    return render_template(
        'admin/exams/seating_chart.html',
        exam=exam,
        chart_data=chart_data,
        configured_seats=configured_seats,
        allocated_count=allocated_count,
        registered_count=registered_count,
        unassigned_count=unassigned_count,
        available_seats=available_seats,
        num_columns=num_columns
    )

@exams_bp.route('/<int:exam_id>/cancel_allocation/<int:allocation_id>', methods=['POST'])
@admin_required
def cancel_allocation(exam_id, allocation_id):
    from app.database.operational_queries import cancel_seat_allocation
    try:
        cancel_seat_allocation(allocation_id)
        flash('Seat allocation cancelled.', 'warning')
    except Exception as e:
        flash(f'Error cancelling allocation: {str(e)}', 'danger')
    return redirect(url_for('admin_exams.seating_chart', exam_id=exam_id))
