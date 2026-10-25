"""
Operational Queries.
Contains queries for Stage 3: Smart Seating, Attendance, and Authentication workflows.
"""

from app.database import get_db_connection
from mysql.connector import Error

def generate_seats_for_room(room_id, rows, cols):
    """
    Generates seats for a room using row/column logic.
    Clears existing seats first to avoid duplication (only if not allocated yet).
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        conn.start_transaction()
        
        # Check if room already has allocations
        cursor.execute('''
            SELECT COUNT(*) FROM SeatAllocation sa 
            JOIN Seat s ON sa.seat_id = s.seat_id 
            WHERE s.room_id = %s
        ''', (room_id,))
        if cursor.fetchone()[0] > 0:
            raise Exception("Cannot regenerate seats: Room has active allocations.")
        
        # Clear existing seats
        cursor.execute("DELETE FROM Seat WHERE room_id = %s", (room_id,))
        
        # Generate new seats
        for r in range(1, rows + 1):
            for c in range(1, cols + 1):
                seat_num = f"R{r}C{c}"
                cursor.execute(
                    "INSERT INTO Seat (room_id, seat_number, row_no, column_no) VALUES (%s, %s, %s, %s)",
                    (room_id, seat_num, r, c)
                )
        
        # Update actual capacity in ExamRoom (just to sync it, though it's technically fixed)
        cursor.execute("UPDATE ExamRoom SET capacity = %s WHERE room_id = %s", (rows * cols, room_id))
        
        conn.commit()
        return rows * cols
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def allocate_seats_for_exam(exam_id):
    """
    Algorithm:
    1. Retrieve all students registered for an exam.
    2. Retrieve all seats belonging to the exam's room.
    3. Verify capacity.
    4. Assign students to seats uniquely.
    5. Store allocations.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        conn.start_transaction()
        
        # Check exam exists and is active
        cursor.execute("SELECT room_id, status FROM Exam WHERE exam_id = %s", (exam_id,))
        room = cursor.fetchone()
        if not room:
            raise Exception("Exam not found or has no room assigned.")
        if room.get('status') in ('Cancelled', 'Completed'):
            raise Exception(f"Cannot allocate seats for an exam that is {room['status']}.")
        room_id = room['room_id']

        # SUBQUERY EXAMPLE 1: Fetch students registered but not allocated yet
        cursor.execute('''
            SELECT student_id FROM ExamRegistration 
            WHERE exam_id = %s AND registration_status = 'Registered'
            AND student_id NOT IN (
                SELECT student_id FROM SeatAllocation WHERE exam_id = %s AND allocation_status IN ('Allocated', 'Reallocated')
            )
            ORDER BY student_id
        ''', (exam_id, exam_id))
        students_to_allocate = [row['student_id'] for row in cursor.fetchall()]
        
        if not students_to_allocate:
            conn.rollback()
            return 0 # No one to allocate
        
        # Fetch available seats (not allocated for this exam)
        cursor.execute('''
            SELECT seat_id FROM Seat
            WHERE room_id = %s
            AND seat_id NOT IN (
                SELECT seat_id FROM SeatAllocation WHERE exam_id = %s AND allocation_status IN ('Allocated', 'Reallocated')
            )
            ORDER BY row_no, column_no
        ''', (room_id, exam_id))
        available_seats = [row['seat_id'] for row in cursor.fetchall()]
        
        # Verify Capacity
        if len(students_to_allocate) > len(available_seats):
            conn.rollback()
            raise Exception(f"Capacity Overflow: Need {len(students_to_allocate)} seats, but only {len(available_seats)} available.")
            
        # Assign unique seats
        allocations = 0
        for i, student_id in enumerate(students_to_allocate):
            seat_id = available_seats[i]
            
            # Double check validation (seat belongs to exam room)
            cursor.execute("SELECT room_id FROM Seat WHERE seat_id = %s", (seat_id,))
            seat_info = cursor.fetchone()
            if not seat_info or seat_info['room_id'] != room_id:
                raise Exception("Validation Error: Seat does not belong to the exam room.")
                
            cursor.execute(
                "INSERT INTO SeatAllocation (student_id, exam_id, seat_id, allocation_status) VALUES (%s, %s, %s, %s)",
                (student_id, exam_id, seat_id, 'Allocated')
            )
            allocations += 1
            
        conn.commit()
        return allocations
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def get_seating_chart(exam_id):
    """Gets the seating arrangement for an exam."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT sa.allocation_id, s.seat_number, s.row_no, s.column_no,
                   st.name, st.registration_no, sa.allocation_status
            FROM Seat s
            JOIN Exam e ON s.room_id = e.room_id
            LEFT JOIN SeatAllocation sa ON s.seat_id = sa.seat_id AND sa.exam_id = e.exam_id AND sa.allocation_status IN ('Allocated', 'Reallocated')
            LEFT JOIN Student st ON sa.student_id = st.student_id
            WHERE e.exam_id = %s
            ORDER BY s.row_no, s.column_no
        ''', (exam_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def cancel_seat_allocation(allocation_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE SeatAllocation SET allocation_status = 'Cancelled' WHERE allocation_id = %s", (allocation_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_invigilator_dashboard_stats(invigilator_id):
    """Stats for the Invigilator Dashboard."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        stats = {}
        
        # Subquery example 2
        cursor.execute("SELECT COUNT(*) as count FROM Exam WHERE invigilator_id = %s AND status = 'Scheduled'", (invigilator_id,))
        stats['assigned_exams'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM Exam WHERE invigilator_id = %s AND exam_date = CURDATE()", (invigilator_id,))
        stats['today_exams'] = cursor.fetchone()['count']
        
        return stats
    finally:
        cursor.close()
        conn.close()

def get_invigilator_exams(invigilator_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT e.*, sub.subject_code, sub.subject_name, r.building, r.room_number,
                   (SELECT COUNT(*) FROM SeatAllocation sa WHERE sa.exam_id = e.exam_id AND sa.allocation_status = 'Allocated') as allocated_count
            FROM Exam e
            JOIN Subject sub ON e.subject_id = sub.subject_id
            JOIN ExamRoom r ON e.room_id = r.room_id
            WHERE e.invigilator_id = %s
            ORDER BY e.exam_date ASC, e.start_time ASC
        ''', (invigilator_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def get_exam_attendance_sheet(exam_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT sa.allocation_id, st.registration_no, st.name, s.seat_number,
                   a.status as attendance_status, a.check_in_time,
                   (SELECT COUNT(*) FROM Authentication auth WHERE auth.allocation_id = sa.allocation_id AND auth.verification_status = 'Success') as has_auth
            FROM SeatAllocation sa
            JOIN Student st ON sa.student_id = st.student_id
            JOIN Seat s ON sa.seat_id = s.seat_id
            LEFT JOIN Attendance a ON sa.allocation_id = a.allocation_id
            WHERE sa.exam_id = %s AND sa.allocation_status = 'Allocated'
            ORDER BY s.row_no, s.column_no
        ''', (exam_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def mark_attendance(allocation_id, status, invigilator_id):
    """Mark attendance (Present, Absent, Late)."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if attendance record exists
        cursor.execute("SELECT attendance_id FROM Attendance WHERE allocation_id = %s", (allocation_id,))
        row = cursor.fetchone()
        
        if row:
            if status == 'Absent':
                cursor.execute("UPDATE Attendance SET status = %s, check_in_time = NULL, verified_by = %s WHERE allocation_id = %s", (status, invigilator_id, allocation_id))
            else:
                cursor.execute("UPDATE Attendance SET status = %s, check_in_time = CURRENT_TIMESTAMP, verified_by = %s WHERE allocation_id = %s", (status, invigilator_id, allocation_id))
        else:
            if status == 'Absent':
                cursor.execute("INSERT INTO Attendance (allocation_id, status, check_in_time, verified_by) VALUES (%s, %s, NULL, %s)", (allocation_id, status, invigilator_id))
            else:
                cursor.execute("INSERT INTO Attendance (allocation_id, status, check_in_time, verified_by) VALUES (%s, %s, CURRENT_TIMESTAMP, %s)", (allocation_id, status, invigilator_id))
        
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def record_authentication_attempt(allocation_id, method, success):
    """Store verification attempt."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        status_val = 'Success' if success else 'Failed'
        cursor.execute('''
            INSERT INTO Authentication (allocation_id, method, verification_status) 
            VALUES (%s, %s, %s)
        ''', (allocation_id, method, status_val))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_authentication_history(allocation_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT * FROM Authentication 
            WHERE allocation_id = %s 
            ORDER BY verified_at DESC
        ''', (allocation_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def get_student_hall_tickets(student_id):
    """Student Experience - Hall Ticket View with authentication status."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT e.exam_id, e.exam_date, e.start_time, e.end_time, e.exam_type,
                   sub.subject_code, sub.subject_name,
                   r.building, r.room_number,
                   er.registration_status,
                   sa.allocation_id,
                   s.seat_number,
                   a.status as attendance_status,
                   a.check_in_time,
                   (SELECT auth.verification_status FROM Authentication auth
                    WHERE auth.allocation_id = sa.allocation_id
                    ORDER BY auth.verified_at DESC LIMIT 1) AS auth_status,
                   (SELECT auth.method FROM Authentication auth
                    WHERE auth.allocation_id = sa.allocation_id
                    ORDER BY auth.verified_at DESC LIMIT 1) AS auth_method
            FROM ExamRegistration er
            JOIN Exam e ON er.exam_id = e.exam_id
            JOIN Subject sub ON e.subject_id = sub.subject_id
            LEFT JOIN ExamRoom r ON e.room_id = r.room_id
            LEFT JOIN SeatAllocation sa ON er.student_id = sa.student_id AND er.exam_id = sa.exam_id AND sa.allocation_status = 'Allocated'
            LEFT JOIN Seat s ON sa.seat_id = s.seat_id
            LEFT JOIN Attendance a ON sa.allocation_id = a.allocation_id
            WHERE er.student_id = %s
            ORDER BY e.exam_date ASC
        ''', (student_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


# ══════════════════════════════════════════════
#  STAGE 4: AI ALERT QUERIES
# ══════════════════════════════════════════════

def get_alerts_for_invigilator(invigilator_id, status_filter=None):
    """Get all AI alerts for exams assigned to this invigilator."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        query = '''
            SELECT al.alert_id, al.alert_type, al.confidence, al.alert_time, al.status,
                   st.registration_no, st.name AS student_name,
                   sub.subject_code, sub.subject_name, e.exam_type, e.exam_id,
                   se.seat_number, r.building, r.room_number
            FROM AIAlert al
            JOIN SeatAllocation sa ON al.allocation_id = sa.allocation_id
            JOIN Student st ON sa.student_id = st.student_id
            JOIN Exam e ON sa.exam_id = e.exam_id
            JOIN Subject sub ON e.subject_id = sub.subject_id
            JOIN Seat se ON sa.seat_id = se.seat_id
            JOIN ExamRoom r ON e.room_id = r.room_id
            WHERE e.invigilator_id = %s
        '''
        params = [invigilator_id]
        if status_filter and status_filter in ('Pending', 'Reviewed', 'Ignored'):
            query += " AND al.status = %s"
            params.append(status_filter)
        query += " ORDER BY al.alert_time DESC"
        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_all_alerts(exam_filter=None, type_filter=None, status_filter=None):
    """Admin: Get all AI alerts with optional filters."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        query = '''
            SELECT al.alert_id, al.alert_type, al.confidence, al.alert_time, al.status,
                   st.registration_no, st.name AS student_name,
                   sub.subject_code, sub.subject_name, e.exam_type, e.exam_id,
                   se.seat_number, r.building, r.room_number,
                   inv.name AS invigilator_name
            FROM AIAlert al
            JOIN SeatAllocation sa ON al.allocation_id = sa.allocation_id
            JOIN Student st ON sa.student_id = st.student_id
            JOIN Exam e ON sa.exam_id = e.exam_id
            JOIN Subject sub ON e.subject_id = sub.subject_id
            JOIN Seat se ON sa.seat_id = se.seat_id
            JOIN ExamRoom r ON e.room_id = r.room_id
            JOIN Invigilator inv ON e.invigilator_id = inv.invigilator_id
            WHERE 1=1
        '''
        params = []
        if exam_filter:
            query += " AND e.exam_id = %s"
            params.append(int(exam_filter))
        if type_filter and type_filter in ('Phone Detected', 'Suspicious Movement'):
            query += " AND al.alert_type = %s"
            params.append(type_filter)
        if status_filter and status_filter in ('Pending', 'Reviewed', 'Ignored'):
            query += " AND al.status = %s"
            params.append(status_filter)
        query += " ORDER BY al.alert_time DESC"
        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def review_alert(alert_id):
    """Set alert status to Reviewed."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE AIAlert SET status = 'Reviewed' WHERE alert_id = %s",
            (alert_id,)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def ignore_alert(alert_id):
    """Set alert status to Ignored."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE AIAlert SET status = 'Ignored' WHERE alert_id = %s",
            (alert_id,)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


# ══════════════════════════════════════════════
#  STAGE 4: INCIDENT QUERIES
# ══════════════════════════════════════════════

def create_incident(allocation_id, invigilator_id, incident_type, description, action_taken):
    """Create a new incident report."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Incident (allocation_id, invigilator_id, incident_type, description, action_taken) "
            "VALUES (%s, %s, %s, %s, %s)",
            (allocation_id, invigilator_id, incident_type, description, action_taken)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()


def get_incidents_for_invigilator(invigilator_id):
    """Get all incidents created by this invigilator."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT inc.incident_id, inc.incident_type, inc.description,
                   inc.action_taken, inc.incident_time,
                   st.registration_no, st.name AS student_name,
                   sub.subject_code, e.exam_type, se.seat_number
            FROM Incident inc
            JOIN SeatAllocation sa ON inc.allocation_id = sa.allocation_id
            JOIN Student st ON sa.student_id = st.student_id
            JOIN Exam e ON sa.exam_id = e.exam_id
            JOIN Subject sub ON e.subject_id = sub.subject_id
            JOIN Seat se ON sa.seat_id = se.seat_id
            WHERE inc.invigilator_id = %s
            ORDER BY inc.incident_time DESC
        ''', (invigilator_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_all_incidents():
    """Admin: Get all incidents."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT inc.incident_id, inc.incident_type, inc.description,
                   inc.action_taken, inc.incident_time,
                   st.registration_no, st.name AS student_name,
                   sub.subject_code, sub.subject_name, e.exam_type,
                   se.seat_number, r.building, r.room_number,
                   inv.name AS invigilator_name
            FROM Incident inc
            JOIN SeatAllocation sa ON inc.allocation_id = sa.allocation_id
            JOIN Student st ON sa.student_id = st.student_id
            JOIN Exam e ON sa.exam_id = e.exam_id
            JOIN Subject sub ON e.subject_id = sub.subject_id
            JOIN Seat se ON sa.seat_id = se.seat_id
            JOIN ExamRoom r ON e.room_id = r.room_id
            JOIN Invigilator inv ON inc.invigilator_id = inv.invigilator_id
            ORDER BY inc.incident_time DESC
        ''')
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


# ══════════════════════════════════════════════
#  STAGE 4: ENHANCED DASHBOARD QUERIES
# ══════════════════════════════════════════════

def get_admin_dashboard_full():
    """
    Enhanced admin dashboard stats with chart data.
    Returns a dict with stat cards + chart data arrays.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        stats = {}

        # ── Stat Cards (Consolidated into 1 network round-trip) ──
        cursor.execute('''
            SELECT 
                (SELECT COUNT(*) FROM Student) AS total_students,
                (SELECT COUNT(*) FROM Exam WHERE status IN ('Scheduled', 'Ongoing')) AS active_exams,
                (SELECT COUNT(*) FROM ExamRoom) AS total_rooms,
                (SELECT COUNT(*) FROM AIAlert WHERE status = 'Pending') AS pending_alerts,
                (SELECT COUNT(*) FROM Incident) AS total_incidents,
                COALESCE(SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END), 0) AS present,
                COALESCE(SUM(CASE WHEN status='Absent'  THEN 1 ELSE 0 END), 0) AS absent,
                COALESCE(SUM(CASE WHEN status='Late'    THEN 1 ELSE 0 END), 0) AS late,
                COUNT(*) AS total_attendance
            FROM Attendance
        ''')
        row = cursor.fetchone() or {}
        stats['total_students'] = row.get('total_students', 0)
        stats['active_exams'] = row.get('active_exams', 0)
        stats['total_rooms'] = row.get('total_rooms', 0)
        stats['pending_alerts'] = row.get('pending_alerts', 0)
        stats['total_incidents'] = row.get('total_incidents', 0)

        present = int(row.get('present', 0))
        absent = int(row.get('absent', 0))
        late = int(row.get('late', 0))
        total_att = int(row.get('total_attendance', 0))
        stats['attendance'] = {
            'present': present,
            'absent': absent,
            'late': late,
            'total': total_att
        }
        stats['attendance_pct'] = float(round(((present + late) / total_att) * 100, 1)) if total_att > 0 else 0.0

        # ── Chart Data: Attendance by Exam ──
        cursor.execute('''
            SELECT CONCAT(sub.subject_code, ' ', e.exam_type) AS label,
                   COALESCE(SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END), 0) AS present,
                   COALESCE(SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END), 0) AS absent,
                   COALESCE(SUM(CASE WHEN a.status = 'Late' THEN 1 ELSE 0 END), 0) AS late
            FROM Exam e
            JOIN Subject sub ON e.subject_id = sub.subject_id
            LEFT JOIN SeatAllocation sa ON e.exam_id = sa.exam_id AND sa.allocation_status = 'Allocated'
            LEFT JOIN Attendance a ON sa.allocation_id = a.allocation_id
            GROUP BY e.exam_id, sub.subject_code, e.exam_type
            ORDER BY e.exam_date DESC
            LIMIT 8
        ''')
        stats['attendance_by_exam'] = cursor.fetchall()

        # ── Chart Data: Alerts by Type ──
        cursor.execute('''
            SELECT alert_type, COUNT(*) AS cnt
            FROM AIAlert
            GROUP BY alert_type
        ''')
        stats['alerts_by_type'] = cursor.fetchall()

        return stats
    finally:
        cursor.close()
        conn.close()


def get_invigilator_dashboard_full(invigilator_id):
    """Enhanced invigilator dashboard stats."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        stats = {}

        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM Exam WHERE invigilator_id = %s AND status IN ('Scheduled','Ongoing')",
            (invigilator_id,)
        )
        stats['assigned_exams'] = cursor.fetchone()['cnt']

        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM Exam WHERE invigilator_id = %s AND exam_date = CURDATE()",
            (invigilator_id,)
        )
        stats['today_exams'] = cursor.fetchone()['cnt']

        cursor.execute('''
            SELECT COUNT(*) AS cnt FROM AIAlert al
            JOIN SeatAllocation sa ON al.allocation_id = sa.allocation_id
            JOIN Exam e ON sa.exam_id = e.exam_id
            WHERE e.invigilator_id = %s AND al.status = 'Pending'
        ''', (invigilator_id,))
        stats['pending_alerts'] = cursor.fetchone()['cnt']

        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM Incident WHERE invigilator_id = %s",
            (invigilator_id,)
        )
        stats['total_incidents'] = cursor.fetchone()['cnt']

        return stats
    finally:
        cursor.close()
        conn.close()

