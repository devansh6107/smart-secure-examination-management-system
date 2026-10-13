"""
Tests — Stage 2: Admin CRUD workflows.
Verifies the database query functions directly.
"""

import sys
import os
import pytest
from mysql.connector import Error

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestAdminQueries:
    """Test Admin Database Queries."""

    def test_department_crud(self):
        from app.database.admin_queries import create_department, get_all_departments, update_department
        
        dept_id = create_department("Test Department", "TST")
        assert dept_id > 0
        
        depts = get_all_departments()
        created_dept = next((d for d in depts if d['department_id'] == dept_id), None)
        assert created_dept is not None
        assert created_dept['department_name'] == "Test Department"
        
        update_department(dept_id, "Updated Department", "T2")
        depts_after = get_all_departments()
        updated = next((d for d in depts_after if d['department_id'] == dept_id), None)
        assert updated['department_code'] == "T2"

    def test_subject_crud(self):
        from app.database.admin_queries import create_subject, get_all_subjects, update_subject
        
        subject_id = create_subject("TEST101", "Test Subject", 4)
        assert subject_id > 0
        
        subjects = get_all_subjects()
        s = next((s for s in subjects if s['subject_id'] == subject_id), None)
        assert s is not None
        
        update_subject(subject_id, "TEST102", "Test 2", 3)
        subjects_after = get_all_subjects()
        updated = next((s for s in subjects_after if s['subject_id'] == subject_id), None)
        assert updated['subject_code'] == "TEST102"
        assert updated['credits'] == 3

    def test_room_crud(self):
        from app.database.admin_queries import create_room, get_all_rooms, update_room
        
        room_id = create_room("T101", "Test Building", 1, 50)
        assert room_id > 0
        
        rooms = get_all_rooms()
        r = next((r for r in rooms if r['room_id'] == room_id), None)
        assert r is not None
        assert r['capacity'] == 50
        
        update_room(room_id, "T101", "Test Building", 2, 60)
        rooms_after = get_all_rooms()
        updated = next((r for r in rooms_after if r['room_id'] == room_id), None)
        assert updated['floor'] == 2
        assert updated['capacity'] == 60

    def test_exam_registration(self):
        from app.database.admin_queries import register_student_for_exam, get_exam_registrations, cancel_registration
        from app.database.queries import get_all_students
        
        # In the seed data, there's an exam with exam_id = 6 (Physics) and no registrations.
        # Student 1 is registered to Exam 1, 2, 3. 
        # Let's use exam 6 and student 1
        
        students = get_all_students()
        student_id = students[0]['student_id']
        exam_id = 6
        
        # 1. Register
        reg_id = register_student_for_exam(student_id, exam_id)
        assert reg_id > 0
        
        # 2. Check it's there
        regs = get_exam_registrations(exam_id)
        assert len([r for r in regs if r['student_id'] == student_id]) == 1
        
        # 3. Duplicate Registration should fail
        with pytest.raises(Error) as exc_info:
            register_student_for_exam(student_id, exam_id)
        assert "Duplicate entry" in str(exc_info.value) or exc_info.value.errno == 1062
        
        # 4. Cancel
        cancel_registration(reg_id)
        regs_after = get_exam_registrations(exam_id)
        canceled_reg = next((r for r in regs_after if r['registration_id'] == reg_id), None)
        assert canceled_reg['registration_status'] == 'Cancelled'

    def test_dashboard_stats(self):
        from app.database.queries import get_admin_dashboard_stats
        
        stats = get_admin_dashboard_stats()
        assert 'total_students' in stats
        assert 'total_rooms' in stats
        assert 'total_departments' in stats
        assert 'active_exams' in stats
        assert 'pending_alerts' in stats
