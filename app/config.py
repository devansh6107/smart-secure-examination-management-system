"""
Application Configuration.

Reads environment variables from .env file and exposes them
as class attributes for Flask and database configuration.
"""

import os
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()


class Config:
    """Central configuration class."""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() in ('true', '1')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))

    # MySQL Database
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'exam_management_db')

    # Session
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
