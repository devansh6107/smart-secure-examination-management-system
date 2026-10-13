"""
Tests — Stage 3: Operational workflows.
Verifies smart seating, attendance, and authentication logic.
"""

import sys
import os
import pytest
from mysql.connector import Error

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestOperations:
    """Test Stage 3 Operations."""

    def test_generate_seats(self):
        from app.database.operational_queries import generate_seats_for_room
        from app.database import get_db_connection
        
        room_id = 4 # Room 4 (T101) has no seats generated in seed data.
        
        # Generate a small 2x2 grid (4 seats)
        total = generate_seats_for_room(room_id, 2, 2)
        assert total == 4
        
        # Verify in DB
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Seat WHERE room_id = %s", (room_id,))
        seats = cursor.fetchall()
        cursor.close()
        conn.close()
        
        assert len(seats) == 4
        seat_numbers = [s['seat_number'] for s in seats]
        assert 'A1' in seat_numbers
        assert 'A2' in seat_numbers
        assert 'B1' in seat_numbers
        assert 'B2' in seat_numbers

    def test_allocation_capacity_overflow(self):
        from app.database.operational_queries import allocate_seats_for_exam, generate_seats_for_room
        from app.database.admin_queries import register_student_for_exam
        from app.database.queries import get_all_students
        from app.database import get_db_connection
        
        # Setup: Create an exam with 5 students registered, but only 4 seats available.
        # Let's use Exam 4 (which uses room 4 - the one we just generated 4 seats for)
        exam_id = 4
        
        students = get_all_students()
        
        # Register 5 students for exam 4
        conn = get_db_connection()
        cursor = conn.cursor()
        for i in range(5):
            cursor.execute("INSERT IGNORE INTO ExamRegistration (student_id, exam_id) VALUES (%s, %s)", (students[i]['student_id'], exam_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        # Try to allocate -> Should raise Capacity Overflow
        with pytest.raises(Exception) as exc_info:
            allocate_seats_for_exam(exam_id)
        assert "Capacity Overflow" in str(exc_info.value)

    def test_successful_allocation_and_duplicate_prevention(self):
        from app.database.operational_queries import allocate_seats_for_exam
        from app.database import get_db_connection
        
        # Setup: Let's use Exam 2 (which uses Room 2). Room 2 capacity is 40 in seed data.
        exam_id = 2
        room_id = 2
        
        # Register 2 students
        conn = get_db_connection()
        cursor = conn.cursor()
        # Ensure clear
        cursor.execute("DELETE FROM SeatAllocation WHERE exam_id = %s", (exam_id,))
        cursor.execute("DELETE FROM ExamRegistration WHERE exam_id = %s", (exam_id,))
        cursor.execute("INSERT INTO ExamRegistration (student_id, exam_id) VALUES (1, %s), (2, %s)", (exam_id, exam_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        # Allocate
        count = allocate_seats_for_exam(exam_id)
        assert count == 2
        
        # Allocate again -> Should return 0 (no new students)
        count_again = allocate_seats_for_exam(exam_id)
        assert count_again == 0
        
        # Re-register a student? The DB unique constraint prevents duplicate registration.

    def test_attendance_and_authentication(self):
        from app.database.operational_queries import mark_attendance, record_authentication_attempt, get_authentication_history, get_exam_attendance_sheet
        
        # Using Exam 2 which we just allocated 2 students to
        exam_id = 2
        allocations = get_exam_attendance_sheet(exam_id)
        assert len(allocations) == 2
        
        alloc_id = allocations[0]['allocation_id']
        
        # Mark Present
        mark_attendance(alloc_id, 'Present', invigilator_id=1)
        
        # Verify check-in time is not null
        sheet = get_exam_attendance_sheet(exam_id)
        updated_alloc = next(a for a in sheet if a['allocation_id'] == alloc_id)
        assert updated_alloc['attendance_status'] == 'Present'
        assert updated_alloc['check_in_time'] is not None
        
        # Multiple Auth Attempts
        record_authentication_attempt(alloc_id, 'QR', 0)    # Fail
        record_authentication_attempt(alloc_id, 'Face', 1)  # Success
        
        history = get_authentication_history(alloc_id)
        assert len(history) == 2
        methods = [h['method'] for h in history]
        assert 'Face' in methods
        assert 'QR' in methods
