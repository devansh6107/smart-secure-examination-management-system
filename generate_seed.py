"""
Seed Data Generator.

Generates the seed.sql file with proper Werkzeug password hashes.
Run this ONCE to update sql/seed.sql with valid hashes.

Usage: python generate_seed.py
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from werkzeug.security import generate_password_hash


def main():
    """Print password hashes for demo accounts."""
    accounts = {
        'admin123': 'Admin account',
        'student123': 'Student accounts',
        'invig123': 'Invigilator accounts',
    }

    print("=" * 60)
    print("  ExamGuard AI — Password Hash Generator")
    print("=" * 60)
    for password, label in accounts.items():
        h = generate_password_hash(password, method='pbkdf2:sha256')
        print(f"\n{label} (password: {password}):")
        print(f"  {h}")
    print("\n" + "=" * 60)
    print("Copy these hashes into sql/seed.sql for the User INSERTs.")
    print("=" * 60)


if __name__ == '__main__':
    main()
