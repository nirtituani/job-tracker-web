# Auth + Deployment Design — Job Tracker Web App
**Date:** 2026-04-27

## Goal
Make the app publicly accessible on the internet, with each user having their own private job tracker. Deploy as a single service on Render (free tier).

## Architecture

Single service: Flask serves both the API and the built React frontend as static files. SQLite is the database, persisted on a Render disk.

```
Browser → Render (Flask)
              ├── /api/*         → Flask routes (authenticated)
              └── /*             → React build (static files)
```

## Backend Changes

### New: `users` table
```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TEXT DEFAULT ''
)
```

### `applications` table
Add `user_id INTEGER` column. All queries filter by the logged-in user's id.

### New API routes
- `POST /api/auth/register` — create account (email + password)
- `POST /api/auth/login` — return session cookie
- `POST /api/auth/logout` — clear session
- `GET /api/auth/me` — return current user info

### Auth mechanism
- Flask `session` (server-side, cookie-based)
- Passwords hashed with `werkzeug.security` (bcrypt-compatible, already a Flask dependency)
- All `/api/applications` and `/api/stats` routes require active session; return 401 if not logged in

### Static file serving
Flask serves `frontend/dist` as static files. Any non-API route returns `index.html` (SPA fallback).

## Frontend Changes

### New screens
- `/login` — email + password form
- `/register` — email + password + confirm form

### Auth flow
- On app load, call `GET /api/auth/me`. If 401 → show login screen. If 200 → show dashboard.
- After login/register → redirect to dashboard.
- Logout button in sidebar footer.

### API client
Add `401` handling to all fetch calls — redirect to login on auth failure.

## Deployment (Render)

### Files to add
- `render.yaml` — Render service config
- `backend/build.sh` — script that builds React then starts Flask

### Render config
- Service type: Web Service
- Runtime: Python
- Build command: install Node + npm deps, run `npm run build`, copy `dist` to Flask static folder, install Python deps
- Start command: `gunicorn app:app`
- Disk: 1GB mounted at `/data` for SQLite

### Environment variables on Render
- `SECRET_KEY` — Flask session secret (set in Render dashboard)
- `DATABASE_URL` — path to SQLite file on persistent disk

## What stays the same
- All existing application fields and API shape
- Settings (localStorage, per-browser)
- Export CSV

## Out of scope
- Password reset / email verification
- OAuth (Google, GitHub)
- Multiple roles / admin
