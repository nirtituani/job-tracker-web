# Auth + Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add email/password auth so each user has a private job tracker, then deploy as a single Flask service on Render.

**Architecture:** Flask serves both the REST API and the built React frontend. Sessions are cookie-based (Flask `session`). SQLite is stored on a Render persistent disk. All API routes are protected; unauthenticated requests get a 401.

**Tech Stack:** Flask, werkzeug.security (password hashing), Flask sessions, gunicorn, React + Vite, Render (hosting)

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `backend/app.py` | Modify | Add users table, user_id to applications, auth routes, protect existing routes, serve React static files |
| `backend/requirements.txt` | Modify | Add gunicorn |
| `frontend/src/api/auth.js` | Create | Auth API client (login, register, logout, me) |
| `frontend/src/api/applications.js` | Modify | Add 401 → logout redirect handling |
| `frontend/src/pages/AuthPage.jsx` | Create | Combined login + register page |
| `frontend/src/App.jsx` | Modify | Add auth state check on load, show AuthPage if not logged in |
| `frontend/src/components/Sidebar.jsx` | Modify | Add logout button in footer |
| `render.yaml` | Create | Render deployment config |
| `backend/build.sh` | Create | Build script: installs deps, builds React, starts gunicorn |

---

## Task 1: Update backend — users table + migrate applications

**Files:**
- Modify: `backend/app.py`

- [ ] **Step 1: Replace `init_db` and `DB_PATH` in `backend/app.py`**

Replace the existing `DB_PATH`, `get_db`, and `init_db` with the following. This adds the `users` table and adds `user_id` to `applications` via `ALTER TABLE IF NOT EXISTS` (safe to run repeatedly):

```python
import os, sqlite3, csv, io
from datetime import datetime
from flask import Flask, request, jsonify, send_file, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder="../frontend/dist", static_url_path="")
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
    # Migrate existing table if user_id column is missing
    try:
        conn.execute("ALTER TABLE applications ADD COLUMN user_id INTEGER NOT NULL DEFAULT 0")
    except Exception:
        pass
    conn.commit()
    conn.close()

init_db()
```

- [ ] **Step 2: Verify the DB initialises without error**

```bash
cd /Users/nirtituani/Downloads/job_tracker_web_pen/backend
source venv/bin/activate
python -c "import app; print('DB OK')"
```
Expected output: `DB OK`

- [ ] **Step 3: Commit**

```bash
cd /Users/nirtituani/Downloads/job_tracker_web_pen
git add backend/app.py
git commit -m "feat: add users table and user_id column to applications"
```

---

## Task 2: Add auth helper + auth routes

**Files:**
- Modify: `backend/app.py`

- [ ] **Step 1: Add `require_login` decorator and auth routes**

Add the following after `init_db()` and before the existing `@app.route` definitions:

```python
from functools import wraps

def require_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

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
```

- [ ] **Step 2: Verify auth routes work**

```bash
cd /Users/nirtituani/Downloads/job_tracker_web_pen/backend
source venv/bin/activate
python app.py &
sleep 2

# Register
curl -s -c /tmp/jar.txt -X POST http://localhost:5001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123"}'
# Expected: {"id":1,"email":"test@test.com"}

# Me (with session cookie)
curl -s -b /tmp/jar.txt http://localhost:5001/api/auth/me
# Expected: {"id":1,"email":"test@test.com"}

# Logout
curl -s -b /tmp/jar.txt -c /tmp/jar.txt -X POST http://localhost:5001/api/auth/logout
# Expected: {"message":"Logged out"}

# Me after logout
curl -s -b /tmp/jar.txt http://localhost:5001/api/auth/me
# Expected: {"error":"Unauthorized"}

pkill -f "python app.py"
```

- [ ] **Step 3: Commit**

```bash
git add backend/app.py
git commit -m "feat: add register/login/logout/me auth routes"
```

---

## Task 3: Protect existing API routes with user scoping

**Files:**
- Modify: `backend/app.py`

- [ ] **Step 1: Replace all five existing route functions**

Replace `get_applications`, `add_application`, `update_application`, `delete_application`, `get_stats`, and `export_csv` with the versions below. Every query now filters by `session["user_id"]`:

```python
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
```

