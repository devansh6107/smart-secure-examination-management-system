"""
ProctoringService — AI Proctoring Simulator.

This service is architected as a pluggable class so that a future
OpenCV / YOLO implementation can replace the simulator without
changing any routes or templates.

Current implementation: deterministic random simulation for demo/testing.
Future implementation: real-time video analysis via OpenCV + YOLO model.
"""

import random
from app.database import get_db_connection


class ProctoringService:
    """
    Simulated AI proctoring engine.

    Methods mirror what a real AI service would expose:
      - simulate_alert()   → single alert for a specific student
      - simulate_batch()   → batch of random alerts for demo
    """

    ALERT_TYPES = ['Phone Detected', 'Suspicious Movement']

    @staticmethod
    def simulate_alert(allocation_id, alert_type, confidence=None):
        """
        Generate a single AIAlert record.

        Parameters:
            allocation_id (int): The seat allocation to flag.
            alert_type (str): One of 'Phone Detected', 'Suspicious Movement'.
            confidence (float|None): 0.00–1.00. If None, a random value in [0.50, 0.99] is used.

        Returns:
            int: The newly created alert_id.
        """
        if alert_type not in ProctoringService.ALERT_TYPES:
            raise ValueError(f"Invalid alert_type: {alert_type}")

        if confidence is None:
            confidence = round(random.uniform(0.50, 0.99), 2)
        else:
            confidence = max(0.0, min(1.0, float(confidence)))

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO AIAlert (allocation_id, alert_type, confidence, status) "
                "VALUES (%s, %s, %s, 'Pending')",
                (allocation_id, alert_type, confidence)
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def simulate_batch(exam_id, count=3):
        """
        Generate multiple random alerts for an exam (demo use).

        Picks `count` random allocated students from the exam and
        generates one random alert for each.

        Parameters:
            exam_id (int): The exam to generate alerts for.
            count (int): Number of alerts to generate.

        Returns:
            list[int]: List of created alert_ids.
        """
        conn = get_db_connection()
        try:
            cursor = conn.cursor(dictionary=True)

            # Fetch all active allocations for this exam
            cursor.execute(
                "SELECT allocation_id FROM SeatAllocation "
                "WHERE exam_id = %s AND allocation_status = 'Allocated'",
                (exam_id,)
            )
            allocations = cursor.fetchall()

            if not allocations:
                raise Exception("No allocated students found for this exam. Allocate seats first.")

            # Pick up to `count` random allocations (with replacement if count > len)
            picks = random.choices(allocations, k=min(count, len(allocations)))

            alert_ids = []
            for pick in picks:
                alert_type = random.choice(ProctoringService.ALERT_TYPES)
                alert_id = ProctoringService.simulate_alert(
                    pick['allocation_id'], alert_type
                )
                alert_ids.append(alert_id)

            return alert_ids
        finally:
            cursor.close()
            conn.close()
