"""
Stage 5 Tests — Reports, Export, and Error Handling.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestReports(unittest.TestCase):
    """Test reports HTML rendering and CSV exports."""
    
    def setUp(self):
        from app import create_app
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_exam_summary_report_access(self):
        """Admin can access exam summary report."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['role'] = 'ADMIN'
            
        response = self.client.get('/admin/reports/exam_summary')
        self.assertEqual(response.status_code, 200)

    def test_exam_summary_csv_export(self):
        """Admin can export exam summary to CSV."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['role'] = 'ADMIN'
            
        response = self.client.get('/admin/reports/exam_summary?export=csv')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'text/csv; charset=utf-8') if 'charset' in response.headers['Content-Type'] else self.assertEqual(response.headers['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename=exam_summary_report.csv', response.headers['Content-Disposition'])
        
    def test_attendance_report_requires_exam_id(self):
        """Attendance report redirects if no exam_id provided."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['role'] = 'ADMIN'
            
        response = self.client.get('/admin/reports/attendance')
        self.assertEqual(response.status_code, 302) # Redirect to index
        
if __name__ == '__main__':
    unittest.main()