- [ ] **Step 2: Add SPA fallback + keep `__main__` block at the bottom**

After `export_csv`, add:

```python
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path.startswith("api/"):
        return jsonify({"error": "Not found"}), 404
    dist = os.path.join(app.static_folder, path)
    if path and os.path.exists(dist):
        return send_file(dist)
    return send_file(os.path.join(app.static_folder, "index.html"))

if __name__ == "__main__":
    app.run(debug=True, port=5001)
```

- [ ] **Step 3: Verify protected routes return 401 without a session**

```bash
cd /Users/nirtituani/Downloads/job_tracker_web_pen/backend
source venv/bin/activate
python app.py &
sleep 2
curl -s http://localhost:5001/api/applications
# Expected: {"error":"Unauthorized"}
curl -s http://localhost:5001/api/stats
# Expected: {"error":"Unauthorized"}
pkill -f "python app.py"
```

- [ ] **Step 4: Commit**

```bash
git add backend/app.py
git commit -m "feat: scope all application routes to logged-in user"
```

---

## Task 4: Add gunicorn to requirements

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Add gunicorn**

```
flask==3.0.0
flask-cors==4.0.0
gunicorn==21.2.0
```

- [ ] **Step 2: Install and verify**

```bash
cd /Users/nirtituani/Downloads/job_tracker_web_pen/backend
source venv/bin/activate
pip install gunicorn==21.2.0
gunicorn --version
# Expected: gunicorn (version 21.2.0)
```

- [ ] **Step 3: Commit**

```bash
git add backend/requirements.txt
git commit -m "chore: add gunicorn for production serving"
```

---

## Task 5: Auth API client (frontend)

**Files:**
- Create: `frontend/src/api/auth.js`
- Modify: `frontend/src/api/applications.js`

- [ ] **Step 1: Create `frontend/src/api/auth.js`**

```js
const API = '/api/auth';

export async function getMe() {
  const res = await fetch(`${API}/me`, { credentials: 'include' });
  if (res.status === 401) return null;
  return res.json();
}

export async function login(email, password) {
  const res = await fetch(`${API}/login`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Login failed');
  return data;
}

export async function register(email, password) {
  const res = await fetch(`${API}/register`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Registration failed');
  return data;
}

export async function logout() {
  await fetch(`${API}/logout`, { method: 'POST', credentials: 'include' });
}
```

- [ ] **Step 2: Add `credentials: 'include'` + 401 redirect to `frontend/src/api/applications.js`**

Replace the entire file:

```js
const API = '/api';

function handle401(res) {
  if (res.status === 401) {
    window.location.reload();
    throw new Error('Session expired');
  }
  return res;
}

export async function getApplications(search = '', status = 'All') {
  const params = new URLSearchParams();
  if (search) params.set('search', search);
  if (status && status !== 'All') params.set('status', status);
  const res = await fetch(`${API}/applications?${params}`, { credentials: 'include' });
  handle401(res);
  return res.json();
}

export async function getStats() {
  const res = await fetch(`${API}/stats`, { credentials: 'include' });
  handle401(res);
  return res.json();
}

export async function addApplication(data) {
  const res = await fetch(`${API}/applications`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  handle401(res);
  return res.json();
}

export async function updateApplication(id, data) {
  const res = await fetch(`${API}/applications/${id}`, {
    method: 'PUT',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  handle401(res);
  return res.json();
}

export async function deleteApplication(id) {
  const res = await fetch(`${API}/applications/${id}`, {
    method: 'DELETE',
    credentials: 'include',
  });
  handle401(res);
  return res.json();
}

export function exportCsv() {
  window.open(`${API}/export`, '_blank');
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/auth.js frontend/src/api/applications.js
git commit -m "feat: add auth API client and session credentials to requests"
```

---

## Task 6: Build AuthPage (login + register)

**Files:**
- Create: `frontend/src/pages/AuthPage.jsx`

- [ ] **Step 1: Create `frontend/src/pages/AuthPage.jsx`**

