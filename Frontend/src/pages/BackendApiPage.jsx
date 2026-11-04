import { useCallback, useEffect, useState } from 'react';
import { Activity, AlertTriangle, CheckCircle2, CircleHelp, RefreshCw, ShieldAlert, XCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { ApiError, apiRoutes, getApiHealth, getApiReadiness } from '../services/api';
import './backend-api.css';
const initialCheck = { state: 'loading', message: 'Checking…' };
function errorMessage(error) {
    if (error instanceof ApiError) {
        if (error.status === 503)
            return `Not ready: ${error.message}`;
        return error.message;
    }
    return 'Could not check the backend.';
}
function StatusCard({ title, detail, check, path, icon: Icon, }) {
    const StatusIcon = check.state === 'loading'
        ? RefreshCw
        : check.state === 'online'
            ? CheckCircle2
            : check.state === 'degraded'
                ? AlertTriangle
                : XCircle;
    return (<article className={`api-status-card api-${check.state}`}>
      <div className="api-status-card-top">
        <span className="api-status-icon"><Icon size={18}/></span>
        <span className="api-status-state"><StatusIcon size={14}/>{check.state}</span>
      </div>
      <h2>{title}</h2>
      <p>{detail}</p>
      <code>{path}</code>
      <small>{check.message}</small>
    </article>);
}
export default function BackendApiPage() {
    const [health, setHealth] = useState(initialCheck);
    const [readiness, setReadiness] = useState(initialCheck);
    const [checking, setChecking] = useState(false);
    const checkBackend = useCallback(async () => {
        setChecking(true);
        setHealth(initialCheck);
        setReadiness(initialCheck);
        const [healthResult, readinessResult] = await Promise.allSettled([
            getApiHealth(),
            getApiReadiness(),
        ]);
        if (healthResult.status === 'fulfilled') {
            const result = healthResult.value;
            setHealth({ state: 'online', message: `API responded: ${result.status}` });
        }
        else {
            setHealth({ state: 'offline', message: errorMessage(healthResult.reason) });
        }
        if (readinessResult.status === 'fulfilled') {
            setReadiness({ state: 'online', message: `Database responded: ${readinessResult.value.status}` });
        }
        else {
            const state = readinessResult.reason instanceof ApiError && readinessResult.reason.status === 503
                ? 'degraded'
                : 'offline';
            setReadiness({ state, message: errorMessage(readinessResult.reason) });
        }
        setChecking(false);
    }, []);
    useEffect(() => {
        void checkBackend();
    }, [checkBackend]);
    return (<main className="backend-api-page">
      <div className="dashboard-eyebrow"><span className="live-dot"/> BACKEND INTEGRATION</div>
      <div className="backend-api-heading">
        <div>
          <h1>Backend API</h1>
          <p>Live connection status and the current integration boundary.</p>
        </div>
        <button className="dashboard-control" onClick={() => void checkBackend()} disabled={checking}>
          <RefreshCw size={15} className={checking ? 'api-spinning' : ''}/>
          {checking ? 'Checking…' : 'Check connection'}
        </button>
      </div>

      <section className="api-status-grid" aria-label="Backend connection status">
        <StatusCard title="API server" detail="HTTP service availability" check={health} path={apiRoutes.health} icon={Activity}/>
        <StatusCard title="Database" detail="Backend database readiness" check={readiness} path={apiRoutes.readiness} icon={CheckCircle2}/>
      </section>

      <section className="api-endpoint-panel">
        <div className="api-panel-heading">
          <span className="api-panel-icon"><CircleHelp size={17}/></span>
          <div><h2>Integration status</h2><p>Routes registered by the backend API v1.</p></div>
        </div>
        <div className="api-endpoint-list">
          <div className="api-endpoint-row">
            <span className="api-endpoint-mark live"><CheckCircle2 size={15}/></span>
            <div><b>Health checks</b><small>Available to this frontend without credentials.</small></div>
            <code>GET /health · /ready</code>
          </div>
          <div className="api-endpoint-row">
            <span className="api-endpoint-mark live"><CheckCircle2 size={15}/></span>
            <div><b>Authenticated data</b><small>Profile and item CRUD; user listing and updates are admin-only.</small></div>
            <code>Bearer token · users · items</code>
          </div>
          <div className="api-endpoint-row">
            <span className="api-endpoint-mark warning"><ShieldAlert size={15}/></span>
            <div><b>Internal agent routes</b><small>Require a private API key. It must not be embedded in frontend code.</small></div>
            <code>{apiRoutes.internal}</code>
          </div>
          <div className="api-endpoint-row">
            <span className="api-endpoint-mark pending"><AlertTriangle size={15}/></span>
            <div><b>Procurement workflows</b><small>Most routes are registered placeholders and return HTTP 501 until backend logic is implemented.</small></div>
            <code>/api/v1/*</code>
          </div>
        </div>
      </section>

      <p className="api-security-note">
        <ShieldAlert size={15}/>
        API data is only requested after sign-in. Account provisioning remains in Supabase Auth; the internal API key is never sent to the browser.
      </p>
      <Link to="/dashboard/data" className="dashboard-control">Open authenticated data management</Link>
    </main>);
}
