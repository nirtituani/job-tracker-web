#!/usr/bin/env python3
"""
Initialize web app database with default schema
"""

import sqlite3
from pathlib import Path

def init_database():
    db_path = Path('/home/user/job_tracker_web/job_applications.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create User table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    
    # Create Application table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS application (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            job_title TEXT NOT NULL,
            location TEXT,
            date_applied TEXT NOT NULL,
            status TEXT DEFAULT 'Applied',
            salary_range TEXT,
            job_link TEXT,
            contact_person TEXT,
            contact_email TEXT,
            job_match INTEGER,
            notes TEXT,
            last_updated TEXT NOT NULL
        )
    ''')
    
    # Create default admin user (password: admin)
    from werkzeug.security import generate_password_hash
    password_hash = generate_password_hash('admin')
    
    try:
        cursor.execute('''
            INSERT INTO user (username, password_hash)
            VALUES ('admin', ?)
        ''', (password_hash,))
    except sqlite3.IntegrityError:
        print("Admin user already exists")
    
    conn.commit()
    conn.close()
    
    print("✅ Database initialized successfully!")

if __name__ == '__main__':
    init_database()
