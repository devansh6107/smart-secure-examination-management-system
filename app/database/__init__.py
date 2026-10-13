"""
MySQL Database Connection Manager.

Provides a connection pool and a context-manager helper
so that routes/services can safely acquire and release connections.

Usage:
    from app.database.connection import get_db_connection

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM User WHERE user_id = %s", (uid,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()          # returns connection to pool
"""

import mysql.connector
from mysql.connector import pooling, Error
from app.config import Config

# ── Connection Pool (created once, reused across requests) ──
_pool = None


def _get_pool():
    """Lazily create the connection pool on first use."""
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="exam_pool",
            pool_size=5,
            pool_reset_session=True,
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            autocommit=False,           # we manage transactions explicitly
            charset='utf8mb4',
            collation='utf8mb4_general_ci'
        )
    return _pool


def get_db_connection():
    """
    Get a connection from the pool.
    Caller is responsible for calling conn.close() to return it.
    """
    try:
        pool = _get_pool()
        return pool.get_connection()
    except Error as e:
        print(f"[DB ERROR] Could not get connection: {e}")
        raise


def close_pool():
    """Close all connections in the pool (for graceful shutdown)."""
    global _pool
    _pool = None
