from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.routes.admin_routes import admin_required
from app.database.admin_queries import get_all_invigilators, create_invigilator, update_invigilator, deactivate_user
from app.database.queries import create_user
from app.services.auth_service import hash_password
from mysql.connector import Error

invigilators_bp = Blueprint('admin_invigilators', __name__, url_prefix='/admin/invigilators')

@invigilators_bp.route('/')
@admin_required
def index():
    invigilators = get_all_invigilators()
    return render_template('admin/invigilators/index.html', invigilators=invigilators)

@invigilators_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add():
    form_data = {}
    if request.method == 'POST':
        form_data = request.form
        employee_id = request.form.get('employee_id', '').strip().upper()
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        designation = request.form.get('designation', '').strip()

        if not employee_id or not name or not designation:
            flash('Please fill in all required fields.', 'danger')
            return render_template('admin/invigilators/form.html', invigilator=None, form_data=form_data)

        # Create User account automatically
        username = employee_id.lower()
        email = f"{username}@faculty.university.edu"
        password = request.form.get('password') or 'invig123'

        try:
            user_id = create_user(username, email, hash_password(password), 'INVIGILATOR')
            create_invigilator(user_id, employee_id, name, phone, designation)
            flash(f"Invigilator '{name}' ({employee_id}) onboarded successfully.", 'success')
            return redirect(url_for('admin_invigilators.index'))
        except Error as e:
            if getattr(e, 'errno', None) == 1062 or 'Duplicate entry' in str(e):
                flash(f"An invigilator or user account with Employee ID '{employee_id}' already exists.", 'danger')
            else:
                flash('Unable to create invigilator profile due to a database constraint error.', 'danger')
            return render_template('admin/invigilators/form.html', invigilator=None, form_data=form_data)
        except Exception:
            flash('An unexpected error occurred while processing the invigilator profile.', 'danger')
            return render_template('admin/invigilators/form.html', invigilator=None, form_data=form_data)

    return render_template('admin/invigilators/form.html', invigilator=None, form_data=None)

@invigilators_bp.route('/<int:invigilator_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit(invigilator_id):
    invigilators = get_all_invigilators()
    invigilator = next((i for i in invigilators if i['invigilator_id'] == invigilator_id), None)
    if not invigilator:
        flash('Invigilator profile not found.', 'danger')
        return redirect(url_for('admin_invigilators.index'))

    if request.method == 'POST':
        employee_id = request.form.get('employee_id', '').strip().upper()
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        designation = request.form.get('designation', '').strip()

        if not employee_id or not name or not designation:
            flash('Please fill in all required fields.', 'danger')
            return render_template('admin/invigilators/form.html', invigilator=invigilator, form_data=request.form)

        try:
            update_invigilator(invigilator_id, employee_id, name, phone, designation)
            flash(f"Invigilator '{name}' ({employee_id}) updated successfully.", 'success')
            return redirect(url_for('admin_invigilators.index'))
        except Error as e:
            if getattr(e, 'errno', None) == 1062 or 'Duplicate entry' in str(e):
                flash(f"Employee ID '{employee_id}' is already registered to another faculty member.", 'danger')
            else:
                flash('Unable to update invigilator profile due to a database constraint error.', 'danger')
            return render_template('admin/invigilators/form.html', invigilator=invigilator, form_data=request.form)
        except Exception:
            flash('An unexpected error occurred while updating the invigilator profile.', 'danger')
            return render_template('admin/invigilators/form.html', invigilator=invigilator, form_data=request.form)

    return render_template('admin/invigilators/form.html', invigilator=invigilator, form_data=None)

@invigilators_bp.route('/<int:user_id>/toggle_status', methods=['POST'])
@admin_required
def toggle_status(user_id):
    is_active = request.form.get('is_active') == '1'
    try:
        deactivate_user(user_id, not is_active)
        flash(f"Invigilator account {'deactivated' if is_active else 'activated'}.", 'success')
    except Error as e:
        flash(f'Database error: {e}', 'danger')
    return redirect(url_for('admin_invigilators.index'))
