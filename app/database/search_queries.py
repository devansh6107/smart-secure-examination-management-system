"""
Search Queries.

Role-aware parameterized search against the relational database.
Strictly enforces access boundaries based on user role.
"""

from app.database import get_db_connection


def search_admin_records(query_term, limit=6):
    """
    Search students, subjects, exams, rooms, and incidents for the Admin role.
    Uses parameterized SQL queries.
    """
    if not query_term or len(query_term.strip()) < 2:
        return []

    term = f"%{query_term.strip()}%"
    results = []
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)

        # 1. Search Students
        cursor.execute("""
            SELECT s.student_id, s.registration_no, s.name, d.department_code, s.year
            FROM Student s
            LEFT JOIN Department d ON s.department_id = d.department_id
            WHERE s.name LIKE %s OR s.registration_no LIKE %s
            ORDER BY s.name ASC
            LIMIT %s
        """, (term, term, limit))
        for row in cursor.fetchall():
            results.append({
                'category': 'Students',
                'title': f"{row['name']} ({row['registration_no']})",
                'subtitle': f"Dept: {row.get('department_code') or 'N/A'} · Year {row['year']}",
                'url': f"/admin/students/{row['student_id']}/edit",
                'badge': 'Student',
                'badge_color': 'success'
            })

        # 2. Search Subjects
        cursor.execute("""
            SELECT subject_id, subject_code, subject_name, credits
            FROM Subject
            WHERE subject_name LIKE %s OR subject_code LIKE %s
            ORDER BY subject_code ASC
            LIMIT %s
        """, (term, term, limit))
        for row in cursor.fetchall():
            results.append({
                'category': 'Subjects',
                'title': f"{row['subject_code']} - {row['subject_name']}",
                'subtitle': f"Credits: {row['credits']}",
                'url': f"/admin/subjects/{row['subject_id']}/edit",
                'badge': 'Subject',
                'badge_color': 'info'
            })

        # 3. Search Exams
        cursor.execute("""
            SELECT e.exam_id, sub.subject_code, sub.subject_name, e.exam_date, e.exam_type,
                   CONCAT(r.building, ' ', r.room_number) AS room_name
            FROM Exam e
            JOIN Subject sub ON e.subject_id = sub.subject_id
            LEFT JOIN ExamRoom r ON e.room_id = r.room_id
            WHERE sub.subject_name LIKE %s OR sub.subject_code LIKE %s OR e.exam_type LIKE %s
            ORDER BY e.exam_date DESC
            LIMIT %s
        """, (term, term, term, limit))
        for row in cursor.fetchall():
            results.append({
                'category': 'Exams',
                'title': f"{row['subject_code']} {row['exam_type']} ({row['exam_date']})",
                'subtitle': f"{row['subject_name']} · Room: {row['room_name'] or 'TBD'}",
                'url': f"/admin/exams/{row['exam_id']}/edit",
                'badge': 'Exam',
                'badge_color': 'primary'
            })

        # 4. Search Rooms
        cursor.execute("""
            SELECT room_id, building, room_number, capacity
            FROM ExamRoom
            WHERE building LIKE %s OR room_number LIKE %s
            ORDER BY building, room_number
            LIMIT %s
        """, (term, term, limit))
        for row in cursor.fetchall():
            results.append({
                'category': 'Rooms',
                'title': f"{row['building']} - {row['room_number']}",
                'subtitle': f"Capacity: {row['capacity']} seats",
                'url': f"/admin/rooms/{row['room_id']}/edit",
                'badge': 'Room',
                'badge_color': 'secondary'
            })

        # 5. Search Incidents
        cursor.execute("""
            SELECT incident_id, incident_type, description, incident_time
            FROM Incident
            WHERE incident_type LIKE %s OR description LIKE %s
            ORDER BY incident_time DESC
            LIMIT %s
        """, (term, term, limit))
        for row in cursor.fetchall():
            results.append({
                'category': 'Incidents',
                'title': f"{row['incident_type']}",
                'subtitle': (row['description'][:60] + '...') if row.get('description') and len(row['description']) > 60 else (row.get('description') or 'No details'),
                'url': "/admin/incidents",
                'badge': 'Incident',
                'badge_color': 'danger'
            })

        return results
    finally:
        cursor.close()
        conn.close()