```jsx
import { useState } from 'react';
import { login, register } from '../api/auth';

export default function AuthPage({ onAuth }) {
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    if (mode === 'register' && password !== confirm) {
      setError('Passwords do not match');
      return;
    }
    setLoading(true);
    try {
      const user = mode === 'login'
        ? await login(email, password)
        : await register(email, password);
      onAuth(user);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-xl bg-primary flex items-center justify-center mx-auto mb-3">
            <span className="text-white font-bold text-lg">JT</span>
          </div>
          <h1 className="text-2xl font-primary font-bold">JOBTRACKER</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {mode === 'login' ? 'Sign in to your account' : 'Create your account'}
          </p>
        </div>

        <form onSubmit={submit} className="bg-card border border-border rounded-2xl p-6 space-y-4 shadow-sm">
          {error && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-xl px-4 py-2">
              {error}
            </div>
          )}
          <div>
            <label className="block text-sm font-medium mb-1.5">Email</label>
            <input
              type="email" required value={email} onChange={e => setEmail(e.target.value)}
              placeholder="you@email.com"
              className="w-full px-4 py-2.5 bg-background border border-border rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5">Password</label>
            <input
              type="password" required value={password} onChange={e => setPassword(e.target.value)}
              placeholder="Min. 6 characters"
              className="w-full px-4 py-2.5 bg-background border border-border rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
          </div>
          {mode === 'register' && (
            <div>
              <label className="block text-sm font-medium mb-1.5">Confirm Password</label>
              <input
                type="password" required value={confirm} onChange={e => setConfirm(e.target.value)}
                placeholder="Repeat password"
                className="w-full px-4 py-2.5 bg-background border border-border rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>
          )}
          <button
            type="submit" disabled={loading}
            className="w-full py-2.5 bg-primary text-white rounded-full text-sm font-primary font-medium hover:bg-primary/90 transition-colors disabled:opacity-60"
          >
            {loading ? 'Please wait...' : mode === 'login' ? 'Sign In' : 'Create Account'}
          </button>
        </form>

        <p className="text-center text-sm text-muted-foreground mt-4">
          {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
          <button onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(''); }}
            className="text-primary font-medium hover:underline">
            {mode === 'login' ? 'Sign up' : 'Sign in'}
          </button>
        </p>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/AuthPage.jsx
git commit -m "feat: add login/register AuthPage component"
```

---

## Task 7: Wire auth into App.jsx + Sidebar logout

