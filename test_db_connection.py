#!/usr/bin/env python3
"""
Safe Database Connection Test Script.

Tests connectivity to the configured MySQL database (local or remote/Aiven)
without modifying any schema, data, or tables.

Security: Never prints passwords, tokens, or credentials to stdout.
"""

import os
import sys
from dotenv import load_dotenv

# Ensure environment variables from .env are loaded
load_dotenv()

# Import the application's configuration and connection builder
from app.config import Config
from app.database import get_connection_params
import mysql.connector
from mysql.connector import Error


def mask_secret(value: str) -> str:
    """Return safe metadata about a secret without revealing its content."""
    if not value:
        return "[NOT CONFIGURED / EMPTY]"
    return f"[CONFIGURED] ({len(value)} chars, starts with '{value[0]}***')"


def run_test():
    print("=" * 60)
    print("  Smart Exam Management System — Database Connection Test")
    print("=" * 60)

    # 1. Print configuration summary (sanitized)
    print("\n[1] Configuration Summary:")
    print(f"  • Host:        {Config.DB_HOST}")
    print(f"  • Port:        {Config.DB_PORT}")
    print(f"  • Database:    {Config.DB_NAME}")
    print(f"  • User:        {Config.DB_USER}")
    print(f"  • Password:    {mask_secret(Config.DB_PASSWORD)}")
    print(f"  • SSL Required: {Config.DB_SSL_REQUIRED}")
    print(f"  • SSL CA File:  {Config.DB_SSL_CA or '[None / Default TLS]'}")
    if Config.DB_SSL_CA:
        ca_exists = os.path.isfile(Config.DB_SSL_CA)
        print(f"  • CA Exists:   {'YES' if ca_exists else 'NO (File not found)'}")

    # 2. Build connection parameters
    print("\n[2] Establishing Connection...")
    conn_params = get_connection_params()

    # 3. Test Connection
    try:
        conn = mysql.connector.connect(**conn_params, connection_timeout=10)
        
        if not conn.is_connected():
            print("❌ Connection could not be established.")
            return False

        print("✓ Connected successfully!")

        # 4. Query Server Metadata (Read-only)
        cursor = conn.cursor()
        
        # MySQL Version
        cursor.execute("SELECT VERSION()")
        version_result = cursor.fetchone()
        version = version_result[0] if version_result else "Unknown"

        # Current Database
        cursor.execute("SELECT DATABASE()")
        db_result = cursor.fetchone()
        current_db = db_result[0] if db_result else "None"

        # Current Authenticated User
        cursor.execute("SELECT CURRENT_USER()")
        user_result = cursor.fetchone()
        auth_user = user_result[0] if user_result else "Unknown"

        # SSL Cipher in use
        cursor.execute("SHOW STATUS LIKE 'Ssl_cipher'")
        ssl_result = cursor.fetchone()
        ssl_cipher = ssl_result[1] if ssl_result and ssl_result[1] else "None (Non-SSL)"

        cursor.close()
        conn.close()

        print("\n[3] Verification Results:")
        print(f"  • Server Version:   {version}")
        print(f"  • Active Database:  {current_db}")
        print(f"  • Authenticated As: {auth_user}")
        print(f"  • Active Cipher:    {ssl_cipher}")

        print("\n" + "=" * 60)
        print("✓ SUCCESS: Database is accessible and responding properly.")
        print("=" * 60)
        return True

    except Error as e:
        print("\n" + "=" * 60)
        print(f"❌ CONNECTION FAILED (Error Code: {e.errno})")
        print(f"Details: {e.msg}")
        print("=" * 60)

        # Context-aware troubleshooting advice
        print("\nTroubleshooting Guidance:")
        if e.errno == 2003:
            print("  • Host/Port Unreachable:")
            print("    The Aiven service may still be PROVISIONING. Cloud services")
            print("    typically require 2-5 minutes to initialize after creation.")
            print("    Please check the Aiven web console status.")
        elif e.errno == 1045:
            print("  • Authentication Denied:")
            print("    The username or password in your environment did not match.")
            print("    Ensure DB_PASSWORD in your .env matches your Aiven service password.")
        elif e.errno == 2026:
            print("  • SSL Handshake Error:")
            print("    The CA certificate path could not be verified or is missing.")
            print("    Download 'ca.pem' from your Aiven dashboard and verify DB_SSL_CA.")
        elif e.errno == 1049:
            print("  • Unknown Database:")
            print(f"    Database '{Config.DB_NAME}' does not exist on the target server.")
        else:
            print("    Check network access and database service availability.")

        return False


if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
