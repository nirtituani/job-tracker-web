import os, csv, io
from functools import wraps
from datetime import datetime
from flask import Flask, request, jsonify, send_file, session, redirect
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth
from sqlalchemy import create_engine, text

STATIC_FOLDER = os.path.join(os.path.dirname(__file__), "static")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")
CORS(app, supports_credentials=True)

DATABASE_URL = os.environ.get("DATABASE_URL", "")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:5001")
GOOGLE_REDIRECT_URI = f"{RENDER_EXTERNAL_URL}/api/auth/google/callback"

# Build SQLAlchemy URL with pg8000 dialect (keeps connections pooled)
_db_url = DATABASE_URL
if _db_url.startswith("postgresql://"):
    _db_url = "postgresql+pg8000://" + _db_url[len("postgresql://"):]
elif _db_url.startswith("postgres://"):
    _db_url = "postgresql+pg8000://" + _db_url[len("postgres://"):]

engine = create_engine(
    _db_url,
    pool_size=3,
    max_overflow=5,
    pool_pre_ping=True,         # reconnect transparently on stale connections
    pool_recycle=240,           # recycle before Supabase's ~5 min idle timeout
    connect_args={"ssl_context": True},
)

oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

def init_db():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT,
                created_at TEXT DEFAULT '',
                google_id TEXT
            )
        """))
        conn.execute(text("""
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
                applied_via TEXT DEFAULT '',
                match_rating INTEGER DEFAULT 0,
                notes TEXT DEFAULT '',
                last_updated TEXT DEFAULT ''
            )
        """))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id TEXT"))
        conn.execute(text("ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL"))
        conn.commit()

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
    with engine.connect() as conn:
        row = conn.execute(text("SELECT id FROM users WHERE email=:e"), {"e": email}).fetchone()
        if row:
            return jsonify({"error": "Email already registered"}), 409
        password_hash = generate_password_hash(password)
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        result = conn.execute(
            text("INSERT INTO users (email, password_hash, created_at) VALUES (:e, :p, :n) RETURNING id"),
            {"e": email, "p": password_hash, "n": now}
        )
        user_id = result.fetchone()[0]
        conn.commit()
    session["user_id"] = user_id
    session["email"] = email
    return jsonify({"id": user_id, "email": email}), 201

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.json
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, email, password_hash FROM users WHERE email=:e"), {"e": email}
        ).fetchone()
    if not row or not row[2] or not check_password_hash(row[2], password):
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

@app.route("/api/init", methods=["GET"])
def init_data():
    """Single endpoint that returns user + applications + stats in one round trip."""
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    uid = session["user_id"]
    with engine.connect() as conn:
        apps = [dict(r._mapping) for r in conn.execute(
            text("SELECT * FROM applications WHERE user_id=:uid ORDER BY id DESC"), {"uid": uid}
        ).fetchall()]
        total = conn.execute(text("SELECT COUNT(*) FROM applications WHERE user_id=:uid"), {"uid": uid}).scalar()
        active = conn.execute(text(
            "SELECT COUNT(*) FROM applications WHERE user_id=:uid AND status NOT IN ('Pre-Applied','Rejected','Ghosted','Withdrawn')"
        ), {"uid": uid}).scalar()
        interviews = conn.execute(text(
            "SELECT COUNT(*) FROM applications WHERE user_id=:uid AND status ILIKE :s"
        ), {"uid": uid, "s": "%Interview%"}).scalar()
        rejected = conn.execute(text(
            "SELECT COUNT(*) FROM applications WHERE user_id=:uid AND status='Rejected'"
        ), {"uid": uid}).scalar()
    return jsonify({
        "user": {"id": uid, "email": session["email"]},
        "applications": apps,
        "stats": {"total": total, "active": active, "interviews": interviews, "rejected": rejected},
    })

@app.route("/api/auth/google")
def google_login():
    return google.authorize_redirect(GOOGLE_REDIRECT_URI)

@app.route("/api/auth/google/callback")
def google_callback():
    token = google.authorize_access_token()
    user_info = token.get("userinfo")
    email = user_info["email"]
    google_id = user_info["sub"]
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, email FROM users WHERE google_id=:g OR email=:e"),
            {"g": google_id, "e": email}
        ).fetchone()
        if row:
            user_id = row[0]
            conn.execute(
                text("UPDATE users SET google_id=:g WHERE id=:i AND google_id IS NULL"),
                {"g": google_id, "i": user_id}
            )
        else:
            now = datetime.now().strftime("%d/%m/%Y %H:%M")
            result = conn.execute(
                text("INSERT INTO users (email, google_id, created_at) VALUES (:e, :g, :n) RETURNING id"),
                {"e": email, "g": google_id, "n": now}
            )
            user_id = result.fetchone()[0]
        conn.commit()
    session["user_id"] = user_id
    session["email"] = email
    return redirect("/")

# --- Import route ---

@app.route("/api/import", methods=["POST"])
@require_login
def import_applications():
    uid = session["user_id"]
    records = request.json  # list of application dicts
    if not isinstance(records, list):
        return jsonify({"error": "Expected a list of applications"}), 400
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    inserted = 0
    with engine.connect() as conn:
        for r in records:
            conn.execute(text("""
                INSERT INTO applications (user_id, company, title, location, date_applied, status,
                salary_range, job_link, contact_person, contact_email, applied_via,
                match_rating, notes, last_updated)
                VALUES (:uid, :company, :title, :location, :date_applied, :status,
                :salary_range, :job_link, :contact_person, :contact_email, :applied_via,
                :match_rating, :notes, :last_updated)
            """), {
                "uid": uid,
                "company": r.get("company", ""),
                "title": r.get("title", ""),
                "location": r.get("location", ""),
                "date_applied": r.get("date_applied", ""),
                "status": r.get("status", "Pre-Applied"),
                "salary_range": r.get("salary_range", ""),
                "job_link": r.get("job_link", ""),
                "contact_person": r.get("contact_person", ""),
                "contact_email": r.get("contact_email", ""),
                "applied_via": r.get("applied_via", ""),
                "match_rating": r.get("match_rating", 0) or 0,
                "notes": r.get("notes", ""),
                "last_updated": r.get("last_updated", now),
            })
            inserted += 1
        conn.commit()
    return jsonify({"imported": inserted})

# --- Application routes ---

@app.route("/api/applications", methods=["GET"])
@require_login
def get_applications():
    uid = session["user_id"]
    status = request.args.get("status", "")
    search = request.args.get("search", "")
    query = "SELECT * FROM applications WHERE user_id=:uid"
    params = {"uid": uid}
    if status and status != "All":
        query += " AND status=:status"
        params["status"] = status
    if search:
        query += " AND (company ILIKE :s OR title ILIKE :s OR location ILIKE :s)"
        params["s"] = f"%{search}%"
    query += " ORDER BY id DESC"
    with engine.connect() as conn:
        rows = [dict(r._mapping) for r in conn.execute(text(query), params).fetchall()]
    return jsonify(rows)

@app.route("/api/applications", methods=["POST"])
@require_login
def add_application():
    uid = session["user_id"]
    data = request.json
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    with engine.connect() as conn:
        result = conn.execute(text("""
            INSERT INTO applications (user_id, company, title, location, date_applied, status,
            salary_range, job_link, contact_person, contact_email, applied_via,
            match_rating, notes, last_updated)
            VALUES (:uid, :company, :title, :location, :date_applied, :status,
            :salary_range, :job_link, :contact_person, :contact_email, :applied_via,
            :match_rating, :notes, :last_updated)
            RETURNING *
        """), {
            "uid": uid,
            "company": data.get("company", ""), "title": data.get("title", ""),
            "location": data.get("location", ""), "date_applied": data.get("date_applied", ""),
            "status": data.get("status", "Pre-Applied"), "salary_range": data.get("salary_range", ""),
            "job_link": data.get("job_link", ""), "contact_person": data.get("contact_person", ""),
            "contact_email": data.get("contact_email", ""), "applied_via": data.get("applied_via", ""),
            "match_rating": data.get("match_rating", 0), "notes": data.get("notes", ""),
            "last_updated": now,
        })
        row = dict(result.mappings().first())
        conn.commit()
    return jsonify(row), 201

@app.route("/api/applications/<int:app_id>", methods=["PUT"])
@require_login
def update_application(app_id):
    uid = session["user_id"]
    data = request.json
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    with engine.connect() as conn:
        result = conn.execute(text("""
            UPDATE applications SET company=:company, title=:title, location=:location,
            date_applied=:date_applied, status=:status, salary_range=:salary_range,
            job_link=:job_link, contact_person=:contact_person, contact_email=:contact_email,
            applied_via=:applied_via, match_rating=:match_rating, notes=:notes,
            last_updated=:last_updated
            WHERE id=:id AND user_id=:uid
            RETURNING *
        """), {
            "company": data.get("company"), "title": data.get("title"),
            "location": data.get("location"), "date_applied": data.get("date_applied"),
            "status": data.get("status"), "salary_range": data.get("salary_range"),
            "job_link": data.get("job_link"), "contact_person": data.get("contact_person"),
            "contact_email": data.get("contact_email"), "applied_via": data.get("applied_via"),
            "match_rating": data.get("match_rating"), "notes": data.get("notes"),
            "last_updated": now, "id": app_id, "uid": uid,
        })
        row = dict(result.mappings().first())
        conn.commit()
    return jsonify(row)

@app.route("/api/applications/<int:app_id>", methods=["DELETE"])
@require_login
def delete_application(app_id):
    uid = session["user_id"]
    with engine.connect() as conn:
        conn.execute(
            text("DELETE FROM applications WHERE id=:id AND user_id=:uid"),
            {"id": app_id, "uid": uid}
        )
        conn.commit()
    return jsonify({"message": "Deleted"})

@app.route("/api/stats", methods=["GET"])
@require_login
def get_stats():
    uid = session["user_id"]
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM applications WHERE user_id=:uid"), {"uid": uid}).scalar()
        active = conn.execute(text(
            "SELECT COUNT(*) FROM applications WHERE user_id=:uid AND status NOT IN ('Pre-Applied','Rejected','Ghosted','Withdrawn')"
        ), {"uid": uid}).scalar()
        interviews = conn.execute(text(
            "SELECT COUNT(*) FROM applications WHERE user_id=:uid AND status ILIKE :s"
        ), {"uid": uid, "s": "%Interview%"}).scalar()
        rejected = conn.execute(text(
            "SELECT COUNT(*) FROM applications WHERE user_id=:uid AND status='Rejected'"
        ), {"uid": uid}).scalar()
    return jsonify({"total": total, "active": active, "interviews": interviews, "rejected": rejected})

@app.route("/api/export", methods=["GET"])
@require_login
def export_csv():
    uid = session["user_id"]
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM applications WHERE user_id=:uid ORDER BY id DESC"), {"uid": uid}
        )
        cols = list(result.keys())
        rows = result.fetchall()
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
