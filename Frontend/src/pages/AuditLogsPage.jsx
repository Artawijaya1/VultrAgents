import { useEffect, useMemo, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Activity, CalendarDays, ChevronDown, Download, FileSearch, Filter, Search, ShieldCheck, X } from 'lucide-react';
import { getAuditEvents, refreshAuditEvents, subscribeToAuditEvents } from '../services/auditLogService';
import { getWorkspaceSettings } from '../services/workspaceSettingsService';
import './governance-pages.css';

const categories = ['All events', 'Procurement', 'Negotiation', 'Fraud', 'Agent', 'Settings', 'System'];
const formatDate = value => {
  const settings = getWorkspaceSettings();
  const locale = settings.dateFormat === 'MM/DD/YYYY' ? 'en-US' : 'en-GB';
  const date = new Intl.DateTimeFormat(locale, {
    timeZone: settings.timezone,
    day: '2-digit',
    month: settings.dateFormat === 'DD MMM YYYY' ? 'short' : '2-digit',
    year: 'numeric',
  }).format(new Date(value));
  const time = new Intl.DateTimeFormat('en-GB', { timeZone: settings.timezone, hour: '2-digit', minute: '2-digit' }).format(new Date(value));
  return `${date} · ${time}`;
};

function exportCsv(events) {
  const columns = ['timestamp', 'category', 'action', 'entityType', 'entityId', 'actor', 'outcome', 'summary'];
  const escape = value => `"${String(value ?? '').replaceAll('"', '""')}"`;
  const csv = [columns.join(','), ...events.map(event => columns.map(key => escape(event[key])).join(','))].join('\r\n');
  const url = URL.createObjectURL(new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8' }));
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `procuremind-audit-logs-${new Date().toISOString().slice(0, 10)}.csv`;
  anchor.click();
  URL.revokeObjectURL(url);
}

function Metric({ icon: Icon, label, value, note }) {
  return <article className="gov-metric"><span className="gov-metric-icon"><Icon size={17} /></span><div><small>{label}</small><strong>{value}</strong><span>{note}</span></div></article>;
}

export default function AuditLogsPage() {
  const outlet = useOutletContext() ?? {};
  const [events, setEvents] = useState(() => getAuditEvents());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('All events');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    const unsubscribe = subscribeToAuditEvents(() => setEvents(getAuditEvents()));
    refreshAuditEvents().then(setEvents).catch(err => setError(err?.message || 'Could not load audit logs from Backend.')).finally(() => setLoading(false));
    return unsubscribe;
  }, []);

  const filtered = useMemo(() => {
    const searchTerm = `${query} ${outlet.search || ''}`.trim().toLowerCase();
    return events.filter(event => {
      const text = [event.action, event.category, event.entityType, event.entityId, event.actor, event.outcome, event.summary, JSON.stringify(event.details || {})].join(' ').toLowerCase();
      const timestamp = new Date(event.timestamp || event.date || 0);
      const afterStart = !fromDate || timestamp >= new Date(`${fromDate}T00:00:00`);
      const beforeEnd = !toDate || timestamp <= new Date(`${toDate}T23:59:59`);
      return (!searchTerm || text.includes(searchTerm))
        && (category === 'All events' || event.category === category)
        && afterStart && beforeEnd;
    });
  }, [events, query, outlet.search, category, fromDate, toDate]);

  const today = new Date().toLocaleDateString('en-CA');
  const todayCount = events.filter(event => new Date(event.timestamp).toLocaleDateString('en-CA') === today).length;
  const reviewCount = events.filter(event => /review|pending|flagged/i.test(`${event.outcome} ${event.action}`)).length;
  const categoriesUsed = new Set(events.map(event => event.category)).size;

  return (
    <main className="governance-page audit-page">
      <header className="gov-page-heading">
        <div>
          <div className="gov-eyebrow"><span className="gov-live-dot" /> GOVERNANCE / ACTIVITY TRAIL</div>
          <h1>Audit Logs</h1>
          <p>Review a searchable timeline of procurement, AI, and workspace activity.</p>
        </div>
        <button className="gov-button gov-button-primary" onClick={() => exportCsv(filtered)} disabled={!filtered.length}><Download size={15} /> Export CSV</button>
      </header>

      {error && <div className="gov-demo-note" role="alert"><ShieldCheck size={15} /><span>{error}</span><button className="gov-button gov-button-quiet" onClick={() => { setLoading(true); setError(''); refreshAuditEvents().then(setEvents).catch(err => setError(err?.message || 'Could not load audit logs from Backend.')).finally(() => setLoading(false)); }}>Retry</button></div>}

      <section className="gov-metric-grid" aria-label="Audit log summary">
        <Metric icon={Activity} label="TOTAL EVENTS" value={events.length.toLocaleString()} note="Available in this workspace" />
        <Metric icon={CalendarDays} label="RECORDED TODAY" value={todayCount.toLocaleString()} note="Across all activity types" />
        <Metric icon={FileSearch} label="REVIEW SIGNALS" value={reviewCount.toLocaleString()} note="Pending, flagged, or review actions" />
        <Metric icon={Filter} label="EVENT CATEGORIES" value={categoriesUsed.toLocaleString()} note="Procurement and governance" />
      </section>

      <section className="gov-panel audit-panel">
        <div className="gov-panel-heading">
          <div><span className="gov-panel-icon"><Activity size={16} /></span><div><h2>Activity timeline</h2><p>{filtered.length} event{filtered.length === 1 ? '' : 's'} match the current filters</p></div></div>
          {(query || category !== 'All events' || fromDate || toDate) && <button className="gov-button gov-button-quiet" onClick={() => { setQuery(''); setCategory('All events'); setFromDate(''); setToDate(''); }}>Clear filters</button>}
        </div>

        <div className="audit-filters">
          <label className="gov-search"><Search size={15} /><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Search event, actor, or record…" aria-label="Search audit events" /></label>
          <label className="gov-select-wrap"><span>Category</span><select value={category} onChange={event => setCategory(event.target.value)}>{categories.map(item => <option key={item}>{item}</option>)}</select><ChevronDown size={13} /></label>
          <label className="gov-date-wrap"><span>From</span><input type="date" value={fromDate} onChange={event => setFromDate(event.target.value)} aria-label="From date" /></label>
          <label className="gov-date-wrap"><span>To</span><input type="date" value={toDate} onChange={event => setToDate(event.target.value)} aria-label="To date" /></label>
        </div>

        <div className="audit-table-scroll">
          <table className="audit-table">
            <thead><tr><th>EVENT</th><th>RECORD</th><th>ACTOR</th><th>TIME</th><th>OUTCOME</th><th><span className="sr-only">Details</span></th></tr></thead>
            <tbody>
              {filtered.map(event => (
                <tr key={event.id} tabIndex={0} onClick={() => setSelected(event)} onKeyDown={key => { if (key.key === 'Enter' || key.key === ' ') { key.preventDefault(); setSelected(event); } }}>
                  <td><div className="audit-event-cell"><span className={`audit-category-mark ${event.category.toLowerCase()}`}><Activity size={14} /></span><div><b>{event.action}</b><small>{event.category}</small></div></div></td>
                  <td><b className="audit-entity">{event.entityId || 'Workspace'}</b><small className="audit-entity-type">{event.entityType || 'Workspace'}</small></td>
                  <td><span className="audit-actor"><i>{String(event.actor || '?').slice(0, 1).toUpperCase()}</i>{event.actor || 'System'}</span></td>
                  <td className="audit-time">{formatDate(event.timestamp || event.date)}</td>
                  <td><span className={`audit-outcome ${String(event.outcome || '').toLowerCase().replaceAll(' ', '-')}`}>{event.outcome || 'Recorded'}</span></td>
                  <td><button className="audit-open" aria-label={`View details for ${event.action}`} onClick={click => { click.stopPropagation(); setSelected(event); }}>View</button></td>
                </tr>
              ))}
              {!filtered.length && <tr><td className="audit-empty" colSpan="6"><Search size={18} /><b>{loading ? 'Loading audit events…' : error ? 'Audit events are unavailable.' : 'No database audit events yet.'}</b><span>{loading ? 'Reading records from Backend.' : error ? 'Retry after checking the API connection.' : 'Backend will show activity as database actions are recorded.'}</span></td></tr>}
            </tbody>
          </table>
        </div>
        <footer className="audit-table-footer"><span>Showing {filtered.length} of {events.length} events</span><span><span className="audit-footer-dot" /> New local events appear automatically</span></footer>
      </section>

      {selected && <div className="gov-overlay" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) setSelected(null); }}>
        <aside className="gov-detail-drawer" role="dialog" aria-modal="true" aria-labelledby="audit-detail-title">
          <button className="gov-close" onClick={() => setSelected(null)} aria-label="Close event details"><X size={17} /></button>
          <span className="gov-detail-icon"><ShieldCheck size={20} /></span>
          <div className="gov-eyebrow">{selected.category} EVENT</div>
          <h2 id="audit-detail-title">{selected.action}</h2>
          <p>{selected.summary || selected.action}</p>
          <dl className="gov-detail-list">
            <div><dt>Event ID</dt><dd>{selected.id}</dd></div>
            <div><dt>Timestamp</dt><dd>{formatDate(selected.timestamp || selected.date)}</dd></div>
            <div><dt>Actor</dt><dd>{selected.actor || 'System'}</dd></div>
            <div><dt>Record</dt><dd>{selected.entityType || 'Workspace'} · {selected.entityId || '—'}</dd></div>
            <div><dt>Outcome</dt><dd>{selected.outcome || 'Recorded'}</dd></div>
            {selected.details && Object.entries(selected.details).map(([key, value]) => <div key={key}><dt>{key.replaceAll(/([A-Z])/g, ' $1')}</dt><dd>{typeof value === 'object' ? JSON.stringify(value) : String(value)}</dd></div>)}
          </dl>
        </aside>
      </div>}
    </main>
  );
}
