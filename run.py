"""
Entry point for the Examination Management System.
Run with: python run.py
"""

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=app.config.get('FLASK_PORT', 5000),
        debug=app.config.get('FLASK_DEBUG', True)
    )
