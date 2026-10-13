"""
Search Routes.

Provides role-enforced API endpoints for live global search across exams,
students, subjects, rooms, and incidents.
"""

from flask import Blueprint, request, jsonify, session
from app.database.search_queries import (
    search_admin_records,
    search_invigilator_records,
    search_student_records
)
from app.database.queries import get_student_by_user_id, get_invigilator_by_user_id

search_bp = Blueprint('search_bp', __name__)


@search_bp.route('/api/search')
def api_search():
    """
    Search endpoint that enforces role-based authorization.
    Returns categorized search results.
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized', 'results': []}), 401

    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({'results': [], 'query': query, 'total': 0})

    role = session.get('role', '').upper()
    user_id = session.get('user_id')
    results = []

    try:
        if role == 'ADMIN':
            results = search_admin_records(query)
        elif role == 'INVIGILATOR':
            invigilator = get_invigilator_by_user_id(user_id)
            if invigilator:
                results = search_invigilator_records(query, invigilator['invigilator_id'])
        elif role == 'STUDENT':
            student = get_student_by_user_id(user_id)
            if student:
                results = search_student_records(query, student['student_id'])
    except Exception as e:
        return jsonify({'error': 'Search failed', 'details': str(e), 'results': []}), 500

    return jsonify({
        'query': query,
        'role': role,
        'total': len(results),
        'results': results
    })


@search_bp.route('/api/health')
def api_health():
    """Diagnostic health endpoint for inspecting database connectivity."""
    from app.config import Config
    from app.database import get_db_connection
    health = {
        'status': 'unknown',
        'db_host': Config.DB_HOST,
        'db_port': Config.DB_PORT,
        'db_name': Config.DB_NAME,
        'db_user': Config.DB_USER,
        'ssl_required': Config.DB_SSL_REQUIRED,
        'ssl_ca_configured': bool(Config.DB_SSL_CA),
    }
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        health['status'] = 'healthy'
        health['database_connected'] = True
        return jsonify(health), 200
    except Exception as e:
        health['status'] = 'unhealthy'
        health['database_connected'] = False
        health['error'] = f"{type(e).__name__}: {str(e)}"
        return jsonify(health), 500

