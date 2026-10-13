"""
Admin Incident Management Routes.
"""
from flask import Blueprint, render_template
from app.routes.admin_routes import admin_required
from app.database.operational_queries import get_all_incidents

incidents_bp = Blueprint('admin_incidents', __name__, url_prefix='/admin/incidents')


@incidents_bp.route('/')
@admin_required
def index():
    """View all incident reports."""
    incident_list = get_all_incidents()
    return render_template('admin/incidents/index.html', incidents=incident_list)
