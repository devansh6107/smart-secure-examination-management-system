"""
Stage 4 Tests — AI Proctoring, Alert Management, Incidents, Dashboard Queries.

Tests:
    1. AI alert generation via ProctoringService
    2. Alert review + ignore status transitions
    3. Incident creation
    4. Dashboard stat queries return expected keys
    5. Role restriction (student cannot access invigilator routes)
"""

import sys
import os
import unittest

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestProctoringService(unittest.TestCase):
    """Tests for the ProctoringService and alert lifecycle."""

    def test_simulate_single_alert(self):
        """ProctoringService.simulate_alert creates a valid AIAlert record."""
        from app.services.proctoring_service import ProctoringService
        from app.database import get_db_connection

        # We need an allocation_id that exists. Use seed data or create one.
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT allocation_id FROM SeatAllocation LIMIT 1")
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            self.skipTest("No seat allocations in database. Run Stage 3 first.")

        alloc_id = row['allocation_id']

        # Generate an alert
        alert_id = ProctoringService.simulate_alert(alloc_id, 'Phone Detected', confidence=0.85)
        self.assertIsNotNone(alert_id)
        self.assertIsInstance(alert_id, int)

        # Verify the record exists
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM AIAlert WHERE alert_id = %s", (alert_id,))
        alert = cursor.fetchone()
        cursor.close()
        conn.close()

        self.assertIsNotNone(alert)
        self.assertEqual(alert['alert_type'], 'Phone Detected')
        self.assertEqual(float(alert['confidence']), 0.85)
        self.assertEqual(alert['status'], 'Pending')

    def test_simulate_invalid_alert_type(self):
        """ProctoringService.simulate_alert rejects invalid alert types."""
        from app.services.proctoring_service import ProctoringService

        with self.assertRaises(ValueError):
            ProctoringService.simulate_alert(1, 'Invalid Type')

    def test_simulate_batch(self):
        """ProctoringService.simulate_batch generates multiple alerts."""
        from app.services.proctoring_service import ProctoringService
        from app.database import get_db_connection

        # Find an exam with allocations
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT DISTINCT exam_id FROM SeatAllocation
            WHERE allocation_status = 'Allocated' LIMIT 1
        ''')
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            self.skipTest("No seat allocations available.")

        exam_id = row['exam_id']
        alert_ids = ProctoringService.simulate_batch(exam_id, count=2)
        self.assertEqual(len(alert_ids), 2)
        for aid in alert_ids:
            self.assertIsInstance(aid, int)


class TestAlertManagement(unittest.TestCase):
    """Tests for alert review and ignore lifecycle."""

    def test_review_alert(self):
        """review_alert changes status to Reviewed."""
        from app.services.proctoring_service import ProctoringService
        from app.database.operational_queries import review_alert
        from app.database import get_db_connection

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT allocation_id FROM SeatAllocation LIMIT 1")
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            self.skipTest("No allocations.")

        alert_id = ProctoringService.simulate_alert(row['allocation_id'], 'Suspicious Movement')
        review_alert(alert_id)

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT status FROM AIAlert WHERE alert_id = %s", (alert_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        self.assertEqual(result['status'], 'Reviewed')

    def test_ignore_alert(self):
        """ignore_alert changes status to Ignored."""
        from app.services.proctoring_service import ProctoringService
        from app.database.operational_queries import ignore_alert
        from app.database import get_db_connection

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT allocation_id FROM SeatAllocation LIMIT 1")
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            self.skipTest("No allocations.")

        alert_id = ProctoringService.simulate_alert(row['allocation_id'], 'Suspicious Movement')
        ignore_alert(alert_id)

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT status FROM AIAlert WHERE alert_id = %s", (alert_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        self.assertEqual(result['status'], 'Ignored')


class TestIncidentManagement(unittest.TestCase):
    """Tests for incident creation."""

    def test_create_incident(self):
        """create_incident inserts a valid Incident record."""
        from app.database.operational_queries import create_incident
        from app.database import get_db_connection

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT allocation_id FROM SeatAllocation LIMIT 1")
        alloc = cursor.fetchone()
        cursor.execute("SELECT invigilator_id FROM Invigilator LIMIT 1")
        inv = cursor.fetchone()
        cursor.close()
        conn.close()

        if not alloc or not inv:
            self.skipTest("No allocations or invigilators.")

        inc_id = create_incident(
            alloc['allocation_id'],
            inv['invigilator_id'],
            'Phone Usage',
            'Student was using phone during exam.',
            'Warning issued.'
        )
        self.assertIsNotNone(inc_id)

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Incident WHERE incident_id = %s", (inc_id,))
        incident = cursor.fetchone()
        cursor.close()
        conn.close()

        self.assertEqual(incident['incident_type'], 'Phone Usage')
        self.assertEqual(incident['description'], 'Student was using phone during exam.')


class TestDashboardQueries(unittest.TestCase):
    """Tests for enhanced dashboard stat queries."""

    def test_admin_dashboard_full(self):
        """get_admin_dashboard_full returns expected keys."""
        from app.database.operational_queries import get_admin_dashboard_full

        stats = get_admin_dashboard_full()
        expected_keys = [
            'total_students', 'active_exams', 'total_rooms',
            'pending_alerts', 'total_incidents',
            'attendance', 'attendance_pct',
            'attendance_by_exam', 'alerts_by_type'
        ]
        for key in expected_keys:
            self.assertIn(key, stats, f"Missing key: {key}")

        self.assertIsInstance(stats['attendance_pct'], (int, float))

    def test_invigilator_dashboard_full(self):
        """get_invigilator_dashboard_full returns expected keys."""
        from app.database.operational_queries import get_invigilator_dashboard_full
        from app.database import get_db_connection

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT invigilator_id FROM Invigilator LIMIT 1")
        inv = cursor.fetchone()
        cursor.close()
        conn.close()

        if not inv:
            self.skipTest("No invigilators.")

        stats = get_invigilator_dashboard_full(inv['invigilator_id'])
        expected_keys = ['assigned_exams', 'today_exams', 'pending_alerts', 'total_incidents']
        for key in expected_keys:
            self.assertIn(key, stats, f"Missing key: {key}")


class TestRoleRestrictions(unittest.TestCase):
    """Test that role-based access control is enforced."""

    def test_student_cannot_access_invigilator_dashboard(self):
        """Student role should be redirected away from invigilator pages."""
        from app import create_app

        app = create_app()
        app.config['TESTING'] = True

        with app.test_client() as client:
            # Simulate a student session
            with client.session_transaction() as sess:
                sess['user_id'] = 1
                sess['username'] = 'student_test'
                sess['role'] = 'STUDENT'

            response = client.get('/invigilator/dashboard', follow_redirects=False)
            # Should redirect (302) since role is STUDENT, not INVIGILATOR
            self.assertIn(response.status_code, [302, 303])

    def test_student_cannot_access_admin_dashboard(self):
        """Student role should be redirected away from admin pages."""
        from app import create_app

        app = create_app()
        app.config['TESTING'] = True

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = 1
                sess['username'] = 'student_test'
                sess['role'] = 'STUDENT'

            response = client.get('/admin/dashboard', follow_redirects=False)
            self.assertIn(response.status_code, [302, 303])


if __name__ == '__main__':
    unittest.main()
