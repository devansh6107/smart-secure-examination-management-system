from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.routes.admin_routes import admin_required
from app.database.admin_queries import get_all_subjects, create_subject, update_subject
from mysql.connector import Error

subjects_bp = Blueprint('admin_subjects', __name__, url_prefix='/admin/subjects')

@subjects_bp.route('/')
@admin_required
def index():
    subjects = get_all_subjects()
    return render_template('admin/subjects/index.html', subjects=subjects)

@subjects_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add():
    form_data = {}
    if request.method == 'POST':
        form_data = request.form
        code = request.form.get('subject_code', '').strip().upper()
        name = request.form.get('subject_name', '').strip()
        credits_raw = request.form.get('credits', '3')

        if not code or not name:
            flash('Please provide both Subject Code and Subject Name.', 'danger')
            return render_template('admin/subjects/form.html', subject=None, form_data=form_data)

        try:
            credits = int(credits_raw)
            create_subject(code, name, credits)
            flash(f"Subject '{code} - {name}' created successfully.", 'success')
            return redirect(url_for('admin_subjects.index'))
        except Error as e:
            if getattr(e, 'errno', None) == 1062 or 'Duplicate entry' in str(e):
                flash(f"A subject with code '{code}' already exists.", 'danger')
            else:
                flash('Unable to create subject due to a database constraint error.', 'danger')
            return render_template('admin/subjects/form.html', subject=None, form_data=form_data)
        except Exception:
            flash('An unexpected error occurred while creating the subject.', 'danger')
            return render_template('admin/subjects/form.html', subject=None, form_data=form_data)

    return render_template('admin/subjects/form.html', subject=None, form_data=None)

@subjects_bp.route('/<int:subject_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit(subject_id):
    subjects = get_all_subjects()
    subject = next((s for s in subjects if s['subject_id'] == subject_id), None)
    if not subject:
        flash('Subject record not found.', 'danger')
        return redirect(url_for('admin_subjects.index'))

    if request.method == 'POST':
        code = request.form.get('subject_code', '').strip().upper()
        name = request.form.get('subject_name', '').strip()
        credits_raw = request.form.get('credits', '3')

        if not code or not name:
            flash('Please provide both Subject Code and Subject Name.', 'danger')
            return render_template('admin/subjects/form.html', subject=subject, form_data=request.form)

        try:
            credits = int(credits_raw)
            update_subject(subject_id, code, name, credits)
            flash(f"Subject '{code} - {name}' updated successfully.", 'success')
            return redirect(url_for('admin_subjects.index'))
        except Error as e:
            if getattr(e, 'errno', None) == 1062 or 'Duplicate entry' in str(e):
                flash(f"Subject code '{code}' is already registered to another course.", 'danger')
            else:
                flash('Unable to update subject due to a database constraint error.', 'danger')
            return render_template('admin/subjects/form.html', subject=subject, form_data=request.form)
        except Exception:
            flash('An unexpected error occurred while updating the subject.', 'danger')
            return render_template('admin/subjects/form.html', subject=subject, form_data=request.form)

    return render_template('admin/subjects/form.html', subject=subject, form_data=None)
