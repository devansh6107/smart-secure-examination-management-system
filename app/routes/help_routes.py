"""
Help and FAQ Routes.

Provides user guides, expandable FAQ, system information, and support contacts.
Accessible to all user roles and unauthenticated visitors needing login assistance.
"""

from flask import Blueprint, render_template, session

help_bp = Blueprint('help_bp', __name__)


@help_bp.route('/help')
@help_bp.route('/faq')
def faq():
    """Renders the Expandable FAQ and Help Center page."""
    current_role = session.get('role', 'GUEST')
    return render_template('help/faq.html', current_role=current_role)
