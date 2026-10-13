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

import os
import tempfile
import mysql.connector
from mysql.connector import pooling, Error
from app.config import Config

# ── Connection Pool (created once, reused across requests) ──
_pool = None


def get_connection_params():
    """Build connection parameters dictionary supporting both local and remote SSL."""
    params = {
        'host': Config.DB_HOST,
        'port': Config.DB_PORT,
        'user': Config.DB_USER,
        'password': Config.DB_PASSWORD,
        'database': Config.DB_NAME,
        'autocommit': False,           # we manage transactions explicitly
        'charset': 'utf8mb4',
        'collation': 'utf8mb4_general_ci',
    }

    # Enable SSL/TLS if explicitly required or if a CA certificate is specified
    if Config.DB_SSL_REQUIRED or Config.DB_SSL_CA:
        params['ssl_disabled'] = False
        ca_path = Config.DB_SSL_CA
        valid_ca = False
        if ca_path:
            if os.path.isfile(ca_path):
                params['ssl_ca'] = ca_path
                valid_ca = True
            elif '-----BEGIN CERTIFICATE-----' in ca_path:
                temp_ca_path = os.path.join(tempfile.gettempdir(), 'aiven_ca.pem')
                try:
                    with open(temp_ca_path, 'w') as f:
                        f.write(ca_path)
                    params['ssl_ca'] = temp_ca_path
                    valid_ca = True
                except Exception as e:
                    print(f"[DB WARNING] Could not write temporary CA cert: {e}")
            else:
                print(f"[DB WARNING] DB_SSL_CA file not found: {ca_path}")

        if valid_ca and Config.DB_SSL_VERIFY_CERT:
            params['ssl_verify_cert'] = True
            params['ssl_verify_identity'] = True
        else:
            params['ssl_verify_cert'] = False
            params['ssl_verify_identity'] = False

    return params


def _get_pool():
    """Lazily create the connection pool on first use."""
    global _pool
    if _pool is None:
        conn_params = get_connection_params()
        _pool = pooling.MySQLConnectionPool(
            pool_name="exam_pool",
            pool_size=5,
            pool_reset_session=True,
            **conn_params
        )
    return _pool


def get_db_connection():
    """
    Get a connection from the pool.
    Caller is responsible for calling conn.close() to return it.
    """
    try:
        pool = _get_pool()
        conn = pool.get_connection()
        if not conn.is_connected():
            conn.reconnect(attempts=3, delay=1)
        return conn
    except Error as e:
        print(f"[DB ERROR] Could not get connection: {e}")
        raise


def close_pool():
    """Close all connections in the pool (for graceful shutdown)."""
    global _pool
    _pool = None

