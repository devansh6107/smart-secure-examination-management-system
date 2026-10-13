"""
Database Query Functions.

Centralised module for all parameterised SQL queries used by
the application. Keeps SQL visible and understandable for
academic evaluation.
"""

from app.database import get_db_connection
from mysql.connector import Error


# ──────────────────────────────────────────────
#  USER QUERIES
# ──────────────────────────────────────────────

def get_user_by_username(username):
    """Fetch a single user by username."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT user_id, username, email, password_hash, role, is_active "
            "FROM User WHERE username = %s",
            (username,)
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_user_by_id(user_id):
    """Fetch a single user by user_id."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT user_id, username, email, role, is_active "
            "FROM User WHERE user_id = %s",
            (user_id,)
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def create_user(username, email, password_hash, role):
    """Insert a new user and return the new user_id."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO User (username, email, password_hash, role) "
            "VALUES (%s, %s, %s, %s)",
            (username, email, password_hash, role)
        )
        conn.commit()
        return cursor.lastrowid
    except Error as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


# ──────────────────────────────────────────────
#  STUDENT QUERIES
# ──────────────────────────────────────────────

def get_student_by_user_id(user_id):
    """Get student profile linked to a user account."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT s.student_id, s.registration_no, s.name, "
            "       s.year, s.section, s.phone, "
            "       d.department_name, d.department_code "
            "FROM Student s "
            "INNER JOIN Department d ON s.department_id = d.department_id "
            "WHERE s.user_id = %s",
            (user_id,)
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_all_students():
    """List all students with department info."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT s.student_id, s.registration_no, s.name, "
            "       s.year, s.section, s.phone, "
            "       d.department_name, d.department_code, "
            "       u.email, u.is_active, u.user_id "
            "FROM Student s "
            "INNER JOIN Department d ON s.department_id = d.department_id "
            "INNER JOIN User u ON s.user_id = u.user_id "
            "ORDER BY s.registration_no"
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


# ──────────────────────────────────────────────
#  INVIGILATOR QUERIES
# ──────────────────────────────────────────────

def get_invigilator_by_user_id(user_id):
    """Get invigilator profile linked to a user account."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT invigilator_id, employee_id, name, phone, designation "
            "FROM Invigilator WHERE user_id = %s",
            (user_id,)
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


# ──────────────────────────────────────────────
#  DASHBOARD STATS
# ──────────────────────────────────────────────

def get_admin_dashboard_stats():
    """Aggregate counts for the admin dashboard."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)

        stats = {}

        cursor.execute("SELECT COUNT(*) AS cnt FROM Student")
        stats['total_students'] = cursor.fetchone()['cnt']

        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM Exam "
            "WHERE status IN ('Scheduled', 'Ongoing')"
        )
        stats['active_exams'] = cursor.fetchone()['cnt']

        cursor.execute("SELECT COUNT(*) AS cnt FROM ExamRoom")
        stats['total_rooms'] = cursor.fetchone()['cnt']

        cursor.execute("SELECT COUNT(*) AS cnt FROM Department")
        stats['total_departments'] = cursor.fetchone()['cnt']

        cursor.execute("SELECT COUNT(*) AS cnt FROM Invigilator")
        stats['total_invigilators'] = cursor.fetchone()['cnt']

        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM AIAlert WHERE status = 'Pending'"
        )
        stats['pending_alerts'] = cursor.fetchone()['cnt']

        # Recent attendance summary
        cursor.execute(
            "SELECT "
            "  COALESCE(SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END),0) AS present, "
            "  COALESCE(SUM(CASE WHEN status='Absent'  THEN 1 ELSE 0 END),0) AS absent, "
            "  COALESCE(SUM(CASE WHEN status='Late'    THEN 1 ELSE 0 END),0) AS late "
            "FROM Attendance"
        )
        att = cursor.fetchone()
        stats['attendance'] = att

        # Recent incidents count
        cursor.execute("SELECT COUNT(*) AS cnt FROM Incident")
        stats['total_incidents'] = cursor.fetchone()['cnt']

        return stats
    finally:
        cursor.close()
        conn.close()


def get_student_dashboard_data(student_id):
    """Data for the student dashboard: upcoming exams, allocations."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        data = {}

        # Upcoming exams (registered, not completed/cancelled)
        cursor.execute(
            "SELECT e.exam_id, sub.subject_name, sub.subject_code, "
            "       e.exam_date, e.start_time, e.end_time, "
            "       e.exam_type, e.status, "
            "       CONCAT(r.building, ' - ', r.room_number) AS room "
            "FROM ExamRegistration er "
            "INNER JOIN Exam e      ON er.exam_id    = e.exam_id "
            "INNER JOIN Subject sub ON e.subject_id  = sub.subject_id "
            "INNER JOIN ExamRoom r  ON e.room_id     = r.room_id "
            "WHERE er.student_id = %s "
            "  AND er.registration_status = 'Registered' "
            "ORDER BY e.exam_date, e.start_time",
            (student_id,)
        )
        data['upcoming_exams'] = cursor.fetchall()

        # Seat allocation info
        cursor.execute(
            "SELECT sa.allocation_id, sub.subject_name, "
            "       e.exam_date, e.exam_type, "
            "       CONCAT(r.building, ' - ', r.room_number) AS room, "
            "       se.seat_number, sa.allocation_status "
            "FROM SeatAllocation sa "
            "INNER JOIN Exam e      ON sa.exam_id   = e.exam_id "
            "INNER JOIN Subject sub ON e.subject_id  = sub.subject_id "
            "INNER JOIN ExamRoom r  ON e.room_id     = r.room_id "
            "INNER JOIN Seat se     ON sa.seat_id    = se.seat_id "
            "WHERE sa.student_id = %s "
            "ORDER BY e.exam_date DESC",
            (student_id,)
        )
        data['allocations'] = cursor.fetchall()

        # Attendance records
        cursor.execute(
            "SELECT sub.subject_name, e.exam_type, "
            "       att.status AS attendance_status, att.check_in_time "
            "FROM Attendance att "
            "INNER JOIN SeatAllocation sa ON att.allocation_id = sa.allocation_id "
            "INNER JOIN Exam e           ON sa.exam_id        = e.exam_id "
            "INNER JOIN Subject sub      ON e.subject_id      = sub.subject_id "
            "WHERE sa.student_id = %s "
            "ORDER BY e.exam_date DESC",
            (student_id,)
        )
        data['attendance'] = cursor.fetchall()

        # Authentication status
        cursor.execute(
            "SELECT sub.subject_name, e.exam_type, "
            "       auth.method, auth.verification_status, auth.verified_at "
            "FROM Authentication auth "
            "INNER JOIN SeatAllocation sa ON auth.allocation_id = sa.allocation_id "
            "INNER JOIN Exam e           ON sa.exam_id         = e.exam_id "
            "INNER JOIN Subject sub      ON e.subject_id       = sub.subject_id "
            "WHERE sa.student_id = %s "
            "ORDER BY auth.verified_at DESC",
            (student_id,)
        )
        data['auth_attempts'] = cursor.fetchall()

        return data
    finally:
        cursor.close()
        conn.close()


