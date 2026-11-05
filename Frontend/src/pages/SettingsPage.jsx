import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { BellRing, Building2, Check, ChevronRight, Clock3, Database, LockKeyhole, RotateCcw, Save, Settings2, ShieldCheck, SlidersHorizontal } from 'lucide-react';
import { getAuthSession, logout } from '../services/api';
import { recordAuditEvent } from '../services/auditLogService';
import { DEFAULT_WORKSPACE_SETTINGS, getWorkspaceSettings, saveWorkspaceSettings } from '../services/workspaceSettingsService';
import './governance-pages.css';

const sections = [
  { id: 'workspace', title: 'Workspace', description: 'Workspace profile and procurement defaults', icon: Building2 },
  { id: 'notifications', title: 'Notifications', description: 'Choose which updates appear in this workspace', icon: BellRing },
  { id: 'preferences', title: 'Preferences', description: 'Set display and navigation defaults', icon: SlidersHorizontal },
  { id: 'security', title: 'Security', description: 'Review session and access controls', icon: LockKeyhole },
];

function Field({ label, hint, children }) {
  return <label className="settings-field"><span>{label}</span>{children}{hint && <small>{hint}</small>}</label>;
}

function Toggle({ checked, onChange, title, description }) {
  return <div className="settings-toggle-row"><div><b>{title}</b><small>{description}</small></div><button type="button" className={`settings-switch ${checked ? 'on' : ''}`} role="switch" aria-checked={checked} aria-label={title} onClick={() => onChange(!checked)}><i /></button></div>;
}

