from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.routes.admin_routes import admin_required
from app.database.admin_queries import create_student, update_student, get_all_departments, deactivate_user
from app.database.queries import get_all_students, create_user
from app.services.auth_service import hash_password
from mysql.connector import Error

students_bp = Blueprint('admin_students', __name__, url_prefix='/admin/students')

@students_bp.route('/')
@admin_required
def index():
    students = get_all_students()
    return render_template('admin/students/index.html', students=students)

@students_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add():
    departments = get_all_departments()
    form_data = {}
    if request.method == 'POST':
        form_data = request.form
        registration_no = request.form.get('registration_no', '').strip()
        name = request.form.get('name', '').strip()
        department_id_raw = request.form.get('department_id')
        year_raw = request.form.get('year', '1')
        section = request.form.get('section', '').strip().upper()
        phone = request.form.get('phone', '').strip()

        if not registration_no or not name or not department_id_raw or not section:
            flash('Please fill in all required fields.', 'danger')
            return render_template('admin/students/form.html', student=None, form_data=form_data, departments=departments)

        try:
            department_id = int(department_id_raw)
            year = int(year_raw)
        except ValueError:
            flash('Invalid numeric value for department or year.', 'danger')
            return render_template('admin/students/form.html', student=None, form_data=form_data, departments=departments)

        # Create User account automatically
        username = registration_no.lower()
        email = f"{username}@student.university.edu"
        password = request.form.get('password') or 'student123'

        try:
            user_id = create_user(username, email, hash_password(password), 'STUDENT')
            create_student(user_id, registration_no, name, department_id, year, section, phone)
            flash(f"Student '{name}' ({registration_no}) registered successfully.", 'success')
            return redirect(url_for('admin_students.index'))
        except Error as e:
            if getattr(e, 'errno', None) == 1062 or 'Duplicate entry' in str(e):
                flash(f"A student or user account with registration number '{registration_no}' already exists.", 'danger')
            else:
                flash('Unable to create student due to a database constraint violation.', 'danger')
            return render_template('admin/students/form.html', student=None, form_data=form_data, departments=departments)
        except Exception:
            flash('An unexpected error occurred while processing the student record.', 'danger')
            return render_template('admin/students/form.html', student=None, form_data=form_data, departments=departments)

    return render_template('admin/students/form.html', student=None, form_data=None, departments=departments)

@students_bp.route('/<int:student_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit(student_id):
    students = get_all_students()
    student = next((s for s in students if s['student_id'] == student_id), None)
    if not student:
        flash('Student record not found.', 'danger')
        return redirect(url_for('admin_students.index'))

    departments = get_all_departments()
    if request.method == 'POST':
        registration_no = request.form.get('registration_no', '').strip()
        name = request.form.get('name', '').strip()
        department_id_raw = request.form.get('department_id')
        year_raw = request.form.get('year', '1')
        section = request.form.get('section', '').strip().upper()
        phone = request.form.get('phone', '').strip()

        if not registration_no or not name or not department_id_raw or not section:
            flash('Please fill in all required fields.', 'danger')
            return render_template('admin/students/form.html', student=student, form_data=request.form, departments=departments)

        try:
            department_id = int(department_id_raw)
            year = int(year_raw)
            update_student(student_id, registration_no, name, department_id, year, section, phone)
            flash(f"Student '{name}' ({registration_no}) updated successfully.", 'success')
            return redirect(url_for('admin_students.index'))
        except Error as e:
            if getattr(e, 'errno', None) == 1062 or 'Duplicate entry' in str(e):
                flash(f"Registration number '{registration_no}' is already registered to another student.", 'danger')
            else:
                flash('Unable to update student due to a database constraint error.', 'danger')
            return render_template('admin/students/form.html', student=student, form_data=request.form, departments=departments)
        except Exception:
            flash('An unexpected error occurred while updating the student record.', 'danger')
            return render_template('admin/students/form.html', student=student, form_data=request.form, departments=departments)

    return render_template('admin/students/form.html', student=student, form_data=None, departments=departments)

@students_bp.route('/<int:user_id>/toggle_status', methods=['POST'])
@admin_required
def toggle_status(user_id):
    is_active = request.form.get('is_active') == '1'
    try:
        deactivate_user(user_id, not is_active)
        flash(f"Student account {'deactivated' if is_active else 'activated'}.", 'success')
    except Error as e:
        flash(f'Database error: {e}', 'danger')
    return redirect(url_for('admin_students.index'))
