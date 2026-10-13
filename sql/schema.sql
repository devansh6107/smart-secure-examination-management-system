-- ============================================================
-- SMART & SECURE AI-BASED EXAMINATION MANAGEMENT SYSTEM
-- Database Schema — All 14 Tables
-- ============================================================
-- Run this file to create the database and all tables:
--   mysql -u root -p < sql/schema.sql
-- ============================================================

DROP DATABASE IF EXISTS exam_management_db;
CREATE DATABASE exam_management_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_general_ci;

USE exam_management_db;

-- ────────────────────────────────────────────────────────────
-- TABLE 1: User
-- Central authentication table for all three roles.
-- Relationship: 1-to-1 with Student, 1-to-1 with Invigilator
-- ────────────────────────────────────────────────────────────
CREATE TABLE User (
    user_id       INT             PRIMARY KEY AUTO_INCREMENT,
    username      VARCHAR(50)     UNIQUE NOT NULL,
    email         VARCHAR(100)    UNIQUE NOT NULL,
    password_hash VARCHAR(255)    NOT NULL,
    role          ENUM('ADMIN', 'STUDENT', 'INVIGILATOR') NOT NULL,
    is_active     BOOLEAN         DEFAULT TRUE,
    created_at    TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ────────────────────────────────────────────────────────────
-- TABLE 2: Department
-- Academic departments (CSE, ECE, etc.)
-- Relationship: 1-to-many with Student
-- ────────────────────────────────────────────────────────────
CREATE TABLE Department (
    department_id   INT             PRIMARY KEY AUTO_INCREMENT,
    department_name VARCHAR(100)    UNIQUE NOT NULL,
    department_code VARCHAR(10)     UNIQUE NOT NULL
) ENGINE=InnoDB;

-- ────────────────────────────────────────────────────────────
-- TABLE 3: Student
-- One-to-one with User (each student has exactly one login).
-- Many-to-one with Department.
-- ────────────────────────────────────────────────────────────
CREATE TABLE Student (
    student_id      INT             PRIMARY KEY AUTO_INCREMENT,
    user_id         INT             UNIQUE NOT NULL,
    registration_no VARCHAR(20)     UNIQUE NOT NULL,
    name            VARCHAR(100)    NOT NULL,
    department_id   INT             NOT NULL,
    year            TINYINT         NOT NULL,
    section         VARCHAR(5)      NOT NULL,
    phone           VARCHAR(15),

    CONSTRAINT fk_student_user
        FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_student_dept
        FOREIGN KEY (department_id) REFERENCES Department(department_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ────────────────────────────────────────────────────────────
-- TABLE 4: Invigilator
-- One-to-one with User.
-- ────────────────────────────────────────────────────────────
CREATE TABLE Invigilator (
    invigilator_id  INT             PRIMARY KEY AUTO_INCREMENT,
    user_id         INT             UNIQUE NOT NULL,
    employee_id     VARCHAR(20)     UNIQUE NOT NULL,
    name            VARCHAR(100)    NOT NULL,
    phone           VARCHAR(15),
    designation     VARCHAR(50),

    CONSTRAINT fk_invigilator_user
        FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ────────────────────────────────────────────────────────────
-- TABLE 5: Subject
-- Subjects/courses that exams are conducted for.
-- Relationship: 1-to-many with Exam
-- ────────────────────────────────────────────────────────────
CREATE TABLE Subject (
    subject_id   INT             PRIMARY KEY AUTO_INCREMENT,
    subject_code VARCHAR(20)     UNIQUE NOT NULL,
    subject_name VARCHAR(100)    NOT NULL,
    credits      TINYINT         NOT NULL
) ENGINE=InnoDB;

-- ────────────────────────────────────────────────────────────
-- TABLE 6: ExamRoom
-- Physical rooms where exams are held.
-- Relationship: 1-to-many with Exam, 1-to-many with Seat
-- ────────────────────────────────────────────────────────────
CREATE TABLE ExamRoom (
    room_id     INT             PRIMARY KEY AUTO_INCREMENT,
    room_number VARCHAR(20)     NOT NULL,
    building    VARCHAR(50)     NOT NULL,
    floor       INT             NOT NULL,
    capacity    INT             NOT NULL,

    UNIQUE KEY uq_room (building, room_number)
) ENGINE=InnoDB;

-- ────────────────────────────────────────────────────────────
-- TABLE 7: Exam
-- Each exam is for one subject, in one room, with one invigilator.
-- CHECK constraint ensures end_time > start_time.
-- ────────────────────────────────────────────────────────────
CREATE TABLE Exam (
    exam_id        INT          PRIMARY KEY AUTO_INCREMENT,
    subject_id     INT          NOT NULL,
    room_id        INT          NOT NULL,
    invigilator_id INT          NOT NULL,
    exam_date      DATE         NOT NULL,
    start_time     TIME         NOT NULL,
    end_time       TIME         NOT NULL,
    semester       ENUM('Fall', 'Winter')                       NOT NULL,
    academic_year  YEAR         NOT NULL,
    exam_type      ENUM('CAT1', 'CAT2', 'FAT', 'LAB')          NOT NULL,
    status         ENUM('Scheduled', 'Ongoing', 'Completed', 'Cancelled')
                                DEFAULT 'Scheduled',

    CONSTRAINT fk_exam_subject
        FOREIGN KEY (subject_id) REFERENCES Subject(subject_id) ON DELETE RESTRICT,
    CONSTRAINT fk_exam_room
        FOREIGN KEY (room_id) REFERENCES ExamRoom(room_id) ON DELETE RESTRICT,
    CONSTRAINT fk_exam_invigilator
        FOREIGN KEY (invigilator_id) REFERENCES Invigilator(invigilator_id) ON DELETE RESTRICT,

    CONSTRAINT chk_exam_time CHECK (end_time > start_time)
) ENGINE=InnoDB;

-- ────────────────────────────────────────────────────────────
-- TABLE 8: ExamRegistration
-- Many-to-many bridge between Student and Exam.
-- A student can register for many exams; an exam has many students.
-- UNIQUE(student_id, exam_id) prevents duplicate registrations.
-- ────────────────────────────────────────────────────────────
CREATE TABLE ExamRegistration (
    registration_id     INT         PRIMARY KEY AUTO_INCREMENT,
    student_id          INT         NOT NULL,
    exam_id             INT         NOT NULL,
    registration_date   DATETIME    DEFAULT CURRENT_TIMESTAMP,
    registration_status ENUM('Registered', 'Cancelled', 'Completed')
                                    DEFAULT 'Registered',

    UNIQUE KEY uq_student_exam (student_id, exam_id),

    CONSTRAINT fk_reg_student
        FOREIGN KEY (student_id) REFERENCES Student(student_id) ON DELETE CASCADE,
    CONSTRAINT fk_reg_exam
        FOREIGN KEY (exam_id) REFERENCES Exam(exam_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ────────────────────────────────────────────────────────────
-- TABLE 9: Seat
-- Individual seats within each exam room.
-- UNIQUE(room_id, seat_number) prevents duplicate seat labels.
-- ────────────────────────────────────────────────────────────
CREATE TABLE Seat (
    seat_id     INT             PRIMARY KEY AUTO_INCREMENT,
    room_id     INT             NOT NULL,
    seat_number VARCHAR(10)     NOT NULL,
    row_no      INT             NOT NULL,
    column_no   INT             NOT NULL,

    UNIQUE KEY uq_room_seat (room_id, seat_number),

    CONSTRAINT fk_seat_room
        FOREIGN KEY (room_id) REFERENCES ExamRoom(room_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ────────────────────────────────────────────────────────────
-- TABLE 10: SeatAllocation
-- Assigns a specific seat to a specific student for a specific exam.
-- Two UNIQUE constraints:
--   (student_id, exam_id) — a student gets one seat per exam
--   (seat_id, exam_id)    — a seat is assigned to one student per exam
-- ────────────────────────────────────────────────────────────
CREATE TABLE SeatAllocation (
    allocation_id     INT         PRIMARY KEY AUTO_INCREMENT,
    student_id        INT         NOT NULL,
    exam_id           INT         NOT NULL,
    seat_id           INT         NOT NULL,
    allocated_at      TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    allocation_status ENUM('Allocated', 'Reallocated', 'Cancelled')
                                  DEFAULT 'Allocated',

    UNIQUE KEY uq_student_exam_alloc (student_id, exam_id),
    UNIQUE KEY uq_seat_exam_alloc    (seat_id, exam_id),

    CONSTRAINT fk_alloc_student
        FOREIGN KEY (student_id) REFERENCES Student(student_id) ON DELETE CASCADE,
    CONSTRAINT fk_alloc_exam
        FOREIGN KEY (exam_id) REFERENCES Exam(exam_id) ON DELETE CASCADE,
    CONSTRAINT fk_alloc_seat
        FOREIGN KEY (seat_id) REFERENCES Seat(seat_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ────────────────────────────────────────────────────────────
-- TABLE 11: Attendance
-- One attendance record per allocation (1-to-1 with SeatAllocation).
-- UNIQUE on allocation_id enforces this.
-- ────────────────────────────────────────────────────────────
CREATE TABLE Attendance (
    attendance_id   INT         PRIMARY KEY AUTO_INCREMENT,
    allocation_id   INT         UNIQUE NOT NULL,
    check_in_time   DATETIME,
    status          ENUM('Present', 'Absent', 'Late') DEFAULT 'Present',
    verified_by     INT         NULL,

    CONSTRAINT fk_att_allocation
        FOREIGN KEY (allocation_id) REFERENCES SeatAllocation(allocation_id) ON DELETE CASCADE,
    CONSTRAINT fk_att_invigilator
        FOREIGN KEY (verified_by) REFERENCES Invigilator(invigilator_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ────────────────────────────────────────────────────────────
-- TABLE 12: Authentication
-- Verification attempts (QR, Face, Manual) for a student.
-- allocation_id is NOT UNIQUE — a student may have multiple attempts.
-- ────────────────────────────────────────────────────────────
CREATE TABLE Authentication (
    auth_id             INT         PRIMARY KEY AUTO_INCREMENT,
    allocation_id       INT         NOT NULL,
    method              ENUM('QR', 'Face', 'Manual') NOT NULL,
    verification_status ENUM('Success', 'Failed')    NOT NULL,
    verified_at         TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_auth_allocation
        FOREIGN KEY (allocation_id) REFERENCES SeatAllocation(allocation_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ────────────────────────────────────────────────────────────
-- TABLE 13: AIAlert
-- Simulated AI proctoring alerts.
-- confidence is DECIMAL(5,2) representing 0.00 – 1.00.
-- ────────────────────────────────────────────────────────────
CREATE TABLE AIAlert (
    alert_id    INT             PRIMARY KEY AUTO_INCREMENT,
    allocation_id INT           NOT NULL,
    alert_type  ENUM('Phone Detected', 'Multiple Faces', 'Suspicious Movement') NOT NULL,
    confidence  DECIMAL(5,2),
    alert_time  TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    status      ENUM('Pending', 'Reviewed', 'Ignored') DEFAULT 'Pending',

    CONSTRAINT fk_alert_allocation
        FOREIGN KEY (allocation_id) REFERENCES SeatAllocation(allocation_id) ON DELETE CASCADE,
    CONSTRAINT chk_confidence CHECK (confidence >= 0 AND confidence <= 1)
) ENGINE=InnoDB;

-- ────────────────────────────────────────────────────────────
-- TABLE 14: Incident
-- Manual incident reports filed by invigilators.
-- ────────────────────────────────────────────────────────────
CREATE TABLE Incident (
    incident_id    INT             PRIMARY KEY AUTO_INCREMENT,
    allocation_id  INT             NOT NULL,
    invigilator_id INT             NOT NULL,
    incident_type  VARCHAR(50)     NOT NULL,
    description    TEXT,
    action_taken   TEXT,
    incident_time  TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_inc_allocation
        FOREIGN KEY (allocation_id) REFERENCES SeatAllocation(allocation_id) ON DELETE CASCADE,
    CONSTRAINT fk_inc_invigilator
        FOREIGN KEY (invigilator_id) REFERENCES Invigilator(invigilator_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ────────────────────────────────────────────────────────────
-- TABLE 15: AuditLog (For Trigger Demonstration)
-- ────────────────────────────────────────────────────────────
CREATE TABLE AuditLog (
    audit_id      INT             PRIMARY KEY AUTO_INCREMENT,
    action_type   VARCHAR(50)     NOT NULL,
    description   TEXT            NOT NULL,
    created_at    TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================================
-- ADVANCED DBMS FEATURES (For Demonstration & Viva)
-- ============================================================

-- ────────────────────────────────────────────────────────────
-- 1. VIEW: vw_exam_summary
-- Aggregates exam details, allocated students, and alert counts.
-- ────────────────────────────────────────────────────────────
CREATE VIEW vw_exam_summary AS
SELECT 
    e.exam_id,
    sub.subject_code,
    sub.subject_name,
    e.exam_type,
    e.exam_date,
    r.building,
    r.room_number,
    COUNT(DISTINCT sa.allocation_id) AS total_allocated,
    COUNT(DISTINCT a.alert_id) AS total_alerts
FROM Exam e
JOIN Subject sub ON e.subject_id = sub.subject_id
JOIN ExamRoom r ON e.room_id = r.room_id
LEFT JOIN SeatAllocation sa ON e.exam_id = sa.exam_id AND sa.allocation_status = 'Allocated'
LEFT JOIN AIAlert a ON sa.allocation_id = a.allocation_id
GROUP BY e.exam_id, sub.subject_code, sub.subject_name, e.exam_type, e.exam_date, r.building, r.room_number;

-- ────────────────────────────────────────────────────────────
-- 2. STORED PROCEDURE & TRANSACTION: sp_reallocate_student
-- Safely moves a student to a new seat within the same exam.
-- ────────────────────────────────────────────────────────────
DELIMITER //

CREATE PROCEDURE sp_reallocate_student(
    IN p_allocation_id INT,
    IN p_new_seat_id INT
)
BEGIN
    DECLARE v_exam_id INT;
    DECLARE v_room_id INT;
    DECLARE v_seat_room_id INT;
    DECLARE v_is_occupied INT;

    -- Custom exception for errors
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- Get exam and room for current allocation
    SELECT sa.exam_id, e.room_id INTO v_exam_id, v_room_id
    FROM SeatAllocation sa
    JOIN Exam e ON sa.exam_id = e.exam_id
    WHERE sa.allocation_id = p_allocation_id FOR UPDATE;

    -- Get room of the target seat
    SELECT room_id INTO v_seat_room_id
    FROM Seat
    WHERE seat_id = p_new_seat_id;

    -- Validate seat belongs to the correct room
    IF v_room_id != v_seat_room_id THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Seat does not belong to the exam room';
    END IF;

    -- Check if new seat is already allocated for this exam
    SELECT COUNT(*) INTO v_is_occupied
    FROM SeatAllocation
    WHERE exam_id = v_exam_id AND seat_id = p_new_seat_id AND allocation_status = 'Allocated';

    IF v_is_occupied > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Seat is already occupied for this exam';
    END IF;

    -- Update allocation
    UPDATE SeatAllocation
    SET seat_id = p_new_seat_id, allocation_status = 'Reallocated'
    WHERE allocation_id = p_allocation_id;

    -- Log the action
    INSERT INTO AuditLog (action_type, description)
    VALUES ('REALLOCATION', CONCAT('Allocation ', p_allocation_id, ' moved to seat ', p_new_seat_id));

    COMMIT;
END //

DELIMITER ;

-- ────────────────────────────────────────────────────────────
-- 3. TRIGGER: trg_after_incident_insert
-- Automatically logs high-severity incidents to the audit log.
-- ────────────────────────────────────────────────────────────
DELIMITER //

CREATE TRIGGER trg_after_incident_insert
AFTER INSERT ON Incident
FOR EACH ROW
BEGIN
    IF NEW.incident_type = 'Cheating' OR NEW.incident_type = 'Impersonation' THEN
        INSERT INTO AuditLog (action_type, description)
        VALUES ('HIGH_RISK_INCIDENT', CONCAT('High severity incident (', NEW.incident_type, ') filed for allocation ', NEW.allocation_id));
    END IF;
END //

DELIMITER ;

-- ============================================================
-- END OF SCHEMA
-- 15 tables, 1 view, 1 procedure, 1 trigger created.
-- ============================================================

