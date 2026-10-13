from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.routes.admin_routes import admin_required
from app.database.admin_queries import get_all_departments, create_department, update_department
from mysql.connector import Error

departments_bp = Blueprint('admin_departments', __name__, url_prefix='/admin/departments')

@departments_bp.route('/')
@admin_required
def index():
    departments = get_all_departments()
    return render_template('admin/departments/index.html', departments=departments)

@departments_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add():
    form_data = {}
    if request.method == 'POST':
        form_data = request.form
        name = request.form.get('department_name', '').strip()
        code = request.form.get('department_code', '').strip().upper()

        if not name or not code:
            flash('Please provide both Department Name and Department Code.', 'danger')
            return render_template('admin/departments/form.html', department=None, form_data=form_data)

        try:
            create_department(name, code)
            flash(f"Department '{name}' ({code}) created successfully.", 'success')
            return redirect(url_for('admin_departments.index'))
        except Error as e:
            if getattr(e, 'errno', None) == 1062 or 'Duplicate entry' in str(e):
                flash(f"A department with code '{code}' or name '{name}' already exists.", 'danger')
            else:
                flash('Unable to create department due to a database constraint error.', 'danger')
            return render_template('admin/departments/form.html', department=None, form_data=form_data)
        except Exception:
            flash('An unexpected error occurred while creating the department.', 'danger')
            return render_template('admin/departments/form.html', department=None, form_data=form_data)

    return render_template('admin/departments/form.html', department=None, form_data=None)

@departments_bp.route('/<int:dept_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit(dept_id):
    departments = get_all_departments()
    dept = next((d for d in departments if d['department_id'] == dept_id), None)
    if not dept:
        flash('Department record not found.', 'danger')
        return redirect(url_for('admin_departments.index'))

    if request.method == 'POST':
        name = request.form.get('department_name', '').strip()
        code = request.form.get('department_code', '').strip().upper()

        if not name or not code:
            flash('Please provide both Department Name and Department Code.', 'danger')
            return render_template('admin/departments/form.html', department=dept, form_data=request.form)

        try:
            update_department(dept_id, name, code)
            flash(f"Department '{name}' ({code}) updated successfully.", 'success')
            return redirect(url_for('admin_departments.index'))
        except Error as e:
            if getattr(e, 'errno', None) == 1062 or 'Duplicate entry' in str(e):
                flash(f"Department code '{code}' or name '{name}' is already registered.", 'danger')
            else:
                flash('Unable to update department due to a database constraint error.', 'danger')
            return render_template('admin/departments/form.html', department=dept, form_data=request.form)
        except Exception:
            flash('An unexpected error occurred while updating the department.', 'danger')
            return render_template('admin/departments/form.html', department=dept, form_data=request.form)

    return render_template('admin/departments/form.html', department=dept, form_data=None)
