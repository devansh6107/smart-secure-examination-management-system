-- ============================================================
-- TRIGGERS
-- ============================================================
-- Run AFTER schema.sql:
--   mysql -u root -p exam_management_db < sql/triggers.sql
-- ============================================================

USE exam_management_db;

DELIMITER //

-- ────────────────────────────────────────────────────────────
-- TRIGGER 1: trg_after_allocation_cancel
-- When a seat allocation is cancelled, automatically mark
-- the corresponding attendance as 'Absent' if it exists.
--
-- Demonstrates: AFTER UPDATE trigger, conditional logic
-- ────────────────────────────────────────────────────────────
CREATE TRIGGER trg_after_allocation_cancel
AFTER UPDATE ON SeatAllocation
FOR EACH ROW
BEGIN
    IF NEW.allocation_status = 'Cancelled' AND OLD.allocation_status != 'Cancelled' THEN
        UPDATE Attendance
        SET status = 'Absent', check_in_time = NULL
        WHERE allocation_id = NEW.allocation_id;
    END IF;
END //

-- ────────────────────────────────────────────────────────────
-- TRIGGER 2: trg_before_exam_registration
-- Prevents registering for an exam that is already Cancelled
-- or Completed.
--
-- Demonstrates: BEFORE INSERT trigger, validation, SIGNAL
-- ────────────────────────────────────────────────────────────
CREATE TRIGGER trg_before_exam_registration
BEFORE INSERT ON ExamRegistration
FOR EACH ROW
BEGIN
    DECLARE v_exam_status VARCHAR(20);

    SELECT status INTO v_exam_status
    FROM Exam WHERE exam_id = NEW.exam_id;

    IF v_exam_status IN ('Cancelled', 'Completed') THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot register for a cancelled or completed exam.';
    END IF;
END //

DELIMITER ;

-- ============================================================
-- END OF TRIGGERS
-- ============================================================
