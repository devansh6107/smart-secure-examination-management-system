-- ============================================================
-- VIEWS — Pre-built query perspectives for the application
-- ============================================================
-- Run AFTER schema.sql:
--   mysql -u root -p exam_management_db < sql/views.sql
-- ============================================================

USE exam_management_db;

-- ────────────────────────────────────────────────────────────
-- VIEW 1: vw_exam_details
-- Flattened exam info with subject name, room, invigilator.
-- Demonstrates: INNER JOIN across 4 tables
-- ────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_exam_details AS
SELECT
    e.exam_id,
    sub.subject_code,
    sub.subject_name,
    e.exam_date,
    e.start_time,
    e.end_time,
    e.exam_type,
    e.semester,
    e.academic_year,
    e.status,
    CONCAT(r.building, ' - ', r.room_number) AS room,
    r.capacity,
    inv.name AS invigilator_name,
    inv.employee_id
FROM Exam e
INNER JOIN Subject sub    ON e.subject_id     = sub.subject_id
INNER JOIN ExamRoom r     ON e.room_id        = r.room_id
INNER JOIN Invigilator inv ON e.invigilator_id = inv.invigilator_id;

-- ────────────────────────────────────────────────────────────
-- VIEW 2: vw_student_allocation
-- Shows each student's seat allocation with room and exam info.
-- Demonstrates: JOIN across 5 tables
-- ────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_student_allocation AS
SELECT
    s.registration_no,
    s.name AS student_name,
    sub.subject_name,
    e.exam_date,
    e.start_time,
    e.exam_type,
    CONCAT(r.building, ' - ', r.room_number) AS room,
    se.seat_number,
    sa.allocation_status
FROM SeatAllocation sa
INNER JOIN Student s    ON sa.student_id = s.student_id
INNER JOIN Exam e       ON sa.exam_id    = e.exam_id
INNER JOIN Subject sub  ON e.subject_id  = sub.subject_id
INNER JOIN ExamRoom r   ON e.room_id     = r.room_id
INNER JOIN Seat se      ON sa.seat_id    = se.seat_id;

-- ────────────────────────────────────────────────────────────
-- VIEW 3: vw_alert_summary
-- AI alerts with student and exam context.
-- Demonstrates: JOIN + enum columns
-- ────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_alert_summary AS
SELECT
    a.alert_id,
    s.registration_no,
    s.name AS student_name,
    sub.subject_name,
    e.exam_date,
    se.seat_number,
    a.alert_type,
    a.confidence,
    a.alert_time,
    a.status AS alert_status
FROM AIAlert a
INNER JOIN SeatAllocation sa ON a.allocation_id  = sa.allocation_id
INNER JOIN Student s         ON sa.student_id    = s.student_id
INNER JOIN Exam e            ON sa.exam_id       = e.exam_id
INNER JOIN Subject sub       ON e.subject_id     = sub.subject_id
INNER JOIN Seat se           ON sa.seat_id       = se.seat_id;

-- ────────────────────────────────────────────────────────────
-- VIEW 4: vw_attendance_report
-- Attendance records with student, exam, and verifier info.
-- Demonstrates: LEFT JOIN (verified_by can be NULL)
-- ────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW vw_attendance_report AS
SELECT
    att.attendance_id,
    s.registration_no,
    s.name AS student_name,
    sub.subject_name,
    e.exam_date,
    e.exam_type,
    att.check_in_time,
    att.status AS attendance_status,
    inv.name AS verified_by_name
FROM Attendance att
INNER JOIN SeatAllocation sa ON att.allocation_id  = sa.allocation_id
INNER JOIN Student s         ON sa.student_id      = s.student_id
INNER JOIN Exam e            ON sa.exam_id         = e.exam_id
INNER JOIN Subject sub       ON e.subject_id       = sub.subject_id
LEFT  JOIN Invigilator inv   ON att.verified_by    = inv.invigilator_id;

-- ============================================================
-- END OF VIEWS
-- ============================================================
