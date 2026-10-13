import pytest
from app.database import get_db_connection

@pytest.fixture(autouse=True)
def cleanup_test_artifacts():
    def clean():
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ExamRegistration WHERE exam_id = 6")
            cursor.execute("DELETE FROM ExamRoom WHERE room_number = 'T101'")
            cursor.execute("DELETE FROM Subject WHERE subject_code IN ('TEST101', 'TEST102')")
            cursor.execute("DELETE FROM Department WHERE department_code IN ('TST', 'T2')")
            conn.commit()
            cursor.close()
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
    
    clean()
    yield
    clean()

