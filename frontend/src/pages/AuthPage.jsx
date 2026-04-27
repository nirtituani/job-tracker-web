import { useState } from 'react';
import { login, register } from '../api/auth';

export default function AuthPage({ onAuth }) {
  const [mode, setMode] = useState('login');
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
      <div className="w-full max-w-sm px-4">
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

          <div className="relative flex items-center gap-3">
            <div className="flex-1 h-px bg-border" />
            <span className="text-xs text-muted-foreground">or</span>
            <div className="flex-1 h-px bg-border" />
          </div>

          <button
            type="button"
            onClick={() => window.location.href = '/api/auth/google'}
            className="w-full py-2.5 border border-border rounded-full text-sm font-primary font-medium hover:bg-muted transition-colors flex items-center justify-center gap-2"
          >
            <svg width="16" height="16" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
            Continue with Google
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
