"""
Admin Database Query Functions.
Extends the application's parameterised queries for the Admin modules.
"""

from app.database import get_db_connection
from mysql.connector import Error

# ──────────────────────────────────────────────
#  DEPARTMENT
# ──────────────────────────────────────────────

def get_all_departments():
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Department ORDER BY department_name")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def create_department(name, code):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Department (department_name, department_code) VALUES (%s, %s)",
            (name, code)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()

def update_department(dept_id, name, code):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Department SET department_name = %s, department_code = %s WHERE department_id = %s",
            (name, code, dept_id)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# ──────────────────────────────────────────────
#  SUBJECT
# ──────────────────────────────────────────────

def get_all_subjects():
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Subject ORDER BY subject_code")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def create_subject(code, name, credits):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Subject (subject_code, subject_name, credits) VALUES (%s, %s, %s)",
            (code, name, credits)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()

def update_subject(subject_id, code, name, credits):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Subject SET subject_code = %s, subject_name = %s, credits = %s WHERE subject_id = %s",
            (code, name, credits, subject_id)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# ──────────────────────────────────────────────
#  EXAM ROOM
# ──────────────────────────────────────────────

def get_all_rooms():
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        # Using LEFT JOIN and GROUP BY to show number of actual seats configured
        cursor.execute(
            "SELECT r.room_id, r.room_number, r.building, r.floor, r.capacity, "
            "COUNT(s.seat_id) as actual_seats "
            "FROM ExamRoom r "
            "LEFT JOIN Seat s ON r.room_id = s.room_id "
            "GROUP BY r.room_id, r.room_number, r.building, r.floor, r.capacity "
            "ORDER BY r.building, r.room_number"
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def create_room(room_number, building, floor, capacity):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ExamRoom (room_number, building, floor, capacity) VALUES (%s, %s, %s, %s)",
            (room_number, building, floor, capacity)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()

def update_room(room_id, room_number, building, floor, capacity):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE ExamRoom SET room_number = %s, building = %s, floor = %s, capacity = %s WHERE room_id = %s",
            (room_number, building, floor, capacity, room_id)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# ──────────────────────────────────────────────
#  INVIGILATOR
# ──────────────────────────────────────────────

def get_all_invigilators():
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT i.invigilator_id, i.employee_id, i.name, i.phone, i.designation, "
            "u.email, u.is_active, u.user_id "
            "FROM Invigilator i "
            "INNER JOIN User u ON i.user_id = u.user_id "
            "ORDER BY i.name"
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def create_invigilator(user_id, employee_id, name, phone, designation):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Invigilator (user_id, employee_id, name, phone, designation) "
            "VALUES (%s, %s, %s, %s, %s)",
            (user_id, employee_id, name, phone, designation)
        )
        conn.commit()
        return cursor.lastrowid
    except Error as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def update_invigilator(invigilator_id, employee_id, name, phone, designation):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Invigilator SET employee_id = %s, name = %s, phone = %s, designation = %s WHERE invigilator_id = %s",
            (employee_id, name, phone, designation, invigilator_id)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def deactivate_user(user_id, is_active=False):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE User SET is_active = %s WHERE user_id = %s",
            (is_active, user_id)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# ──────────────────────────────────────────────
#  STUDENT
# ──────────────────────────────────────────────

def create_student(user_id, registration_no, name, department_id, year, section, phone):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Student (user_id, registration_no, name, department_id, year, section, phone) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (user_id, registration_no, name, department_id, year, section, phone)
        )
        conn.commit()
        return cursor.lastrowid
    except Error as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def update_student(student_id, registration_no, name, department_id, year, section, phone):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Student SET registration_no = %s, name = %s, department_id = %s, year = %s, section = %s, phone = %s "
            "WHERE student_id = %s",
            (registration_no, name, department_id, year, section, phone, student_id)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# ──────────────────────────────────────────────
#  EXAM
# ──────────────────────────────────────────────

def get_all_exams():
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT e.exam_id, e.exam_date, e.start_time, e.end_time, "
            "e.semester, e.academic_year, e.exam_type, e.status, "
            "sub.subject_code, sub.subject_name, "
            "CONCAT(r.building, ' - ', r.room_number) as room_name, "
            "i.name as invigilator_name, "
            "(SELECT COUNT(*) FROM ExamRegistration er WHERE er.exam_id = e.exam_id) as registered_students "
            "FROM Exam e "
            "INNER JOIN Subject sub ON e.subject_id = sub.subject_id "
            "INNER JOIN ExamRoom r ON e.room_id = r.room_id "
            "INNER JOIN Invigilator i ON e.invigilator_id = i.invigilator_id "
            "ORDER BY e.exam_date DESC, e.start_time DESC"
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def create_exam(subject_id, room_id, invigilator_id, exam_date, start_time, end_time, semester, academic_year, exam_type, status='Scheduled'):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Exam (subject_id, room_id, invigilator_id, exam_date, start_time, end_time, semester, academic_year, exam_type, status) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (subject_id, room_id, invigilator_id, exam_date, start_time, end_time, semester, academic_year, exam_type, status)
        )
        conn.commit()
        return cursor.lastrowid
    except Error as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def update_exam(exam_id, subject_id, room_id, invigilator_id, exam_date, start_time, end_time, semester, academic_year, exam_type, status):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Exam SET subject_id = %s, room_id = %s, invigilator_id = %s, exam_date = %s, start_time = %s, end_time = %s, semester = %s, academic_year = %s, exam_type = %s, status = %s "
            "WHERE exam_id = %s",
            (subject_id, room_id, invigilator_id, exam_date, start_time, end_time, semester, academic_year, exam_type, status, exam_id)
        )
        conn.commit()
    except Error as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def cancel_exam(exam_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE Exam SET status = 'Cancelled' WHERE exam_id = %s", (exam_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# ──────────────────────────────────────────────
#  EXAM REGISTRATION
# ──────────────────────────────────────────────

def get_exam_registrations(exam_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT er.registration_id, er.registration_date, er.registration_status, "
            "s.student_id, s.registration_no, s.name, d.department_code "
            "FROM ExamRegistration er "
            "INNER JOIN Student s ON er.student_id = s.student_id "
            "INNER JOIN Department d ON s.department_id = d.department_id "
            "WHERE er.exam_id = %s "
            "ORDER BY s.registration_no",
            (exam_id,)
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def register_student_for_exam(student_id, exam_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ExamRegistration (student_id, exam_id) VALUES (%s, %s)",
            (student_id, exam_id)
        )
        conn.commit()
        return cursor.lastrowid
    except Error as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def cancel_registration(registration_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE ExamRegistration SET registration_status = 'Cancelled' WHERE registration_id = %s",
            (registration_id,)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()