def get_invigilator_dashboard_data(invigilator_id):
    """Data for the invigilator dashboard: assigned exams, alerts."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        data = {}

        # Assigned exams
        cursor.execute(
            "SELECT e.exam_id, sub.subject_name, sub.subject_code, "
            "       e.exam_date, e.start_time, e.end_time, "
            "       e.exam_type, e.status, "
            "       CONCAT(r.building, ' - ', r.room_number) AS room, "
            "       r.capacity, "
            "       (SELECT COUNT(*) FROM ExamRegistration er "
            "        WHERE er.exam_id = e.exam_id "
            "          AND er.registration_status = 'Registered') AS student_count "
            "FROM Exam e "
            "INNER JOIN Subject sub ON e.subject_id = sub.subject_id "
            "INNER JOIN ExamRoom r  ON e.room_id    = r.room_id "
            "WHERE e.invigilator_id = %s "
            "ORDER BY e.exam_date, e.start_time",
            (invigilator_id,)
        )
        data['assigned_exams'] = cursor.fetchall()

        # Pending AI alerts for assigned exams
        cursor.execute(
            "SELECT al.alert_id, s.registration_no, s.name AS student_name, "
            "       al.alert_type, al.confidence, al.alert_time, al.status, "
            "       sub.subject_name, se.seat_number "
            "FROM AIAlert al "
            "INNER JOIN SeatAllocation sa ON al.allocation_id = sa.allocation_id "
            "INNER JOIN Student s        ON sa.student_id    = s.student_id "
            "INNER JOIN Exam e           ON sa.exam_id       = e.exam_id "
            "INNER JOIN Subject sub      ON e.subject_id     = sub.subject_id "
            "INNER JOIN Seat se          ON sa.seat_id       = se.seat_id "
            "WHERE e.invigilator_id = %s "
            "ORDER BY al.alert_time DESC",
            (invigilator_id,)
        )
        data['alerts'] = cursor.fetchall()

        # Recent incidents
        cursor.execute(
            "SELECT inc.incident_id, s.name AS student_name, "
            "       inc.incident_type, inc.description, "
            "       inc.incident_time "
            "FROM Incident inc "
            "INNER JOIN SeatAllocation sa ON inc.allocation_id = sa.allocation_id "
            "INNER JOIN Student s        ON sa.student_id     = s.student_id "
            "WHERE inc.invigilator_id = %s "
            "ORDER BY inc.incident_time DESC "
            "LIMIT 10",
            (invigilator_id,)
        )
        data['incidents'] = cursor.fetchall()

        return data
    finally:
        cursor.close()
        conn.close()
