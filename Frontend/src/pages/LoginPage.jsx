import { useState } from 'react';
import { ArrowRight, ShieldCheck } from 'lucide-react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import Logo from '../components/Logo';
import { ApiError, getAuthSession, login } from '../services/api';
import './auth-pages.css';
export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const navigate = useNavigate();
    const location = useLocation();
    const state = location.state;
    const destination = state?.from?.startsWith('/dashboard/') ? state.from : '/dashboard/data';
    async function submit(event) {
        event.preventDefault();
        setError('');
        setSubmitting(true);
        try {
            await login(email.trim(), password);
            navigate(destination, { replace: true });
        }
        catch (reason) {
            if (reason instanceof ApiError && reason.status === 503) {
                setError('Supabase authentication is not configured on the backend yet.');
            }
            else {
                setError(reason instanceof Error ? reason.message : 'Could not sign in.');
            }
        }
        finally {
            setSubmitting(false);
        }
    }
    if (getAuthSession())
        return <Navigate to={destination} replace/>;
    return (<main className="auth-page">
      <section className="auth-card">
        <div className="auth-brand"><Logo /></div>
        <span className="auth-kicker"><ShieldCheck size={14}/> SECURE WORKSPACE ACCESS</span>
        <h1>Welcome back</h1>
        <p className="auth-description">Sign in with your Supabase account to manage your profile and API data.</p>
        <form className="auth-form" onSubmit={event => void submit(event)}>
          <label htmlFor="login-email">Email address</label>
          <input id="login-email" type="email" autoComplete="username" required value={email} onChange={event => setEmail(event.target.value)}/>
          <label htmlFor="login-password">Password</label>
          <input id="login-password" type="password" autoComplete="current-password" required value={password} onChange={event => setPassword(event.target.value)}/>
          {error && <p className="auth-error" role="alert">{error}</p>}
          <button className="auth-submit" type="submit" disabled={submitting}>
            {submitting ? 'Signing in…' : 'Sign in'} <ArrowRight size={16}/>
          </button>
        </form>
        <p className="auth-footnote">Accounts are provisioned in Supabase; registration is not available here.</p>
        <Link to="/" className="auth-back">Back to home</Link>
      </section>
    </main>);
}