**Files:**
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/components/Sidebar.jsx`

- [ ] **Step 1: Update `frontend/src/App.jsx`**

Add `getMe` import and `user` state. Show `AuthPage` if not logged in, show dashboard if logged in:

Replace the imports block and `export default function App()` opening:

```jsx
import { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import StatsCards from './components/StatsCards';
import ApplicationTable from './components/ApplicationTable';
import AddApplicationModal from './components/AddApplicationModal';
import AuthPage from './pages/AuthPage';
import { getApplications, getStats, addApplication, updateApplication, deleteApplication, exportCsv } from './api/applications';
import { getMe, logout as apiLogout } from './api/auth';
import { useSettings } from './hooks/useSettings';
import { Plus, X } from 'lucide-react';
```

Add `user` state and auth check inside `App()`, right after the existing state declarations:

```jsx
const [user, setUser] = useState(undefined); // undefined = loading, null = not logged in

useEffect(() => {
  getMe().then(setUser);
}, []);

const handleLogout = async () => {
  await apiLogout();
  setUser(null);
};
```

Add this block right before the final `return (`:

```jsx
if (user === undefined) return (
  <div className="min-h-screen bg-background flex items-center justify-center">
    <p className="text-muted-foreground text-sm">Loading...</p>
  </div>
);
if (user === null) return <AuthPage onAuth={setUser} />;
```

- [ ] **Step 2: Pass `onLogout` to `Sidebar` in the return JSX**

Change:
```jsx
<Sidebar activeView={activeView} setActiveView={setActiveView} />
```
To:
```jsx
<Sidebar activeView={activeView} setActiveView={setActiveView} user={user} onLogout={handleLogout} />
```

- [ ] **Step 3: Update `frontend/src/components/Sidebar.jsx` — add logout button**

Replace the bottom user block (the `<div className="px-4 py-4 ...">` section) with:

```jsx
export default function Sidebar({ activeView, setActiveView, user, onLogout }) {
```

And replace the footer div:

```jsx
      <div className="px-4 py-4 border-t border-sidebar-border">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-primary/20 flex items-center justify-center text-sm font-semibold text-primary">
            {user?.email?.[0]?.toUpperCase() ?? 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground truncate">{user?.email ?? ''}</p>
          </div>
          <button onClick={onLogout} title="Logout"
            className="text-muted-foreground hover:text-red-500 transition-colors flex-shrink-0">
            <LogOut size={16} />
          </button>
        </div>
      </div>
```

Add `LogOut` to the lucide import at the top of `Sidebar.jsx`:

```jsx
import { LayoutDashboard, FileText, BarChart3, Settings, LogOut } from 'lucide-react';
```

- [ ] **Step 4: Test locally**

```bash
# Kill any running servers, then:
cd /Users/nirtituani/Downloads/job_tracker_web_pen/backend
source venv/bin/activate
python app.py &
cd ../frontend
npm run dev &
sleep 3
open http://localhost:5175
```

- Verify: app shows login screen on first load
- Register a new account → lands on dashboard
- Add an application → appears in table
- Open incognito → register different email → different empty tracker
- Logout button in sidebar footer works

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.jsx frontend/src/components/Sidebar.jsx
git commit -m "feat: gate app behind auth, add logout to sidebar"
```

---

## Task 8: Render deployment files

**Files:**
- Create: `render.yaml`
- Create: `backend/build.sh`

- [ ] **Step 1: Create `render.yaml` in repo root**

```yaml
services:
  - type: web
    name: job-tracker
    runtime: python
    buildCommand: bash backend/build.sh
    startCommand: cd backend && gunicorn app:app --bind 0.0.0.0:$PORT
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        value: /data/database.db
    disk:
      name: db
      mountPath: /data
      sizeGB: 1
```

- [ ] **Step 2: Create `backend/build.sh`**

```bash
#!/usr/bin/env bash
set -e

echo "==> Installing Node deps and building React..."
cd frontend
npm install
npm run build
cd ..

echo "==> Copying React build into Flask static folder..."
rm -rf backend/static
cp -r frontend/dist backend/static

echo "==> Installing Python deps..."
cd backend
pip install -r requirements.txt

echo "==> Build complete."
```

- [ ] **Step 3: Update `app.py` static folder path for production**

The `static_folder` in app.py currently points to `../frontend/dist`. On Render the build script copies to `backend/static`. Update the Flask app instantiation line:

```python
app = Flask(__name__,
            static_folder=os.path.join(os.path.dirname(__file__), "static"),
            static_url_path="")
```

- [ ] **Step 4: Make build script executable and commit**

```bash
chmod +x backend/build.sh
git add render.yaml backend/build.sh backend/app.py
git commit -m "chore: add Render deployment config and build script"
```

---

## Task 9: Deploy to Render

- [ ] **Step 1: Push repo to GitHub**

If not already a git repo with a remote:
```bash
cd /Users/nirtituani/Downloads/job_tracker_web_pen
git remote add origin <your-github-repo-url>
git push -u origin main
```

- [ ] **Step 2: Create Render service**

1. Go to [render.com](https://render.com) → **New → Web Service**
2. Connect your GitHub repo
3. Render will detect `render.yaml` automatically — click **Apply**
4. In the dashboard, confirm these environment variables are set:
   - `SECRET_KEY` — auto-generated (done by render.yaml)
   - `DATABASE_URL` — `/data/database.db` (done by render.yaml)
5. Click **Deploy**

- [ ] **Step 3: Verify deployment**

Once deploy finishes (takes ~3 minutes):
```
https://job-tracker.onrender.com/api/auth/me
# Expected: {"error":"Unauthorized"} — means Flask is running
```

Open the root URL in browser → login screen should appear.

- [ ] **Step 4: Register your account on the live site**

Register at the live URL. Add a test application. Confirm it persists after a page refresh.

---

## Self-Review Notes

- All spec requirements covered: users table, user_id scoping, auth routes, session auth, SPA fallback, gunicorn, render.yaml, disk persistence
- `credentials: 'include'` added to all fetch calls — required for cookies to work cross-origin during local dev and on Render
- `CORS(app, supports_credentials=True)` set in Task 1 — required for credentials to work
- Existing data (user_id=0) won't be visible to any new user — safe migration
- Static folder path updated for production (Task 8 Step 3) while keeping local dev working via Vite proxy
