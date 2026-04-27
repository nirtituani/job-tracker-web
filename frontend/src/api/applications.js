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
