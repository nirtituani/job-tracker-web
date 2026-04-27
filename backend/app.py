import os, csv, io
from functools import wraps
from datetime import datetime
from urllib.parse import urlparse
from flask import Flask, request, jsonify, send_file, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import pg8000.dbapi as pg8000

STATIC_FOLDER = os.path.join(os.path.dirname(__file__), "static")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")
CORS(app, supports_credentials=True)

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    url = urlparse(DATABASE_URL)
    conn = pg8000.connect(
        host=url.hostname,
        port=url.port or 5432,
        database=url.path.lstrip("/"),
        user=url.username,
        password=url.password,
        ssl_context=True
    )
    return conn

def fetchone_dict(cur):
    row = cur.fetchone()
    if row is None:
        return None
    cols = [d[0] for d in cur.description]
    return dict(zip(cols, row))

def fetchall_dict(cur):
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT ''
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id SERIAL PRIMARY KEY,
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
    conn.commit()
    cur.close()
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
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email=%s", (email,))
    if cur.fetchone():
        cur.close(); conn.close()
        return jsonify({"error": "Email already registered"}), 409
    password_hash = generate_password_hash(password)
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    cur.execute(
        "INSERT INTO users (email, password_hash, created_at) VALUES (%s, %s, %s) RETURNING id",
        (email, password_hash, now)
    )
    user_id = cur.fetchone()[0]
    conn.commit()
    cur.close(); conn.close()
    session["user_id"] = user_id
    session["email"] = email
    return jsonify({"id": user_id, "email": email}), 201

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.json
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, email, password_hash FROM users WHERE email=%s", (email,))
    row = cur.fetchone()
    cur.close(); conn.close()
    if not row or not check_password_hash(row[2], password):
        return jsonify({"error": "Invalid email or password"}), 401
    session["user_id"] = row[0]
    session["email"] = row[1]
    return jsonify({"id": row[0], "email": row[1]})

@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})

@app.route("/api/auth/me", methods=["GET"])
def me():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"id": session["user_id"], "email": session["email"]})

# --- Application routes ---

@app.route("/api/applications", methods=["GET"])
@require_login
def get_applications():
    uid = session["user_id"]
    conn = get_db()
    cur = conn.cursor()
    status = request.args.get("status", "")
    search = request.args.get("search", "")
    query = "SELECT * FROM applications WHERE user_id=%s"
    params = [uid]
    if status and status != "All":
        query += " AND status=%s"
        params.append(status)
    if search:
        query += " AND (company ILIKE %s OR title ILIKE %s OR location ILIKE %s)"
        params.extend([f"%{search}%"] * 3)
    query += " ORDER BY id DESC"
    cur.execute(query, params)
    rows = fetchall_dict(cur)
    cur.close(); conn.close()
    return jsonify(rows)

@app.route("/api/applications", methods=["POST"])
@require_login
def add_application():
    uid = session["user_id"]
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    cur.execute("""
        INSERT INTO applications (user_id, company, title, location, date_applied, status,
        salary_range, job_link, contact_person, contact_email, applied_via,
        match_rating, notes, last_updated)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
    cur.close(); conn.close()
    return jsonify({"message": "Added"}), 201

@app.route("/api/applications/<int:app_id>", methods=["PUT"])
@require_login
def update_application(app_id):
    uid = session["user_id"]
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    cur.execute("""
        UPDATE applications SET company=%s, title=%s, location=%s, date_applied=%s,
        status=%s, salary_range=%s, job_link=%s, contact_person=%s, contact_email=%s,
        applied_via=%s, match_rating=%s, notes=%s, last_updated=%s
        WHERE id=%s AND user_id=%s
    """, (
        data.get("company"), data.get("title"), data.get("location"),
        data.get("date_applied"), data.get("status"), data.get("salary_range"),
        data.get("job_link"), data.get("contact_person"), data.get("contact_email"),
        data.get("applied_via"), data.get("match_rating"), data.get("notes"),
        now, app_id, uid
    ))
    conn.commit()
    cur.close(); conn.close()
    return jsonify({"message": "Updated"})

@app.route("/api/applications/<int:app_id>", methods=["DELETE"])
@require_login
def delete_application(app_id):
    uid = session["user_id"]
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM applications WHERE id=%s AND user_id=%s", (app_id, uid))
    conn.commit()
    cur.close(); conn.close()
    return jsonify({"message": "Deleted"})

@app.route("/api/stats", methods=["GET"])
@require_login
def get_stats():
    uid = session["user_id"]
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM applications WHERE user_id=%s", (uid,))
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM applications WHERE user_id=%s AND status IN ('Applied','Phone Screen','Online Assessment')", (uid,))
    active = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM applications WHERE user_id=%s AND status ILIKE %s", (uid, "%Interview%"))
    interviews = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM applications WHERE user_id=%s AND status='Rejected'", (uid,))
    rejected = cur.fetchone()[0]
    cur.close(); conn.close()
    return jsonify({"total": total, "active": active, "interviews": interviews, "rejected": rejected})

@app.route("/api/export", methods=["GET"])
@require_login
def export_csv():
    uid = session["user_id"]
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM applications WHERE user_id=%s ORDER BY id DESC", (uid,))
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    cur.close(); conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(cols)
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
    full_path = os.path.join(STATIC_FOLDER, path)
    if path and os.path.exists(full_path):
        return send_file(full_path)
    index = os.path.join(STATIC_FOLDER, "index.html")
    if os.path.exists(index):
        return send_file(index)
    return jsonify({"error": "Frontend not built"}), 404

if __name__ == "__main__":
    app.run(debug=True, port=5001)
