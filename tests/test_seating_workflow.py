"""
Tests for Seating Chart Navigation & Student Allocation Workflow.

Verifies:
1. Visible Seating Chart action link on the Admin Exams list.
2. Complete end-to-end workflow:
   - Student registration
   - Room seat generation
   - Seating chart rendering with subject, room, registered count, and configured seat count
   - Distinction between physical room infrastructure and student exam allocation
   - Auto-allocation execution
   - Verification of resulting student-to-seat assignments
   - Prevention of duplicate allocations
   - Handling of insufficient seat capacity
3. Role-Based Access Control (RBAC) on seating routes.
"""

import pytest
from app import create_app
from app.database import get_db_connection
from app.database.admin_queries import (
    create_exam, register_student_for_exam, create_room, create_subject,
    get_all_invigilators
)
from app.database.operational_queries import (
    generate_seats_for_room, allocate_seats_for_exam, get_seating_chart
)


@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-seating-workflow-secret'
    })
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_client(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['username'] = 'admin'
        sess['role'] = 'ADMIN'
    return client


@pytest.fixture
def student_client(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['username'] = 'rahul.kumar'
        sess['role'] = 'STUDENT'
    return client


class TestSeatingNavigationWorkflow:
    """End-to-end tests for student seat-allocation navigation and execution."""

    def test_exams_list_displays_seating_chart_action(self, admin_client):
        """Requirement 1 & 2: Action link to seating chart is visible in admin exams list."""
        response = admin_client.get('/admin/exams/')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        
        # Verify action exists and links to /admin/exams/<id>/seating
        assert 'Seating Chart' in html
        assert '/admin/exams/' in html
        assert '/seating' in html

    def test_complete_seating_workflow(self, admin_client):
        """
        Requirement 3, 4, 5, 6, 9:
        Test the entire workflow:
        1. Create subject, room, exam, students
        2. Generate physical room seats
        3. Register students
        4. Open seating chart and verify metrics + distinctions
        5. Trigger auto-allocation
        6. Verify student-to-seat mappings
        7. Prevent duplicate allocations on re-run
        """
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get invigilator and active students
        invs = get_all_invigilators()
        inv_id = invs[0]['invigilator_id'] if invs else 1
        
        cursor.execute("SELECT student_id, name, registration_no FROM Student LIMIT 3")
        students = cursor.fetchall()
        assert len(students) >= 2, "Need at least 2 students for test"
        student_1 = students[0]['student_id']
        student_2 = students[1]['student_id']
        
        # Create a test room and exam
        cursor.execute(
            "INSERT INTO ExamRoom (room_number, building, floor, capacity) VALUES (%s, %s, %s, %s)",
            ('WFLOW1', 'Test Hall', 1, 10)
        )
        room_id = cursor.lastrowid
        
        cursor.execute("SELECT subject_id, subject_code, subject_name FROM Subject LIMIT 1")
        subj = cursor.fetchone()
        subject_id = subj['subject_id']
        subject_code = subj['subject_code']
        subject_name = subj['subject_name']
        
        cursor.execute(
            "INSERT INTO Exam (subject_id, room_id, invigilator_id, exam_date, start_time, end_time, semester, academic_year, exam_type, status) "
            "VALUES (%s, %s, %s, '2026-11-20', '10:00:00', '13:00:00', 'Fall', 2026, 'CAT1', 'Scheduled')",
            (subject_id, room_id, inv_id)
        )
        exam_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()

        try:
            # Step 1: Generate physical room seats (3 rows x 2 cols = 6 physical seats)
            generated_seats = generate_seats_for_room(room_id, 3, 2)
            assert generated_seats == 6

            # Step 2: Register 2 students for this exam
            reg1 = register_student_for_exam(student_1, exam_id)
            reg2 = register_student_for_exam(student_2, exam_id)
            assert reg1 > 0 and reg2 > 0

            # Step 3: Open exam seating chart via GET
            seating_url = f'/admin/exams/{exam_id}/seating'
            response = admin_client.get(seating_url)
            assert response.status_code == 200
            html = response.data.decode('utf-8')

            # Verify Requirement 3: Architectural distinction
            assert 'Physical Room Seats' in html
            assert 'Student Allocation' in html
            assert 'ExamRoom &rarr; Seat' in html or 'ExamRoom' in html
            assert 'ExamRegistration &rarr; SeatAllocation' in html or 'SeatAllocation' in html

            # Verify Requirement 4: Metrics displayed
            assert subject_code in html
            assert 'Test Hall - WFLOW1' in html
            assert 'Auto-Allocate Unassigned' in html

            # Step 4: Allocate seats via POST /admin/exams/<exam_id>/allocate
            alloc_url = f'/admin/exams/{exam_id}/allocate'
            alloc_response = admin_client.post(alloc_url, follow_redirects=True)
            assert alloc_response.status_code == 200
            alloc_html = alloc_response.data.decode('utf-8')
            assert 'Successfully allocated seats for 2 students' in alloc_html

            # Step 5: Verify allocations in database and seating chart
            chart = get_seating_chart(exam_id)
            assert len(chart) == 6 # 6 total physical seats in room
            
            allocated_seats = [s for s in chart if s['allocation_status'] == 'Allocated']
            assert len(allocated_seats) == 2
            
            allocated_reg_nos = {s['registration_no'] for s in allocated_seats}
            assert students[0]['registration_no'] in allocated_reg_nos
            assert students[1]['registration_no'] in allocated_reg_nos

            # Step 6: Verify duplicate allocation prevention (re-running returns 0 / info flash)
            realloc_response = admin_client.post(alloc_url, follow_redirects=True)
            assert realloc_response.status_code == 200
            realloc_html = realloc_response.data.decode('utf-8')
            assert 'No unassigned registered students to allocate' in realloc_html or 'No new students' in realloc_html

        finally:
            # Clean up test records
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("DELETE FROM SeatAllocation WHERE exam_id = %s", (exam_id,))
            c.execute("DELETE FROM ExamRegistration WHERE exam_id = %s", (exam_id,))
            c.execute("DELETE FROM Exam WHERE exam_id = %s", (exam_id,))
            c.execute("DELETE FROM Seat WHERE room_id = %s", (room_id,))
            c.execute("DELETE FROM ExamRoom WHERE room_id = %s", (room_id,))
            conn.commit()
            c.close()
            conn.close()

    def test_capacity_overflow_handling(self, admin_client):
        """Requirement 7: Clear error when registered students exceed available seats."""
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(
            "INSERT INTO ExamRoom (room_number, building, floor, capacity) VALUES (%s, %s, %s, %s)",
            ('OVRFLW', 'Tiny Room', 1, 1)
        )
        room_id = cursor.lastrowid
        
        cursor.execute("SELECT subject_id FROM Subject LIMIT 1")
        subject_id = cursor.fetchone()['subject_id']
        
        invs = get_all_invigilators()
        inv_id = invs[0]['invigilator_id'] if invs else 1
        
        cursor.execute(
            "INSERT INTO Exam (subject_id, room_id, invigilator_id, exam_date, start_time, end_time, semester, academic_year, exam_type, status) "
            "VALUES (%s, %s, %s, '2026-11-21', '09:00:00', '12:00:00', 'Fall', 2026, 'CAT1', 'Scheduled')",
            (subject_id, room_id, inv_id)
        )
        exam_id = cursor.lastrowid
        
        cursor.execute("SELECT student_id FROM Student LIMIT 2")
        students = cursor.fetchall()
        conn.commit()
        cursor.close()
        conn.close()

        try:
            # Generate only 1 seat for room
            generate_seats_for_room(room_id, 1, 1)
            
            # Register 2 students for the exam
            register_student_for_exam(students[0]['student_id'], exam_id)
            register_student_for_exam(students[1]['student_id'], exam_id)

            # POST allocate -> should flash capacity overflow error
            alloc_response = admin_client.post(f'/admin/exams/{exam_id}/allocate', follow_redirects=True)
            assert alloc_response.status_code == 200
            html = alloc_response.data.decode('utf-8')
            assert 'Capacity Overflow' in html or 'Allocation failed' in html

        finally:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("DELETE FROM SeatAllocation WHERE exam_id = %s", (exam_id,))
            c.execute("DELETE FROM ExamRegistration WHERE exam_id = %s", (exam_id,))
            c.execute("DELETE FROM Exam WHERE exam_id = %s", (exam_id,))
            c.execute("DELETE FROM Seat WHERE room_id = %s", (room_id,))
            c.execute("DELETE FROM ExamRoom WHERE room_id = %s", (room_id,))
            conn.commit()
            c.close()
            conn.close()

    def test_seating_rbac_enforcement(self, client, student_client):
        """Requirement 8: RBAC strictly enforced on seating chart and allocate routes."""
        # Unauthenticated access
        res1 = client.get('/admin/exams/1/seating', follow_redirects=False)
        assert res1.status_code in (302, 401)
        
        res2 = client.post('/admin/exams/1/allocate', follow_redirects=False)
        assert res2.status_code in (302, 401)
        
        # Student role access
        res3 = student_client.get('/admin/exams/1/seating', follow_redirects=False)
        assert res3.status_code == 302
        assert '/student/dashboard' in res3.headers.get('Location', '') or '/login' in res3.headers.get('Location', '')
        
        res4 = student_client.post('/admin/exams/1/allocate', follow_redirects=False)
        assert res4.status_code == 302