export default function SettingsPage() {
  const navigate = useNavigate();
  const [settings, setSettings] = useState(() => getWorkspaceSettings());
  const [activeSection, setActiveSection] = useState('workspace');
  const [saved, setSaved] = useState(false);
  const [signingOut, setSigningOut] = useState(false);
  const [saveError, setSaveError] = useState('');
  const account = getAuthSession()?.user;
  const currentSection = sections.find(item => item.id === activeSection) || sections[0];
  const Icon = currentSection.icon;

  useEffect(() => {
    const sync = () => setSettings(getWorkspaceSettings());
    window.addEventListener('procuremind:settings-updated', sync);
    return () => window.removeEventListener('procuremind:settings-updated', sync);
  }, []);

  const dirtyFields = useMemo(() => Object.keys(DEFAULT_WORKSPACE_SETTINGS).filter(key => settings[key] !== getWorkspaceSettings()[key]), [settings]);
  const update = (key, value) => {
    setSaved(false);
    setSettings(current => ({ ...current, [key]: value }));
  };

  const save = event => {
    event.preventDefault();
    setSaveError('');
    const previous = getWorkspaceSettings();
    const changed = Object.keys(settings).filter(key => settings[key] !== previous[key]);
    try {
      const next = saveWorkspaceSettings(settings);
      setSettings(next);
      if (changed.length) {
        recordAuditEvent({
          category: 'Settings',
          action: 'Workspace settings updated',
          entityType: 'Workspace settings',
          entityId: next.workspaceName || 'workspace',
          outcome: 'Saved locally',
          summary: `${changed.length} workspace preference${changed.length === 1 ? '' : 's'} changed.`,
          details: { changedFields: changed },
        });
      }
      setSaved(true);
      window.setTimeout(() => setSaved(false), 2800);
    } catch {
      setSaveError('Settings could not be saved in this browser. Check available local storage and try again.');
    }
  };

  const reset = () => {
    const previous = getWorkspaceSettings();
    const changed = Object.keys(DEFAULT_WORKSPACE_SETTINGS).filter(key => previous[key] !== DEFAULT_WORKSPACE_SETTINGS[key]);
    const next = saveWorkspaceSettings({ ...DEFAULT_WORKSPACE_SETTINGS });
    setSettings(next);
    setSaved(false);
    if (changed.length) {
      recordAuditEvent({ category: 'Settings', action: 'Workspace settings restored to defaults', entityType: 'Workspace settings', outcome: 'Saved locally', details: { changedFields: changed } });
    }
  };

  const signOut = async () => {
    setSigningOut(true);
    recordAuditEvent({ category: 'System', action: 'User signed out', entityType: 'Account session', entityId: account?.email || 'current-session', outcome: 'Signed out', summary: 'The active workspace session was signed out.' });
    try {
      await logout();
    } finally {
      navigate('/login', { replace: true });
    }
  };

  return (
    <main className="governance-page settings-page">
      <header className="gov-page-heading">
        <div>
          <div className="gov-eyebrow"><span className="gov-live-dot" /> GOVERNANCE / CONFIGURATION</div>
          <h1>Workspace Settings</h1>
          <p>Manage workspace defaults, notifications, and your local interface preferences.</p>
        </div>
        <div className="settings-heading-status"><span><i /> Preferences ready</span><small>Changes are saved in this browser</small></div>
      </header>

      <div className="gov-demo-note"><Database size={15} /><span>This frontend workspace stores these settings locally. Authentication and role permissions remain controlled by Supabase and Backend.</span></div>

      <div className="settings-layout">
        <nav className="settings-nav gov-panel" aria-label="Settings sections">
          <div className="settings-nav-title">SETTINGS</div>
          {sections.map(section => {
            const SectionIcon = section.icon;
            return <button type="button" key={section.id} className={`settings-nav-item ${activeSection === section.id ? 'active' : ''}`} onClick={() => setActiveSection(section.id)}><SectionIcon size={17} /><span><b>{section.title}</b><small>{section.description}</small></span><ChevronRight size={14} /></button>;
          })}
          <div className="settings-account-card"><span className="settings-account-avatar">{(account?.email || '?').slice(0, 2).toUpperCase()}</span><div><b>{account?.email || 'Not signed in'}</b><small>{account?.email ? 'Signed-in account' : 'No active session'}</small></div></div>
          {account?.email && <button className="settings-signout" type="button" onClick={signOut} disabled={signingOut}>{signingOut ? 'Signing out…' : 'Sign out of this session'}</button>}
        </nav>

        <form className="settings-content gov-panel" onSubmit={save}>
          <div className="gov-panel-heading settings-panel-heading"><div><span className="gov-panel-icon"><Icon size={17} /></span><div><h2>{currentSection.title}</h2><p>{currentSection.description}</p></div></div><span className="settings-local-tag"><i /> LOCAL</span></div>

          {activeSection === 'workspace' && <div className="settings-form-grid">
            <Field label="Workspace name" hint="Shown in the dashboard workspace switcher."><input value={settings.workspaceName} onChange={event => update('workspaceName', event.target.value)} maxLength={80} required /></Field>
            <Field label="Default currency" hint="Used for display preferences in the workspace."><select value={settings.currency} onChange={event => update('currency', event.target.value)}><option value="USD">USD — US Dollar</option><option value="IDR">IDR — Indonesian Rupiah</option><option value="SGD">SGD — Singapore Dollar</option><option value="EUR">EUR — Euro</option></select></Field>
            <Field label="Workspace timezone" hint="Used when displaying audit timestamps and dates."><select value={settings.timezone} onChange={event => update('timezone', event.target.value)}><option>Asia/Makassar</option><option>Asia/Jakarta</option><option>Asia/Singapore</option><option>UTC</option><option>America/New_York</option><option>Europe/London</option></select></Field>
          </div>}

          {activeSection === 'notifications' && <div className="settings-toggle-list">
            <Toggle checked={settings.criticalAlerts} onChange={value => update('criticalAlerts', value)} title="Critical fraud alerts" description="Show a workspace notification when a high-severity review item is added." />
            <Toggle checked={settings.approvalNotifications} onChange={value => update('approvalNotifications', value)} title="Approval requests" description="Show a notification when an approval request is waiting for review." />
            <Toggle checked={settings.weeklyDigest} onChange={value => update('weeklyDigest', value)} title="Weekly procurement digest" description="Add a weekly activity summary to the local notification preference set." />
            <div className="settings-info-card"><BellRing size={16} /><span>These switches save notification preferences locally. No email or external notification is sent.</span></div>
          </div>}

          {activeSection === 'preferences' && <div className="settings-form-grid">
            <Field label="Default dashboard page" hint="Choose the page opened from the workspace home link."><select value={settings.defaultModule} onChange={event => update('defaultModule', event.target.value)}><option value="/dashboard">Overview</option><option value="/dashboard/purchase-orders">Purchase Orders</option><option value="/negotiation">Negotiation Copilot</option><option value="/fraud-detection">Fraud Detection</option><option value="/dashboard/audit-logs">Audit Logs</option></select></Field>
            <Field label="Date format" hint="Applied to local audit and activity views."><select value={settings.dateFormat} onChange={event => update('dateFormat', event.target.value)}><option>DD MMM YYYY</option><option>MM/DD/YYYY</option><option>YYYY-MM-DD</option></select></Field>
            <div className="settings-full-row"><Toggle checked={settings.compactTables} onChange={value => update('compactTables', value)} title="Compact tables" description="Use denser rows in tables to fit more procurement records on screen." /></div>
          </div>}

          {activeSection === 'security' && <div className="settings-security-content">
            <div className="settings-security-banner"><span><ShieldCheck size={18} /></span><div><b>Authentication is managed by Supabase</b><small>Role claims and approval permissions are verified by the Backend on every protected request.</small></div></div>
            <Field label="Local session timeout preference" hint="This preference is saved for the workspace UI. It does not override Supabase token expiry."><div className="settings-input-with-unit"><Clock3 size={15} /><select value={settings.sessionTimeout} onChange={event => update('sessionTimeout', event.target.value)}><option value="15">15 minutes</option><option value="30">30 minutes</option><option value="60">1 hour</option><option value="240">4 hours</option></select></div></Field>
            <div className="settings-security-row"><div><b>Current account</b><small>{account?.email || 'No active session'}</small></div><span className="settings-verified"><Check size={13} /> Active session</span></div>
            <p className="settings-security-footnote">No passwords, API keys, or Supabase role claims are stored on this page.</p>
          </div>}

          {saveError && <p className="settings-error" role="alert">{saveError}</p>}
          <footer className="settings-form-footer"><button className="gov-button gov-button-quiet" type="button" onClick={reset}><RotateCcw size={14} /> Restore defaults</button><span>{saved ? <i className="settings-saved"><Check size={13} /> Saved just now</i> : dirtyFields.length > 0 ? `${dirtyFields.length} unsaved change${dirtyFields.length === 1 ? '' : 's'}` : 'All changes saved'}</span><button className="gov-button gov-button-primary" type="submit"><Save size={14} /> Save changes</button></footer>
        </form>
      </div>
    </main>
  );
}