def search_invigilator_records(query_term, invigilator_id, limit=6):
    """
    Search assigned exams, enrolled students, and reported incidents for an Invigilator.
    """
    if not query_term or len(query_term.strip()) < 2:
        return []

    term = f"%{query_term.strip()}%"
    results = []
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)

        # 1. Search Assigned Exams
        cursor.execute("""
            SELECT e.exam_id, sub.subject_code, sub.subject_name, e.exam_date, e.exam_type,
                   CONCAT(r.building, ' ', r.room_number) AS room_name
            FROM Exam e
            JOIN Subject sub ON e.subject_id = sub.subject_id
            JOIN ExamRoom r ON e.room_id = r.room_id
            WHERE e.invigilator_id = %s
              AND (sub.subject_name LIKE %s OR sub.subject_code LIKE %s OR e.exam_type LIKE %s)
            ORDER BY e.exam_date ASC
            LIMIT %s
        """, (invigilator_id, term, term, term, limit))
        for row in cursor.fetchall():
            results.append({
                'category': 'Assigned Exams',
                'title': f"{row['subject_code']} {row['exam_type']}",
                'subtitle': f"{row['subject_name']} · {row['exam_date']} · {row['room_name']}",
                'url': f"/invigilator/exam/{row['exam_id']}",
                'badge': 'Exam',
                'badge_color': 'warning'
            })

        # 2. Search Students in Assigned Exams
        cursor.execute("""
            SELECT DISTINCT s.name, s.registration_no, sub.subject_code, e.exam_id, se.seat_number
            FROM SeatAllocation sa
            JOIN Student s ON sa.student_id = s.student_id
            JOIN Exam e ON sa.exam_id = e.exam_id
            JOIN Subject sub ON e.subject_id = sub.subject_id
            JOIN Seat se ON sa.seat_id = se.seat_id
            WHERE e.invigilator_id = %s
              AND (s.name LIKE %s OR s.registration_no LIKE %s)
            LIMIT %s
        """, (invigilator_id, term, term, limit))
        for row in cursor.fetchall():
            results.append({
                'category': 'Students in Hall',
                'title': f"{row['name']} ({row['registration_no']})",
                'subtitle': f"Exam: {row['subject_code']} · Seat: {row['seat_number']}",
                'url': f"/invigilator/exam/{row['exam_id']}",
                'badge': 'Student',
                'badge_color': 'info'
            })

        # 3. Search Reported Incidents
        cursor.execute("""
            SELECT incident_id, incident_type, description
            FROM Incident
            WHERE invigilator_id = %s
              AND (incident_type LIKE %s OR description LIKE %s)
            ORDER BY incident_time DESC
            LIMIT %s
        """, (invigilator_id, term, term, limit))
        for row in cursor.fetchall():
            results.append({
                'category': 'Reported Incidents',
                'title': f"{row['incident_type']}",
                'subtitle': (row['description'][:60] if row.get('description') else 'No details'),
                'url': "/invigilator/incidents",
                'badge': 'Incident',
                'badge_color': 'danger'
            })

        return results
    finally:
        cursor.close()
        conn.close()


def search_student_records(query_term, student_id, limit=6):
    """
    Search registered exams and hall ticket details for a Student.
    """
    if not query_term or len(query_term.strip()) < 2:
        return []

    term = f"%{query_term.strip()}%"
    results = []
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT e.exam_id, sub.subject_code, sub.subject_name, e.exam_date, e.exam_type,
                   r.building, r.room_number, se.seat_number, er.registration_status
            FROM ExamRegistration er
            JOIN Exam e ON er.exam_id = e.exam_id
            JOIN Subject sub ON e.subject_id = sub.subject_id
            LEFT JOIN ExamRoom r ON e.room_id = r.room_id
            LEFT JOIN SeatAllocation sa ON (sa.exam_id = e.exam_id AND sa.student_id = er.student_id)
            LEFT JOIN Seat se ON sa.seat_id = se.seat_id
            WHERE er.student_id = %s
              AND (sub.subject_name LIKE %s OR sub.subject_code LIKE %s OR e.exam_type LIKE %s)
            ORDER BY e.exam_date ASC
            LIMIT %s
        """, (student_id, term, term, term, limit))
        for row in cursor.fetchall():
            seat_info = f"Seat {row['seat_number']}" if row.get('seat_number') else "Pending Allocation"
            results.append({
                'category': 'My Exams',
                'title': f"{row['subject_code']} - {row['subject_name']}",
                'subtitle': f"{row['exam_type']} · {row['exam_date']} · {seat_info}",
                'url': f"/student/hall-ticket/{row['exam_id']}",
                'badge': 'Hall Ticket',
                'badge_color': 'success'
            })

        return results
    finally:
        cursor.close()
        conn.close()
