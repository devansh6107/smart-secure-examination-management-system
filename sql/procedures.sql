-- ============================================================
-- STORED PROCEDURES
-- ============================================================
-- Run AFTER schema.sql:
--   mysql -u root -p exam_management_db < sql/procedures.sql
-- ============================================================

USE exam_management_db;

DELIMITER //

-- ────────────────────────────────────────────────────────────
-- PROCEDURE 1: sp_allocate_seats
-- Automatically allocates seats to all registered students
-- for a given exam. Uses a TRANSACTION to ensure atomicity.
--
-- Demonstrates: Cursor, Transaction, Error handling
--
-- Usage: CALL sp_allocate_seats(1);
-- ────────────────────────────────────────────────────────────
CREATE PROCEDURE sp_allocate_seats(IN p_exam_id INT)
BEGIN
    DECLARE v_room_id INT;
    DECLARE v_student_id INT;
    DECLARE v_seat_id INT;
    DECLARE v_done INT DEFAULT 0;
    DECLARE v_seat_done INT DEFAULT 0;
    DECLARE v_count INT DEFAULT 0;

    -- Cursor: all registered students who don't already have a seat
    DECLARE cur_students CURSOR FOR
        SELECT er.student_id
        FROM ExamRegistration er
        WHERE er.exam_id = p_exam_id
          AND er.registration_status = 'Registered'
          AND er.student_id NOT IN (
              SELECT sa.student_id FROM SeatAllocation sa
              WHERE sa.exam_id = p_exam_id
                AND sa.allocation_status = 'Allocated'
          );

    -- Cursor: available seats in the exam room
    DECLARE cur_seats CURSOR FOR
        SELECT s.seat_id
        FROM Seat s
        WHERE s.room_id = v_room_id
          AND s.seat_id NOT IN (
              SELECT sa.seat_id FROM SeatAllocation sa
              WHERE sa.exam_id = p_exam_id
                AND sa.allocation_status = 'Allocated'
          )
        ORDER BY s.row_no, s.column_no;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = 1;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    -- Get the room for this exam
    SELECT room_id INTO v_room_id FROM Exam WHERE exam_id = p_exam_id;

    START TRANSACTION;

    OPEN cur_students;

    student_loop: LOOP
        FETCH cur_students INTO v_student_id;
        IF v_done = 1 THEN
            LEAVE student_loop;
        END IF;

        -- Find the next available seat
        -- We re-open seat cursor approach: pick the first unallocated seat
        SET v_seat_id = NULL;
        SELECT s.seat_id INTO v_seat_id
        FROM Seat s
        WHERE s.room_id = v_room_id
          AND s.seat_id NOT IN (
              SELECT sa.seat_id FROM SeatAllocation sa
              WHERE sa.exam_id = p_exam_id
                AND sa.allocation_status = 'Allocated'
          )
        ORDER BY s.row_no, s.column_no
        LIMIT 1;

        IF v_seat_id IS NOT NULL THEN
            INSERT INTO SeatAllocation (student_id, exam_id, seat_id, allocation_status)
            VALUES (v_student_id, p_exam_id, v_seat_id, 'Allocated');
            SET v_count = v_count + 1;
        END IF;
    END LOOP;

    CLOSE cur_students;

    COMMIT;

    SELECT v_count AS seats_allocated;
END //

-- ────────────────────────────────────────────────────────────
-- PROCEDURE 2: sp_exam_report
-- Generates a summary report for a given exam.
--
-- Demonstrates: Aggregate functions, JOIN, OUT parameters
--
-- Usage: CALL sp_exam_report(1, @total, @present, @absent, @late, @alerts);
-- ────────────────────────────────────────────────────────────
CREATE PROCEDURE sp_exam_report(
    IN  p_exam_id       INT,
    OUT p_total_reg     INT,
    OUT p_present       INT,
    OUT p_absent        INT,
    OUT p_late          INT,
    OUT p_alert_count   INT
)
BEGIN
    -- Total registered students
    SELECT COUNT(*) INTO p_total_reg
    FROM ExamRegistration
    WHERE exam_id = p_exam_id AND registration_status != 'Cancelled';

    -- Attendance counts
    SELECT
        COALESCE(SUM(CASE WHEN att.status = 'Present' THEN 1 ELSE 0 END), 0),
        COALESCE(SUM(CASE WHEN att.status = 'Absent'  THEN 1 ELSE 0 END), 0),
        COALESCE(SUM(CASE WHEN att.status = 'Late'    THEN 1 ELSE 0 END), 0)
    INTO p_present, p_absent, p_late
    FROM Attendance att
    INNER JOIN SeatAllocation sa ON att.allocation_id = sa.allocation_id
    WHERE sa.exam_id = p_exam_id;

    -- AI alert count
    SELECT COUNT(*) INTO p_alert_count
    FROM AIAlert al
    INNER JOIN SeatAllocation sa ON al.allocation_id = sa.allocation_id
    WHERE sa.exam_id = p_exam_id;
END //

DELIMITER ;

-- ============================================================
-- END OF PROCEDURES
-- ============================================================
