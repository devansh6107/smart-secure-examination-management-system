-- ============================================================
-- REPRESENTATIVE QUERIES FOR DBMS DEMONSTRATION & VIVA
-- ============================================================
-- This file contains academic queries demonstrating joins, 
-- subqueries, aggregate functions, GROUP BY, and HAVING.

-- ────────────────────────────────────────────────────────────
-- 1. Students registered for each exam (JOINs)
-- ────────────────────────────────────────────────────────────
SELECT 
    e.exam_type, sub.subject_name, s.name, s.registration_no
FROM ExamRegistration er
JOIN Exam e ON er.exam_id = e.exam_id
JOIN Subject sub ON e.subject_id = sub.subject_id
JOIN Student s ON er.student_id = s.student_id
ORDER BY e.exam_date, s.registration_no;


-- ────────────────────────────────────────────────────────────
-- 2. Students without attendance in an allocated exam (SUBQUERY)
-- ────────────────────────────────────────────────────────────
SELECT 
    s.name, s.registration_no, sub.subject_code, sa.seat_id
FROM SeatAllocation sa
JOIN Student s ON sa.student_id = s.student_id
JOIN Exam e ON sa.exam_id = e.exam_id
JOIN Subject sub ON e.subject_id = sub.subject_id
WHERE sa.allocation_status = 'Allocated'
  AND sa.allocation_id NOT IN (
      SELECT allocation_id FROM Attendance
  );


-- ────────────────────────────────────────────────────────────
-- 3. Attendance percentage per exam (GROUP BY, Aggregate functions)
-- ────────────────────────────────────────────────────────────
SELECT 
    e.exam_id,
    sub.subject_code,
    e.exam_type,
    COUNT(sa.allocation_id) AS total_allocated,
    SUM(CASE WHEN a.status IN ('Present', 'Late') THEN 1 ELSE 0 END) AS total_present,
    ROUND((SUM(CASE WHEN a.status IN ('Present', 'Late') THEN 1 ELSE 0 END) / COUNT(sa.allocation_id)) * 100, 2) AS attendance_percentage
FROM Exam e
JOIN Subject sub ON e.subject_id = sub.subject_id
JOIN SeatAllocation sa ON e.exam_id = sa.exam_id AND sa.allocation_status = 'Allocated'
LEFT JOIN Attendance a ON sa.allocation_id = a.allocation_id
GROUP BY e.exam_id, sub.subject_code, e.exam_type;


-- ────────────────────────────────────────────────────────────
-- 4. Number of AI alerts per exam (GROUP BY)
-- ────────────────────────────────────────────────────────────
SELECT 
    sub.subject_code, e.exam_type, COUNT(al.alert_id) AS total_alerts
FROM Exam e
JOIN Subject sub ON e.subject_id = sub.subject_id
JOIN SeatAllocation sa ON e.exam_id = sa.exam_id
JOIN AIAlert al ON sa.allocation_id = al.allocation_id
GROUP BY e.exam_id, sub.subject_code, e.exam_type
ORDER BY total_alerts DESC;


-- ────────────────────────────────────────────────────────────
-- 5. Exams with highest alert count (GROUP BY, HAVING)
-- Identifies exams that had more than 2 AI alerts.
-- ────────────────────────────────────────────────────────────
SELECT 
    sub.subject_code, e.exam_type, COUNT(al.alert_id) AS alert_count
FROM Exam e
JOIN Subject sub ON e.subject_id = sub.subject_id
JOIN SeatAllocation sa ON e.exam_id = sa.exam_id
JOIN AIAlert al ON sa.allocation_id = al.allocation_id
GROUP BY e.exam_id, sub.subject_code, e.exam_type
HAVING alert_count > 2
ORDER BY alert_count DESC;


-- ────────────────────────────────────────────────────────────
-- 6. Students with multiple authentication attempts (GROUP BY, HAVING)
-- ────────────────────────────────────────────────────────────
SELECT 
    s.name, s.registration_no, COUNT(auth.auth_id) AS attempt_count
FROM Authentication auth
JOIN SeatAllocation sa ON auth.allocation_id = sa.allocation_id
JOIN Student s ON sa.student_id = s.student_id
GROUP BY sa.allocation_id, s.name, s.registration_no
HAVING attempt_count > 1;


-- ────────────────────────────────────────────────────────────
-- 7. Exam Rooms with utilization statistics (JOIN, GROUP BY)
-- ────────────────────────────────────────────────────────────
SELECT 
    r.building, r.room_number, r.capacity,
    COUNT(s.seat_id) AS physical_seats
FROM ExamRoom r
LEFT JOIN Seat s ON r.room_id = s.room_id
GROUP BY r.room_id, r.building, r.room_number, r.capacity;


-- ────────────────────────────────────────────────────────────
-- 8. Incidents by Invigilator (Aggregate)
-- ────────────────────────────────────────────────────────────
SELECT 
    inv.name, inv.employee_id, COUNT(inc.incident_id) AS incident_count
FROM Invigilator inv
LEFT JOIN Incident inc ON inv.invigilator_id = inc.invigilator_id
GROUP BY inv.invigilator_id, inv.name, inv.employee_id
ORDER BY incident_count DESC;


-- ────────────────────────────────────────────────────────────
-- 9. Testing the View (vw_exam_summary)
-- ────────────────────────────────────────────────────────────
SELECT * FROM vw_exam_summary;


-- ────────────────────────────────────────────────────────────
-- 10. Testing the Stored Procedure (sp_reallocate_student)
-- Note: Replace 1, 10 with actual allocation_id and seat_id.
-- ────────────────────────────────────────────────────────────
-- CALL sp_reallocate_student(1, 10);
-- SELECT * FROM AuditLog;
