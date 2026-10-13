#!/usr/bin/env python3
"""
Database Schema & Seed Initializer.

Executes schema.sql, views.sql, procedures.sql, triggers.sql, and seed.sql
against the currently configured database (local or remote/Aiven) without
requiring root/superuser DROP DATABASE permissions.

Usage:
    python3 init_database.py
"""

import os
import sys
import re
from dotenv import load_dotenv

load_dotenv()

from app.config import Config
from app.database import get_db_connection
import mysql.connector


def read_sql_file(filepath: str) -> str:
    """Read an SQL file from the sql/ directory."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def execute_standard_sql(cursor, sql_content: str, label: str):
    """Execute standard SQL statements (tables, views, seed data)."""
    print(f"\n[+] Executing {label}...")
    
    # Remove comment-only lines and lines switching databases
    cleaned_lines = []
    for line in sql_content.splitlines():
        trimmed = line.strip()
        if trimmed.startswith('--') or trimmed.startswith('/*'):
            continue
        # Skip database creation/switching statements so we target the active DB
        if re.match(r'^(DROP\s+DATABASE|CREATE\s+DATABASE|USE\s+)', trimmed, re.IGNORECASE):
            continue
        cleaned_lines.append(line)
        
    full_sql = "\n".join(cleaned_lines)
    
    # Split by semicolon
    statements = [stmt.strip() for stmt in full_sql.split(';') if stmt.strip()]
    
    count = 0
    for stmt in statements:
        if not stmt:
            continue
        try:
            cursor.execute(stmt)
            count += 1
        except mysql.connector.Error as err:
            # Report error with first 80 chars of statement
            snippet = stmt.replace('\n', ' ')[:80]
            print(f"    ⚠️ Warning on statement: {snippet}...\n    Error: {err}")
            
    print(f"    ✓ {count} statements executed for {label}.")


def execute_procedure_sql(cursor, sql_content: str):
    """Execute stored procedures handling DELIMITER blocks."""
    print("\n[+] Executing Stored Procedures...")
    
    # Remove DELIMITER commands and USE statements
    # Match blocks between DELIMITER // ... //
    blocks = re.findall(r'CREATE\s+PROCEDURE[\s\S]*?END(?:\s*//|\s*;)', sql_content, re.IGNORECASE)
    
    count = 0
    for block in blocks:
        clean_block = block.strip()
        if clean_block.endswith('//'):
            clean_block = clean_block[:-2].strip()
        elif clean_block.endswith(';'):
            clean_block = clean_block[:-1].strip()
            
        # Extract procedure name
        name_match = re.search(r'CREATE\s+PROCEDURE\s+([a-zA-Z0-9_]+)', clean_block, re.IGNORECASE)
        proc_name = name_match.group(1) if name_match else "procedure"
        
        try:
            cursor.execute(f"DROP PROCEDURE IF EXISTS {proc_name}")
            cursor.execute(clean_block)
            print(f"    ✓ Created procedure: {proc_name}")
            count += 1
        except mysql.connector.Error as err:
            print(f"    ⚠️ Error creating {proc_name}: {err}")
            
    print(f"    ✓ {count} stored procedures created.")


def execute_trigger_sql(cursor, sql_content: str):
    """Execute triggers handling DELIMITER blocks."""
    print("\n[+] Executing Triggers...")
    
    blocks = re.findall(r'CREATE\s+TRIGGER[\s\S]*?END(?:\s*//|\s*;)', sql_content, re.IGNORECASE)
    
    count = 0
    for block in blocks:
        clean_block = block.strip()
        if clean_block.endswith('//'):
            clean_block = clean_block[:-2].strip()
        elif clean_block.endswith(';'):
            clean_block = clean_block[:-1].strip()
            
        name_match = re.search(r'CREATE\s+TRIGGER\s+([a-zA-Z0-9_]+)', clean_block, re.IGNORECASE)
        trig_name = name_match.group(1) if name_match else "trigger"
        
        try:
            cursor.execute(f"DROP TRIGGER IF EXISTS {trig_name}")
            cursor.execute(clean_block)
            print(f"    ✓ Created trigger: {trig_name}")
            count += 1
        except mysql.connector.Error as err:
            print(f"    ⚠️ Error creating {trig_name}: {err}")
            
    print(f"    ✓ {count} triggers created.")


def main():
    print("=" * 65)
    print("  Initializing Database Schema & Seed Data")
    print(f"  Target Host:     {Config.DB_HOST}")
    print(f"  Target Database: {Config.DB_NAME}")
    print("=" * 65)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Schema
        schema_sql = read_sql_file("sql/schema.sql")
        execute_standard_sql(cursor, schema_sql, "Schema (Tables & Constraints)")

        # 2. Views
        views_sql = read_sql_file("sql/views.sql")
        execute_standard_sql(cursor, views_sql, "Analytical Views")

        # 3. Procedures
        proc_sql = read_sql_file("sql/procedures.sql")
        execute_procedure_sql(cursor, proc_sql)

        # 4. Triggers
        trig_sql = read_sql_file("sql/triggers.sql")
        execute_trigger_sql(cursor, trig_sql)

        # 5. Seed Data
        seed_sql = read_sql_file("sql/seed.sql")
        execute_standard_sql(cursor, seed_sql, "Seed Data (Users, Students, Exams, Attendance)")

        conn.commit()

        # 6. Verify Tables
        cursor.execute("SHOW TABLES")
        tables = [t[0] for t in cursor.fetchall()]
        print("\n" + "=" * 65)
        print(f"✓ DATABASE INITIALIZATION COMPLETE! Total tables/views: {len(tables)}")
        print(f"Tables & Views in {Config.DB_NAME}:")
        for t in sorted(tables):
            print(f"  • {t}")
        print("=" * 65)

    except Exception as e:
        conn.rollback()
        print(f"\n❌ FAILED to initialize database: {e}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
