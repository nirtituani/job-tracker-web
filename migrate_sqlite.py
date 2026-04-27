"""
One-time migration: import jobs from a local SQLite database into the live app.

Usage:
  python migrate_sqlite.py

You will be prompted for your email, password, and the SQLite file path.
"""
import sqlite3, json, getpass
import urllib.request, urllib.error

API = input("App URL (e.g. https://your-app.onrender.com): ").rstrip("/")
DB_PATH = input("SQLite file path [/Users/nirtituani/Downloads/job_tracker_new/job_applications.db]: ").strip()
if not DB_PATH:
    DB_PATH = "/Users/nirtituani/Downloads/job_tracker_new/job_applications.db"
EMAIL = input("Your account email: ").strip()
PASSWORD = getpass.getpass("Your password: ")

# --- Login ---
print("\nLogging in...")
login_data = json.dumps({"email": EMAIL, "password": PASSWORD}).encode()
req = urllib.request.Request(
    f"{API}/api/auth/login",
    data=login_data,
    headers={"Content-Type": "application/json"},
    method="POST",
)
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
try:
    res = opener.open(req)
    user = json.loads(res.read())
    print(f"Logged in as {user['email']}")
except urllib.error.HTTPError as e:
    print(f"Login failed: {e.read().decode()}")
    exit(1)

# --- Read SQLite ---
print(f"\nReading {DB_PATH}...")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT * FROM applications ORDER BY id ASC")
rows = cur.fetchall()
conn.close()
print(f"Found {len(rows)} records")

# Map old column names to new ones
records = []
for r in rows:
    records.append({
        "company":        r["company_name"] or "",
        "title":          r["job_title"] or "",
        "location":       r["location"] or "",
        "date_applied":   r["date_applied"] or "",
        "status":         r["status"] or "Pre-Applied",
        "salary_range":   r["salary_range"] or "",
        "job_link":       r["job_link"] or "",
        "contact_person": r["contact_person"] or "",
        "contact_email":  r["contact_email"] or "",
        "applied_via":    r["applied_via"] or "",
        "match_rating":   r["job_match"] or 0,
        "notes":          r["notes"] or "",
        "last_updated":   r["last_updated"] or "",
    })

# --- Import ---
print("Importing...")
import_data = json.dumps(records).encode()
req2 = urllib.request.Request(
    f"{API}/api/import",
    data=import_data,
    headers={"Content-Type": "application/json"},
    method="POST",
)
try:
    res2 = opener.open(req2)
    result = json.loads(res2.read())
    print(f"\nDone! {result['imported']} applications imported successfully.")
except urllib.error.HTTPError as e:
    print(f"Import failed: {e.read().decode()}")
    exit(1)
