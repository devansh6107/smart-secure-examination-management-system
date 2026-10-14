"""
Database Expansion Script.
Updates registration numbers to remove '22' and use '23', '24', '25', '26'
with program codes: BCE, BYB, BME, BIT, BEC, BEE.
Expands Students, Teachers (Invigilators), and Exams.
"""

import sys
import os
import random
from werkzeug.security import generate_password_hash
from app.database import get_db_connection

def expand_db():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    print("=" * 60)
    print("STARTING DATABASE EXPANSION")
    print("=" * 60)

    # 1. Update existing 22-series students to 23/24/25/26
    reg_updates = [
        ('22BCE1001', '23BCE1001'),
        ('22BCE1002', '23BCE1002'),
        ('22BCE1003', '24BCE1003'),
        ('22BEC1001', '25BEC1001'),
        ('22BME1001', '26BME1001'),
    ]
    for old_reg, new_reg in reg_updates:
        cursor.execute("UPDATE Student SET registration_no = %s WHERE registration_no = %s", (new_reg, old_reg))
        if cursor.rowcount > 0:
            print(f"  • Migrated {old_reg} -> {new_reg}")
            
    # Also update any other 22-prefixed student if any
    cursor.execute("SELECT student_id, registration_no FROM Student WHERE registration_no LIKE '22%'")
    remaining_22 = cursor.fetchall()
    for s in remaining_22:
        new_reg = '23' + s['registration_no'][2:]
        cursor.execute("UPDATE Student SET registration_no = %s WHERE student_id = %s", (new_reg, s['student_id']))
        print(f"  • Migrated remaining {s['registration_no']} -> {new_reg}")
    conn.commit()

    # 2. Ensure Departments exist
    departments = [
        ('Computer Science and Engineering', 'CSE'),
        ('Electronics and Communication', 'ECE'),
        ('Mechanical Engineering', 'MECH'),
        ('Information Technology', 'IT'),
        ('Electrical and Electronics Engineering', 'EEE'),
        ('Biotechnology', 'BIO'),
    ]
    for dept_name, dept_code in departments:
        cursor.execute("""
            INSERT INTO Department (department_name, department_code)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE department_name = VALUES(department_name)
        """, (dept_name, dept_code))
    conn.commit()
    
    # Map department codes to department_ids
    cursor.execute("SELECT department_id, department_code FROM Department")
    dept_map = {row['department_code']: row['department_id'] for row in cursor.fetchall()}

    # 3. Add more Teachers (Invigilators)
    # Common password for all demo invigilators: 'invig123'
    invig_pwd_hash = generate_password_hash('invig123')
    
    new_invigilators = [
        ('dr.ananya', 'ananya.roy@faculty.edu', 'Dr. Ananya Roy', 'FAC004', 'Professor', '9876500004'),
        ('prof.siddharth', 'siddharth.m@faculty.edu', 'Prof. Siddharth Menon', 'FAC005', 'Associate Professor', '9876500005'),
        ('dr.kavita', 'kavita.deshmukh@faculty.edu', 'Dr. Kavita Deshmukh', 'FAC006', 'Assistant Professor', '9876500006'),
        ('dr.ramesh', 'ramesh.verma@faculty.edu', 'Dr. Ramesh Verma', 'FAC007', 'Professor', '9876500007'),
        ('prof.divya', 'divya.nair@faculty.edu', 'Prof. Divya Nair', 'FAC008', 'Associate Professor', '9876500008'),
        ('dr.alok', 'alok.chatterjee@faculty.edu', 'Dr. Alok Chatterjee', 'FAC009', 'Professor', '9876500009'),
        ('prof.swati', 'swati.pandey@faculty.edu', 'Prof. Swati Pandey', 'FAC010', 'Assistant Professor', '9876500010'),
    ]

    for username, email, full_name, emp_id, desig, phone in new_invigilators:
        # Check if user already exists
        cursor.execute("SELECT user_id FROM User WHERE username = %s OR email = %s", (username, email))
        user_row = cursor.fetchone()
        if not user_row:
            cursor.execute("""
                INSERT INTO User (username, email, password_hash, role)
                VALUES (%s, %s, %s, 'INVIGILATOR')
            """, (username, email, invig_pwd_hash))
            uid = cursor.lastrowid
        else:
            uid = user_row['user_id']

        cursor.execute("SELECT invigilator_id FROM Invigilator WHERE employee_id = %s", (emp_id,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO Invigilator (user_id, employee_id, name, designation, phone)
                VALUES (%s, %s, %s, %s, %s)
            """, (uid, emp_id, full_name, desig, phone))
            print(f"  + Added Teacher: {full_name} ({emp_id})")

    conn.commit()

    # 4. Add new Students with years 23, 24, 25, 26 and program codes BCE, BYB, BME, BIT, BEC, BEE
    student_pwd_hash = generate_password_hash('student123')
    
    # (username, email, name, reg_no, dept_code, year, section, phone)
    student_dataset = [
        # Year 23 (Final / 4th Year)
        ('rohan.verma', 'rohan.verma@student.edu', 'Rohan Verma', '23BCE1042', 'CSE', 4, 'A', '9811001042'),
        ('sneha.reddy', 'sneha.reddy@student.edu', 'Sneha Reddy', '23BIT2015', 'IT', 4, 'B', '9811002015'),
        ('kartik.iyer', 'kartik.iyer@student.edu', 'Kartik Iyer', '23BEC3088', 'ECE', 4, 'A', '9811003088'),
        ('pooja.nair', 'pooja.nair@student.edu', 'Pooja Nair', '23BEE4012', 'EEE', 4, 'B', '9811004012'),
        ('akash.sharma', 'akash.sharma@student.edu', 'Akash Sharma', '23BME5076', 'MECH', 4, 'A', '9811005076'),
        ('tanya.sen', 'tanya.sen@student.edu', 'Tanya Sen', '23BYB6024', 'BIO', 4, 'A', '9811006024'),

        # Year 24 (3rd Year)
        ('manish.pandey', 'manish.pandey@student.edu', 'Manish Pandey', '24BCE1180', 'CSE', 3, 'B', '9822001180'),
        ('deepika.joshi', 'deepika.joshi@student.edu', 'Deepika Joshi', '24BIT2190', 'IT', 3, 'A', '9822002190'),
        ('varun.malhotra', 'varun.malhotra@student.edu', 'Varun Malhotra', '24BEC3105', 'ECE', 3, 'B', '9822003105'),
        ('shruti.saxena', 'shruti.saxena@student.edu', 'Shruti Saxena', '24BEE4144', 'EEE', 3, 'A', '9822004144'),
        ('kunal.chawla', 'kunal.chawla@student.edu', 'Kunal Chawla', '24BME5133', 'MECH', 3, 'B', '9822005133'),
        ('aishwarya.rao', 'aishwarya.rao@student.edu', 'Aishwarya Rao', '24BYB6199', 'BIO', 3, 'A', '9822006199'),

        # Year 25 (2nd Year)
        ('aditya.kapoor', 'aditya.kapoor@student.edu', 'Aditya Kapoor', '25BCE1250', 'CSE', 2, 'A', '9833001250'),
        ('megha.singh', 'megha.singh@student.edu', 'Megha Singh', '25BIT2233', 'IT', 2, 'B', '9833002233'),
        ('vivek.shukla', 'vivek.shukla@student.edu', 'Vivek Shukla', '25BEC3277', 'ECE', 2, 'A', '9833003277'),
        ('simran.kaur', 'simran.kaur@student.edu', 'Simran Kaur', '25BEE4218', 'EEE', 2, 'B', '9833004218'),
        ('harsh.vardhan', 'harsh.vardhan@student.edu', 'Harsh Vardhan', '25BME5260', 'MECH', 2, 'A', '9833005260'),
        ('ananya.bose', 'ananya.bose@student.edu', 'Ananya Bose', '25BYB6285', 'BIO', 2, 'B', '9833006285'),

        # Year 26 (1st Year)
        ('ayush.mishra', 'ayush.mishra@student.edu', 'Ayush Mishra', '26BCE1310', 'CSE', 1, 'A', '9844001310'),
        ('tanvi.desai', 'tanvi.desai@student.edu', 'Tanvi Desai', '26BIT2345', 'IT', 1, 'B', '9844002345'),
        ('ishaan.gupta', 'ishaan.gupta@student.edu', 'Ishaan Gupta', '26BEC3390', 'ECE', 1, 'A', '9844003390'),
        ('ritika.roy', 'ritika.roy@student.edu', 'Ritika Roy', '26BEE4360', 'EEE', 1, 'B', '9844004360'),
        ('pranav.kulkarni', 'pranav.kulkarni@student.edu', 'Pranav Kulkarni', '26BME5315', 'MECH', 1, 'A', '9844005315'),
        ('khushi.jain', 'khushi.jain@student.edu', 'Khushi Jain', '26BYB6370', 'BIO', 1, 'B', '9844006370'),
    ]

    for username, email, full_name, reg_no, dept_code, yr, sec, phone in student_dataset:
        cursor.execute("SELECT user_id FROM User WHERE username = %s OR email = %s", (username, email))
        user_row = cursor.fetchone()
        if not user_row:
            cursor.execute("""
                INSERT INTO User (username, email, password_hash, role)
                VALUES (%s, %s, %s, 'STUDENT')
            """, (username, email, student_pwd_hash))
            uid = cursor.lastrowid
        else:
            uid = user_row['user_id']

        dept_id = dept_map.get(dept_code, 1)
        cursor.execute("SELECT student_id FROM Student WHERE registration_no = %s", (reg_no,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO Student (user_id, registration_no, name, department_id, year, section, phone)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (uid, reg_no, full_name, dept_id, yr, sec, phone))
            print(f"  + Added Student: {full_name} ({reg_no}) - Dept: {dept_code}, Year: {yr}")

    conn.commit()

    # 5. Add more Subjects for IT, EEE, and BIO
    new_subjects = [
        ('BAITE201', 'Web Technologies & Cloud Architecture', 4),
        ('BAITE302', 'Artificial Intelligence & Machine Learning', 4),
        ('BAEEE205', 'Signals, Systems and DSP', 3),
        ('BABIO101', 'Cell Biology & Genetic Engineering', 3),
        ('BABIO204', 'Bioprocess Engineering & Bioinformatics', 4),
    ]
    for sub_code, sub_name, creds in new_subjects:
        cursor.execute("""
            INSERT INTO Subject (subject_code, subject_name, credits)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE subject_name = VALUES(subject_name)
        """, (sub_code, sub_name, creds))
    conn.commit()

    # 6. Add more Exams
    # Get available subjects, rooms, and invigilators
    cursor.execute("SELECT subject_id, subject_code FROM Subject")
    subj_dict = {row['subject_code']: row['subject_id'] for row in cursor.fetchall()}

    cursor.execute("SELECT invigilator_id, employee_id FROM Invigilator")
    invig_dict = {row['employee_id']: row['invigilator_id'] for row in cursor.fetchall()}

    cursor.execute("SELECT room_id FROM ExamRoom")
    room_ids = [row['room_id'] for row in cursor.fetchall()]

    new_exams = [
        ('BAITE201', 3, 'FAC004', '2026-10-22', '09:00:00', '12:00:00', 'Fall', 2026, 'CAT1', 'Scheduled'),
        ('BAITE302', 4, 'FAC005', '2026-10-23', '14:00:00', '17:00:00', 'Fall', 2026, 'CAT1', 'Scheduled'),
        ('BAEEE205', 5, 'FAC006', '2026-10-24', '09:00:00', '11:00:00', 'Fall', 2026, 'CAT1', 'Scheduled'),
        ('BABIO101', 6, 'FAC007', '2026-10-25', '14:00:00', '17:00:00', 'Fall', 2026, 'CAT1', 'Scheduled'),
        ('BABIO204', 7, 'FAC008', '2026-10-26', '09:00:00', '12:00:00', 'Fall', 2026, 'CAT2', 'Scheduled'),
        ('BACSE202', 8, 'FAC009', '2026-11-05', '09:00:00', '12:00:00', 'Fall', 2026, 'FAT', 'Scheduled'),
        ('BAMAT205', 9, 'FAC010', '2026-11-08', '14:00:00', '17:00:00', 'Fall', 2026, 'FAT', 'Scheduled'),
    ]

    for scode, rid, emp_id, edate, stime, etime, sem, yr, etype, status in new_exams:
        sid = subj_dict.get(scode)
        iid = invig_dict.get(emp_id, 1)
        actual_room = rid if rid in room_ids else room_ids[0]

        cursor.execute("""
            SELECT exam_id FROM Exam
            WHERE subject_id = %s AND exam_date = %s AND exam_type = %s
        """, (sid, edate, etype))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO Exam (subject_id, room_id, invigilator_id, exam_date, start_time, end_time, semester, academic_year, exam_type, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (sid, actual_room, iid, edate, stime, etime, sem, yr, etype, status))
            print(f"  + Added Exam: {scode} ({etype}) on {edate} in Room {actual_room}")

    conn.commit()

    # Summary
    cursor.execute("SELECT COUNT(*) as cnt FROM Student")
    total_students = cursor.fetchone()['cnt']
    cursor.execute("SELECT COUNT(*) as cnt FROM Invigilator")
    total_teachers = cursor.fetchone()['cnt']
    cursor.execute("SELECT COUNT(*) as cnt FROM Exam")
    total_exams = cursor.fetchone()['cnt']

    print("=" * 60)
    print("EXPANSION COMPLETE!")
    print(f"  Total Students in DB: {total_students}")
    print(f"  Total Teachers in DB: {total_teachers}")
    print(f"  Total Exams in DB:    {total_exams}")
    print("=" * 60)

    cursor.close()
    conn.close()

if __name__ == '__main__':
    expand_db()
