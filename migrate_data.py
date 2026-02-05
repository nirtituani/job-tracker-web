#!/usr/bin/env python3
"""
Data Migration Script
Migrates data from desktop SQLite database to web app database
"""

import sqlite3
import sys
from pathlib import Path

def migrate_data(source_db_path, target_db_path):
    """Migrate applications from source to target database"""
    
    # Connect to source database
    source_conn = sqlite3.connect(source_db_path)
    source_cursor = source_conn.cursor()
    
    # Connect to target database
    target_conn = sqlite3.connect(target_db_path)
    target_cursor = target_conn.cursor()
    
    try:
        # Check if job_match column exists
        source_cursor.execute("PRAGMA table_info(applications)")
        columns = [col[1] for col in source_cursor.fetchall()]
        has_job_match = 'job_match' in columns
        
        print(f"Source database columns: {columns}")
        print(f"Has job_match column: {has_job_match}")
        
        # Read all applications from source
        if has_job_match:
            # Find the position of job_match
            job_match_pos = columns.index('job_match')
            source_cursor.execute('SELECT * FROM applications')
        else:
            source_cursor.execute('''
                SELECT company_name, job_title, location, date_applied, status, 
                       salary_range, job_link, contact_person, contact_email, 
                       notes, last_updated
                FROM applications
            ''')
        
        applications = source_cursor.fetchall()
        
        print(f"Found {len(applications)} applications to migrate")
        
        # Insert into target database
        migrated = 0
        for app in applications:
            try:
                # Extract fields based on schema
                if has_job_match:
                    # Map to proper positions (handle ALTER TABLE case)
                    row_dict = dict(zip(columns, app))
                    company_name = row_dict.get('company_name')
                    job_title = row_dict.get('job_title')
                    location = row_dict.get('location')
                    date_applied = row_dict.get('date_applied')
                    status = row_dict.get('status')
                    salary_range = row_dict.get('salary_range')
                    job_link = row_dict.get('job_link')
                    contact_person = row_dict.get('contact_person')
                    contact_email = row_dict.get('contact_email')
                    notes = row_dict.get('notes')
                    last_updated = row_dict.get('last_updated')
                    job_match = row_dict.get('job_match')
                else:
                    company_name, job_title, location, date_applied, status, \
                    salary_range, job_link, contact_person, contact_email, \
                    notes, last_updated = app
                    job_match = None
                
                target_cursor.execute('''
                    INSERT INTO application 
                    (company_name, job_title, location, date_applied, status, 
                     salary_range, job_link, contact_person, contact_email, 
                     job_match, notes, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (company_name, job_title, location, date_applied, status,
                      salary_range, job_link, contact_person, contact_email,
                      job_match, notes, last_updated))
                
                migrated += 1
                
            except Exception as e:
                print(f"Error migrating application {company_name}: {e}")
                continue
        
        target_conn.commit()
        print(f"\n✅ Successfully migrated {migrated} applications!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        target_conn.rollback()
        
    finally:
        source_conn.close()
        target_conn.close()

if __name__ == '__main__':
    # Source database path (from desktop app)
    source_db = Path('/home/user/job_tracker/job_applications.db')
    
    # Target database path (for web app)
    target_db = Path('/home/user/job_tracker_web/job_applications.db')
    
    if not source_db.exists():
        print(f"❌ Source database not found: {source_db}")
        print("Please ensure the desktop app database exists")
        sys.exit(1)
    
    print("📊 Starting data migration...")
    print(f"Source: {source_db}")
    print(f"Target: {target_db}")
    print()
    
    migrate_data(str(source_db), str(target_db))
    
    print("\n🎉 Migration complete!")
    print("You can now deploy your web app to Render.com")
