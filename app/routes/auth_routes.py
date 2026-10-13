"""
Authentication Routes.

Handles login, logout, and the landing page.
Uses Flask sessions for authentication state.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.services.auth_service import authenticate_user

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    """Landing page — redirect to dashboard if logged in, else login."""
    if 'user_id' in session:
        return _redirect_to_dashboard(session['role'])
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with form handling."""
    if 'user_id' in session:
        return _redirect_to_dashboard(session['role'])

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # Validate input
        if not username or not password:
            flash('Please enter both username and password.', 'warning')
            return render_template('auth/login.html')

        try:
            user = authenticate_user(username, password)
        except Exception as e:
            flash('Database connection error. Please try again.', 'danger')
            return render_template('auth/login.html')

        if user is None:
            flash('Invalid username or password.', 'danger')
            return render_template('auth/login.html')

        # Set session data
        session['user_id'] = user['user_id']
        session['username'] = user['username']
        session['role'] = user['role']
        session['email'] = user['email']
        session.permanent = True

        flash(f'Welcome back, {user["username"]}!', 'success')
        return _redirect_to_dashboard(user['role'])

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    """Clear session and redirect to login."""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


def _redirect_to_dashboard(role):
    """Redirect user to their role-specific dashboard."""
    if role == 'ADMIN':
        return redirect(url_for('admin.dashboard'))
    elif role == 'STUDENT':
        return redirect(url_for('student.dashboard'))
    elif role == 'INVIGILATOR':
        return redirect(url_for('invigilator.dashboard'))
    return redirect(url_for('auth.login'))
