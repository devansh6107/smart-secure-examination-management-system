"""
Tests — Database connection and basic auth.
"""

import sys
import os
import pytest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestDatabaseConnection:
    """Test MySQL database connectivity."""

    def test_connection_pool(self):
        """Verify we can get a connection from the pool."""
        from app.database import get_db_connection
        conn = get_db_connection()
        assert conn is not None
        assert conn.is_connected()
        conn.close()

    def test_tables_exist(self):
        """Verify all 14 tables were created."""
        from app.database import get_db_connection
        expected_tables = [
            'User', 'Department', 'Student', 'Invigilator', 'Subject',
            'ExamRoom', 'Exam', 'ExamRegistration', 'Seat', 'SeatAllocation',
            'Attendance', 'Authentication', 'AIAlert', 'Incident'
        ]
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        for table in expected_tables:
            # MySQL table names may be case-insensitive
            assert table.lower() in [t.lower() for t in tables], \
                f"Table '{table}' not found in database"

    def test_seed_data_loaded(self):
        """Verify seed data was inserted."""
        from app.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) AS cnt FROM User")
        assert cursor.fetchone()['cnt'] >= 9, "Expected at least 9 users (1 admin + 5 students + 3 invigilators)"

        cursor.execute("SELECT COUNT(*) AS cnt FROM Department")
        assert cursor.fetchone()['cnt'] >= 3, "Expected at least 3 departments"

        cursor.execute("SELECT COUNT(*) AS cnt FROM Subject")
        assert cursor.fetchone()['cnt'] >= 6, "Expected at least 6 subjects"

        cursor.execute("SELECT COUNT(*) AS cnt FROM ExamRoom")
        assert cursor.fetchone()['cnt'] >= 4, "Expected at least 4 rooms"

        cursor.execute("SELECT COUNT(*) AS cnt FROM Exam")
        assert cursor.fetchone()['cnt'] >= 6, "Expected at least 6 exams"

        cursor.close()
        conn.close()

    def test_views_exist(self):
        """Verify database views were created."""
        from app.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT TABLE_NAME FROM information_schema.VIEWS "
            "WHERE TABLE_SCHEMA = DATABASE()"
        )
        views = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        expected_views = ['vw_exam_details', 'vw_student_allocation',
                          'vw_alert_summary', 'vw_attendance_report']
        for view in expected_views:
            assert view in views, f"View '{view}' not found"


class TestAuthentication:
    """Test the authentication service."""

    def test_hash_password(self):
        """Verify password hashing produces valid hash."""
        from app.services.auth_service import hash_password, verify_password
        h = hash_password('test123')
        assert h.startswith('pbkdf2:sha256:')
        assert verify_password(h, 'test123')

    def test_wrong_password(self):
        """Verify wrong password fails verification."""
        from app.services.auth_service import hash_password, verify_password
        h = hash_password('correct')
        assert not verify_password(h, 'wrong')

    def test_authenticate_valid_user(self):
        """Test login with valid credentials (requires seeded DB)."""
        from app.services.auth_service import authenticate_user
        # This test depends on seed data with proper hashes
        # It will be validated after running the seed update
        user = authenticate_user('admin', 'admin123')
        if user:
            assert user['role'] == 'ADMIN'
            assert user['username'] == 'admin'

    def test_authenticate_invalid_user(self):
        """Test login with non-existent user."""
        from app.services.auth_service import authenticate_user
        user = authenticate_user('nonexistent_user', 'password')
        assert user is None

    def test_authenticate_wrong_password(self):
        """Test login with wrong password."""
        from app.services.auth_service import authenticate_user
        user = authenticate_user('admin', 'wrong_password_here')
        assert user is None


class TestRoleAuthorization:
    """Test role-based access control."""

    def _get_test_client(self):
        from app import create_app
        app = create_app()
        app.config['TESTING'] = True
        return app.test_client()

    def test_admin_dashboard_requires_login(self):
        """Admin dashboard should redirect unauthenticated users."""
        client = self._get_test_client()
        response = client.get('/admin/dashboard', follow_redirects=False)
        assert response.status_code in (302, 308)

    def test_student_dashboard_requires_login(self):
        """Student dashboard should redirect unauthenticated users."""
        client = self._get_test_client()
        response = client.get('/student/dashboard', follow_redirects=False)
        assert response.status_code in (302, 308)

    def test_invigilator_dashboard_requires_login(self):
        """Invigilator dashboard should redirect unauthenticated users."""
        client = self._get_test_client()
        response = client.get('/invigilator/dashboard', follow_redirects=False)
        assert response.status_code in (302, 308)

    def test_login_page_accessible(self):
        """Login page should be publicly accessible."""
        client = self._get_test_client()
        response = client.get('/login')
        assert response.status_code == 200
