import { useEffect, useState } from 'react';
import { Link, Navigate, Outlet, useLocation } from 'react-router-dom';
import { ApiError, getAuthSession, getCurrentUser } from '../services/api';
import './auth-pages.css';
export default function AuthenticatedRoute() {
    const [state, setState] = useState('checking');
    const [message, setMessage] = useState('');
    const [attempt, setAttempt] = useState(0);
    const location = useLocation();
    const from = `${location.pathname}${location.search}`;
    useEffect(() => {
        let active = true;
        if (!getAuthSession()) {
            setState('failed');
            return () => { active = false; };
        }
        setState('checking');
        getCurrentUser().then(() => {
            if (active)
                setState('allowed');
        }).catch((error) => {
            if (!active)
                return;
            if (error instanceof ApiError && error.status === 401) {
                setState('failed');
                return;
            }
            setMessage(error instanceof Error ? error.message : 'Could not verify your session.');
            setState('failed');
        });
        return () => { active = false; };
    }, [attempt]);
    if (state === 'checking') {
        return <div className="auth-checking" role="status">Verifying your session…</div>;
    }
    if (state === 'allowed')
        return <Outlet />;
    if (!getAuthSession()) {
        return <Navigate to="/login" replace state={{ from }}/>;
    }
    return (<div className="auth-checking">
      <div className="auth-check-error">
        <h1>Could not verify your session</h1>
        <p>{message || 'Your sign-in session has expired.'}</p>
        <button className="auth-submit" onClick={() => setAttempt(value => value + 1)}>Try again</button>
        <Link to="/login" state={{ from }} className="auth-back">Sign in again</Link>
      </div>
    </div>);
}
