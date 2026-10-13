"""
Flask Application Factory.

Creates and configures the Flask application instance,
registers all blueprints, and sets up session management.
"""

from flask import Flask
from app.config import Config


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Load configuration from Config class
    app.config.from_object(Config)
    app.secret_key = Config.SECRET_KEY

    # ── Register Blueprints ──
    from app.routes.auth_routes import auth_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.student_routes import student_bp
    from app.routes.invigilator_routes import invigilator_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # ── Register Admin Sub-Modules ──
    from app.routes.admin.departments import departments_bp
    from app.routes.admin.subjects import subjects_bp
    from app.routes.admin.rooms import rooms_bp
    from app.routes.admin.invigilators import invigilators_bp
    from app.routes.admin.students import students_bp
    from app.routes.admin.exams import exams_bp
    from app.routes.admin.registrations import registrations_bp
    from app.routes.admin.alerts import alerts_bp
    from app.routes.admin.incidents import incidents_bp
    from app.routes.admin.reports import reports_bp
    
    app.register_blueprint(departments_bp)
    app.register_blueprint(subjects_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(invigilators_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(exams_bp)
    app.register_blueprint(registrations_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(incidents_bp)
    app.register_blueprint(reports_bp)

    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(invigilator_bp, url_prefix='/invigilator')

    # ── Register Search & Help Blueprints ──
    from app.routes.search_routes import search_bp
    from app.routes.help_routes import help_bp

    app.register_blueprint(search_bp)
    app.register_blueprint(help_bp)

    # ── UTM Attribution & Security Hooks ──
    from app.services.utm_service import capture_utm_parameters

    @app.before_request
    def handle_utm_attribution():
        capture_utm_parameters()

    # ── Application Metadata Context Processor ──
    @app.context_processor
    def inject_app_metadata():
        return {
            'APP_VERSION': '2.4.0',
            'APP_LAST_UPDATED': 'October 13, 2026',
            'utm_data': app.config.get('utm_data')
        }

    return app
