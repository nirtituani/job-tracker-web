import os, sqlite3, csv, io
from functools import wraps
from datetime import datetime
from flask import Flask, request, jsonify, send_file, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__,
            static_folder=os.path.join(os.path.dirname(__file__), "static"),
            static_url_path="")
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")
CORS(app, supports_credentials=True)

DB_PATH = os.environ.get("DATABASE_URL", os.path.join(os.path.dirname(__file__), "database.db"))

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT ''
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 0,
            company TEXT NOT NULL,
            title TEXT NOT NULL,
            location TEXT DEFAULT '',
            date_applied TEXT DEFAULT '',
            status TEXT DEFAULT 'Pre-Applied',
            salary_range TEXT DEFAULT '',
            job_link TEXT DEFAULT '',
            contact_person TEXT DEFAULT '',
            contact_email TEXT DEFAULT '',
            applied_via TEXT DEFAULT 'Company Website',
            match_rating INTEGER DEFAULT 0,
            notes TEXT DEFAULT '',
            last_updated TEXT DEFAULT ''
        )
    """)
    try:
        conn.execute("ALTER TABLE applications ADD COLUMN user_id INTEGER NOT NULL DEFAULT 0")
    except Exception:
        pass
    conn.commit()
    conn.close()

init_db()

# --- Auth helpers ---

def require_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

# --- Auth routes ---

@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.json
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    conn = get_db()
    existing = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
    if existing:
        conn.close()
        return jsonify({"error": "Email already registered"}), 409
    password_hash = generate_password_hash(password)
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    cursor = conn.execute(
        "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
        (email, password_hash, now)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    session["user_id"] = user_id
    session["email"] = email
    return jsonify({"id": user_id, "email": email}), 201

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.json
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    conn.close()
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password"}), 401
    session["user_id"] = user["id"]
    session["email"] = user["email"]
    return jsonify({"id": user["id"], "email": user["email"]})

@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})

@app.route("/api/auth/me", methods=["GET"])
def me():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"id": session["user_id"], "email": session["email"]})

# --- Application routes (all scoped to logged-in user) ---

@app.route("/api/applications", methods=["GET"])
@require_login
def get_applications():
    uid = session["user_id"]
    conn = get_db()
    status = request.args.get("status", "")
    search = request.args.get("search", "")
    query = "SELECT * FROM applications WHERE user_id=?"
    params = [uid]
    if status and status != "All":
        query += " AND status=?"
        params.append(status)
    if search:
        query += " AND (company LIKE ? OR title LIKE ? OR location LIKE ?)"
        params.extend([f"%{search}%"] * 3)
    query += " ORDER BY id DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/applications", methods=["POST"])
@require_login
def add_application():
    uid = session["user_id"]
    data = request.json
    conn = get_db()
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    conn.execute("""
        INSERT INTO applications (user_id, company, title, location, date_applied, status,
        salary_range, job_link, contact_person, contact_email, applied_via,
        match_rating, notes, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        uid,
        data.get("company", ""), data.get("title", ""),
        data.get("location", ""), data.get("date_applied", ""),
        data.get("status", "Pre-Applied"), data.get("salary_range", ""),
        data.get("job_link", ""), data.get("contact_person", ""),
        data.get("contact_email", ""), data.get("applied_via", "Company Website"),
        data.get("match_rating", 0), data.get("notes", ""), now
    ))
    conn.commit()
    conn.close()
    return jsonify({"message": "Added"}), 201

@app.route("/api/applications/<int:app_id>", methods=["PUT"])
@require_login
def update_application(app_id):
    uid = session["user_id"]
    data = request.json
    conn = get_db()
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    conn.execute("""
        UPDATE applications SET company=?, title=?, location=?, date_applied=?,
        status=?, salary_range=?, job_link=?, contact_person=?, contact_email=?,
        applied_via=?, match_rating=?, notes=?, last_updated=?
        WHERE id=? AND user_id=?
    """, (
        data.get("company"), data.get("title"), data.get("location"),
        data.get("date_applied"), data.get("status"), data.get("salary_range"),
        data.get("job_link"), data.get("contact_person"), data.get("contact_email"),
        data.get("applied_via"), data.get("match_rating"), data.get("notes"),
        now, app_id, uid
    ))
    conn.commit()
    conn.close()
    return jsonify({"message": "Updated"})

@app.route("/api/applications/<int:app_id>", methods=["DELETE"])
@require_login
def delete_application(app_id):
    uid = session["user_id"]
    conn = get_db()
    conn.execute("DELETE FROM applications WHERE id=? AND user_id=?", (app_id, uid))
    conn.commit()
    conn.close()
    return jsonify({"message": "Deleted"})

@app.route("/api/stats", methods=["GET"])
@require_login
def get_stats():
    uid = session["user_id"]
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM applications WHERE user_id=?", (uid,)).fetchone()[0]
    active = conn.execute(
        "SELECT COUNT(*) FROM applications WHERE user_id=? AND status IN ('Applied','Phone Screen','Online Assessment')",
        (uid,)).fetchone()[0]
    interviews = conn.execute(
        "SELECT COUNT(*) FROM applications WHERE user_id=? AND status LIKE '%Interview%'",
        (uid,)).fetchone()[0]
    rejected = conn.execute(
        "SELECT COUNT(*) FROM applications WHERE user_id=? AND status='Rejected'",
        (uid,)).fetchone()[0]
    conn.close()
    return jsonify({"total": total, "active": active, "interviews": interviews, "rejected": rejected})

@app.route("/api/export", methods=["GET"])
@require_login
def export_csv():
    uid = session["user_id"]
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM applications WHERE user_id=? ORDER BY id DESC", (uid,)
    ).fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Company", "Job Title", "Location", "Date Applied",
                     "Status", "Salary Range", "Job Link", "Contact Person",
                     "Contact Email", "Applied Via", "Match", "Notes", "Last Updated"])
    for r in rows:
        writer.writerow(list(r))
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()),
                     mimetype="text/csv", as_attachment=True,
                     download_name="applications.csv")

# --- SPA fallback ---

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path.startswith("api/"):
        return jsonify({"error": "Not found"}), 404
    dist = os.path.join(app.static_folder, path)
    if path and os.path.exists(dist):
        return send_file(dist)
    index = os.path.join(app.static_folder, "index.html")
    if os.path.exists(index):
        return send_file(index)
    return jsonify({"error": "Frontend not built"}), 404

if __name__ == "__main__":
    app.run(debug=True, port=5001)
