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
