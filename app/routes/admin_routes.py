"""
Admin Routes.

Dashboard and management pages for the ADMIN role.
"""

from functools import wraps
from flask import Blueprint, render_template, session, redirect, url_for, flash


admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator: restrict access to ADMIN role only."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'ADMIN':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard with aggregate statistics and charts."""
    from app.database.operational_queries import get_admin_dashboard_full
    try:
        stats = get_admin_dashboard_full()
    except Exception as e:
        flash(f'Error loading dashboard data: {e}', 'danger')
        stats = {}
    return render_template('admin/dashboard.html', stats=stats)
