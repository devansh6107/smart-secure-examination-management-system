"""
Tests for UI/UX Enhancements.

Verifies:
1. UTM parameter capture, validation, and session storage.
2. Role-enforced Search API endpoint behavior and queries.
3. Help and FAQ routes.
4. Validation and duplicate entry handling on student and room management.
"""

import pytest
from app import create_app
from app.services.utm_service import sanitize_utm_value, capture_utm_parameters


@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key-ui-ux'
    })
    return app


@pytest.fixture
def client(app):
    return app.test_client()


class TestUTMTracking:
    """Test Feature 14: UTM Parameter Tracking."""

    def test_utm_sanitization(self):
        assert sanitize_utm_value('google') == 'google'
        assert sanitize_utm_value('cpc_campaign-2026') == 'cpc_campaign-2026'
        assert sanitize_utm_value('<script>alert(1)</script>') is None
        assert sanitize_utm_value('') is None
        assert sanitize_utm_value('a' * 150) is None or len(sanitize_utm_value('a' * 150)) <= 100

    def test_utm_capture_in_session(self, client):
        res = client.get('/login?utm_source=university_portal&utm_medium=email&utm_campaign=fall2026')
        assert res.status_code == 200

        with client.session_transaction() as sess:
            assert 'utm_data' in sess
            assert sess['utm_data']['utm_source'] == 'university_portal'
            assert sess['utm_data']['utm_medium'] == 'email'
            assert sess['utm_data']['utm_campaign'] == 'fall2026'

    def test_utm_rejects_malicious_script(self, client):
        res = client.get('/login?utm_source=<script>alert("xss")</script>')
        assert res.status_code == 200
        with client.session_transaction() as sess:
            utm = sess.get('utm_data', {})
            assert 'utm_source' not in utm


class TestSearchAPI:
    """Test Feature 3: Site Search API with Role Enforcement."""

    def test_search_unauthenticated_returns_401(self, client):
        res = client.get('/api/search?q=test')
        assert res.status_code == 401
        data = res.get_json()
        assert data['error'] == 'Unauthorized'

    def test_search_short_query_returns_empty(self, client):
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['role'] = 'ADMIN'
            sess['username'] = 'admin'

        res = client.get('/api/search?q=a')
        assert res.status_code == 200
        data = res.get_json()
        assert data['total'] == 0
        assert data['results'] == []

    def test_admin_search_finds_students_and_exams(self, client):
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['role'] = 'ADMIN'
            sess['username'] = 'admin'

        res = client.get('/api/search?q=rahul')
        assert res.status_code == 200
        data = res.get_json()
        assert data['total'] >= 1
        assert any(r['category'] == 'Students' for r in data['results'])

    def test_student_search_enforces_boundaries(self, client):
        # User 2 is student rahul.kumar (student_id = 1)
        with client.session_transaction() as sess:
            sess['user_id'] = 2
            sess['role'] = 'STUDENT'
            sess['username'] = 'rahul.kumar'

        res = client.get('/api/search?q=CAT')
        assert res.status_code == 200
        data = res.get_json()
        assert data['role'] == 'STUDENT'
        # Any result returned should be category 'My Exams'
        for r in data['results']:
            assert r['category'] == 'My Exams'


class TestHelpAndFAQ:
    """Test Feature 19: Expandable FAQ and Help Center."""

    def test_faq_accessible_unauthenticated(self, client):
        res = client.get('/help')
        assert res.status_code == 200
        html = res.data.decode('utf-8')
        assert 'Frequently Asked Questions' in html
        assert 'How does login work?' in html
        assert 'What do AI proctoring alerts mean?' in html
        assert 'Examination Support Desk' in html

    def test_faq_accessible_via_faq_route(self, client):
        res = client.get('/faq')
        assert res.status_code == 200


class TestFormErrorHandling:
    """Test Feature 16: Form Error States and duplicate prevention."""

    def test_duplicate_student_registration_message(self, client):
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['role'] = 'ADMIN'
            sess['username'] = 'admin'

        # Post duplicate registration number '22BCE1001' (already in seed data)
        res = client.post('/admin/students/add', data={
            'registration_no': '22BCE1001',
            'name': 'Duplicate Student Test',
            'department_id': '1',
            'year': '2',
            'section': 'A',
            'phone': '9999999999'
        }, follow_redirects=True)

        assert res.status_code == 200
        html = res.data.decode('utf-8')
        assert 'already exists' in html.lower()
        # Ensure raw SQL / MySQL trace is NOT leaked
        assert 'mysql.connector.errors' not in html
        assert 'SQL syntax' not in html
