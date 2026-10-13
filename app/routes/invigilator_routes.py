"""
Invigilator Routes.

Dashboard and proctoring pages for the INVIGILATOR role.
"""

from functools import wraps
from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from app.database.queries import get_invigilator_by_user_id

invigilator_bp = Blueprint('invigilator', __name__, url_prefix='/invigilator')


def invigilator_required(f):
    """Decorator: restrict access to INVIGILATOR role only."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'INVIGILATOR':
            flash('Access denied. Invigilator account required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def _get_invigilator():
    """Helper to get the current invigilator profile."""
    return get_invigilator_by_user_id(session['user_id'])


# ══════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════

@invigilator_bp.route('/dashboard')
@invigilator_required
def dashboard():
    """Invigilator dashboard with assigned exams, alerts, incidents."""
    from app.database.operational_queries import get_invigilator_dashboard_full, get_invigilator_exams
    try:
        invigilator = _get_invigilator()
        if not invigilator:
            flash('Invigilator profile not found.', 'danger')
            return redirect(url_for('auth.login'))

        stats = get_invigilator_dashboard_full(invigilator['invigilator_id'])
        exams = get_invigilator_exams(invigilator['invigilator_id'])
    except Exception as e:
        flash(f'Error loading dashboard data: {e}', 'danger')
        invigilator = {}
        stats = {}
        exams = []
    return render_template('invigilator/dashboard.html',
                           invigilator=invigilator, stats=stats, exams=exams)


# ══════════════════════════════════════════════
#  EXAM SHEET (Stage 3)
# ══════════════════════════════════════════════

@invigilator_bp.route('/exam/<int:exam_id>')
@invigilator_required
def exam_sheet(exam_id):
    """View exam attendance and verification sheet."""
    from app.database.operational_queries import get_exam_attendance_sheet, get_invigilator_exams
    try:
        invigilator = _get_invigilator()
        exams = get_invigilator_exams(invigilator['invigilator_id'])
        exam = next((e for e in exams if e['exam_id'] == exam_id), None)

        if not exam:
            flash('Exam not found or you are not assigned to it.', 'danger')
            return redirect(url_for('invigilator.dashboard'))

        allocations = get_exam_attendance_sheet(exam_id)
        return render_template('invigilator/exam_sheet.html', exam=exam, allocations=allocations)
    except Exception as e:
        flash(f'Error loading exam sheet: {e}', 'danger')
        return redirect(url_for('invigilator.dashboard'))


@invigilator_bp.route('/attendance/<int:exam_id>/<int:allocation_id>', methods=['POST'])
@invigilator_required
def mark_attendance_route(exam_id, allocation_id):
    """Mark attendance."""
    from app.database.operational_queries import mark_attendance
    try:
        status = request.form.get('status')
        invigilator = _get_invigilator()
        mark_attendance(allocation_id, status, invigilator['invigilator_id'])
        flash(f'Attendance marked as {status}.', 'success')
    except Exception as e:
        flash(f'Error marking attendance: {e}', 'danger')
    return redirect(url_for('invigilator.exam_sheet', exam_id=exam_id))


@invigilator_bp.route('/authenticate/<int:exam_id>/<int:allocation_id>', methods=['POST'])
@invigilator_required
def verify_identity(exam_id, allocation_id):
    """Simulate identity verification."""
    from app.database.operational_queries import record_authentication_attempt
    try:
        method = request.form.get('method')
        success = int(request.form.get('success', 0))
        record_authentication_attempt(allocation_id, method, success)

        status_text = 'Success' if success else 'Failed'
        flash_color = 'success' if success else 'danger'
        flash(f'{method} Authentication {status_text}.', flash_color)
    except Exception as e:
        flash(f'Error simulating authentication: {e}', 'danger')
    return redirect(url_for('invigilator.exam_sheet', exam_id=exam_id))


# ══════════════════════════════════════════════
#  AI ALERTS (Stage 4)
# ══════════════════════════════════════════════

@invigilator_bp.route('/alerts')
@invigilator_required
def alerts():
    """View AI alerts for assigned exams."""
    from app.database.operational_queries import get_alerts_for_invigilator, get_invigilator_exams
    try:
        invigilator = _get_invigilator()
        status_filter = request.args.get('status')
        alert_list = get_alerts_for_invigilator(invigilator['invigilator_id'], status_filter)
        exams = get_invigilator_exams(invigilator['invigilator_id'])
        return render_template('invigilator/alerts.html',
                               invigilator=invigilator, alerts=alert_list, exams=exams,
                               current_status=status_filter)
    except Exception as e:
        flash(f'Error loading alerts: {e}', 'danger')
        return redirect(url_for('invigilator.dashboard'))


@invigilator_bp.route('/alerts/<int:alert_id>/review', methods=['POST'])
@invigilator_required
def review_alert_route(alert_id):
    """Mark alert as Reviewed."""
    from app.database.operational_queries import review_alert
    try:
        review_alert(alert_id)
        flash('Alert marked as Reviewed.', 'success')
    except Exception as e:
        flash(f'Error reviewing alert: {e}', 'danger')
    return redirect(url_for('invigilator.alerts'))


@invigilator_bp.route('/alerts/<int:alert_id>/ignore', methods=['POST'])
@invigilator_required
def ignore_alert_route(alert_id):
    """Mark alert as Ignored."""
    from app.database.operational_queries import ignore_alert
    try:
        ignore_alert(alert_id)
        flash('Alert marked as Ignored.', 'info')
    except Exception as e:
        flash(f'Error ignoring alert: {e}', 'danger')
    return redirect(url_for('invigilator.alerts'))


@invigilator_bp.route('/simulate/<int:exam_id>', methods=['POST'])
@invigilator_required
def simulate_proctoring(exam_id):
    """Trigger AI simulation for demo/testing."""
    from app.services.proctoring_service import ProctoringService
    try:
        count = int(request.form.get('count', 3))
        count = max(1, min(count, 10))  # Clamp between 1 and 10
        alert_ids = ProctoringService.simulate_batch(exam_id, count)
        flash(f'AI Simulation complete: {len(alert_ids)} alerts generated.', 'warning')
    except Exception as e:
        flash(f'Simulation failed: {e}', 'danger')
    return redirect(url_for('invigilator.alerts'))


# ══════════════════════════════════════════════
#  INCIDENTS (Stage 4)
# ══════════════════════════════════════════════

@invigilator_bp.route('/incidents')
@invigilator_required
def incidents():
    """View incidents created by this invigilator."""
    from app.database.operational_queries import get_incidents_for_invigilator, get_invigilator_exams, get_exam_attendance_sheet
    try:
        invigilator = _get_invigilator()
        incident_list = get_incidents_for_invigilator(invigilator['invigilator_id'])
        exams = get_invigilator_exams(invigilator['invigilator_id'])

        # Build allocation choices for the "Create Incident" modal
        all_allocations = []
        for exam in exams:
            allocs = get_exam_attendance_sheet(exam['exam_id'])
            for a in allocs:
                a['exam_label'] = f"{exam['subject_code']} {exam['exam_type']}"
            all_allocations.extend(allocs)

        return render_template('invigilator/incidents.html',
                               invigilator=invigilator, incidents=incident_list,
                               allocations=all_allocations)
    except Exception as e:
        flash(f'Error loading incidents: {e}', 'danger')
        return redirect(url_for('invigilator.dashboard'))


@invigilator_bp.route('/incidents/create', methods=['POST'])
@invigilator_required
def create_incident_route():
    """Create a new incident report."""
    from app.database.operational_queries import create_incident
    try:
        invigilator = _get_invigilator()
        allocation_id = int(request.form.get('allocation_id'))
        incident_type = request.form.get('incident_type')
        description = request.form.get('description', '')
        action_taken = request.form.get('action_taken', '')

        if not incident_type:
            flash('Incident type is required.', 'danger')
            return redirect(url_for('invigilator.incidents'))

        create_incident(allocation_id, invigilator['invigilator_id'],
                        incident_type, description, action_taken)
        flash('Incident report filed successfully.', 'success')
    except Exception as e:
        flash(f'Error creating incident: {e}', 'danger')
    return redirect(url_for('invigilator.incidents'))
