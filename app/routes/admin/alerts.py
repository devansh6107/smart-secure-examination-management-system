"""
Admin AI Alert Management Routes.
"""
from flask import Blueprint, render_template, request
from app.routes.admin_routes import admin_required
from app.database.operational_queries import get_all_alerts
from app.database.admin_queries import get_all_exams

alerts_bp = Blueprint('admin_alerts', __name__, url_prefix='/admin/alerts')


@alerts_bp.route('/')
@admin_required
def index():
    """View all AI alerts with optional filters."""
    exam_filter = request.args.get('exam')
    type_filter = request.args.get('type')
    status_filter = request.args.get('status')

    alert_list = get_all_alerts(exam_filter, type_filter, status_filter)
    exams = get_all_exams()

    return render_template('admin/alerts/index.html',
                           alerts=alert_list, exams=exams,
                           current_exam=exam_filter,
                           current_type=type_filter,
                           current_status=status_filter)
