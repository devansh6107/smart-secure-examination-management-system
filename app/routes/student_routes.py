"""
Student Routes.

Dashboard and exam viewing pages for the STUDENT role.
"""

from functools import wraps
from flask import Blueprint, render_template, session, redirect, url_for, flash
from app.database.queries import get_student_by_user_id, get_student_dashboard_data

student_bp = Blueprint('student', __name__, url_prefix='/student')


def student_required(f):
    """Decorator: restrict access to STUDENT role only."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'STUDENT':
            flash('Access denied. Student account required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@student_bp.route('/dashboard')
@student_required
def dashboard():
    """Student dashboard with upcoming exams, seat info, attendance."""
    from app.database.operational_queries import get_student_hall_tickets
    try:
        student = get_student_by_user_id(session['user_id'])
        if not student:
            flash('Student profile not found.', 'danger')
            return redirect(url_for('auth.login'))

        tickets = get_student_hall_tickets(student['student_id'])
    except Exception as e:
        flash(f'Error loading dashboard data: {e}', 'danger')
        student = {}
        tickets = []
    return render_template('student/dashboard.html', student=student, tickets=tickets)

@student_bp.route('/hall_ticket/<int:exam_id>')
@student_required
def hall_ticket(exam_id):
    """View and print individual hall ticket."""
    from app.database.operational_queries import get_student_hall_tickets
    try:
        student = get_student_by_user_id(session['user_id'])
        tickets = get_student_hall_tickets(student['student_id'])
        ticket = next((t for t in tickets if t['exam_id'] == exam_id), None)
        if not ticket:
            flash('Hall ticket not found or you are not registered for this exam.', 'danger')
            return redirect(url_for('student.dashboard'))
            
        return render_template('student/hall_ticket.html', student=student, ticket=ticket)
    except Exception as e:
        flash(f'Error loading hall ticket: {e}', 'danger')
        return redirect(url_for('student.dashboard'))
