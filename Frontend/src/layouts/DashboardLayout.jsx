import { useEffect, useState } from 'react';
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom';
import { Activity, Bell, ChevronDown, ChevronLeft, ChevronRight, ClipboardList, Database, FileText, Handshake, LayoutDashboard, Menu, MessageSquare, Search, Settings, ShieldAlert, ShieldCheck, Users, X } from 'lucide-react';
import Logo from '../components/Logo';
import { getAuthSession } from '../services/api';
import { getWorkspaceSettings } from '../services/workspaceSettingsService';
import './dashboard.css';
import './dashboard-api-link.css';
const sections = [
    { label: 'WORKSPACE', links: [{ title: 'Overview', to: '/dashboard', icon: LayoutDashboard }, { title: 'Data management', to: '/dashboard/data', icon: Database }, { title: 'Backend API', to: '/dashboard/api', icon: Activity }] },
    { label: 'AI AGENTS', links: [{ title: 'Negotiation Copilot', to: '/negotiation', icon: Handshake }, { title: 'Fraud Detection', to: '/fraud-detection', icon: ShieldAlert }, { title: 'Agent Chat', to: '/dashboard/chat', icon: MessageSquare }] },
    { label: 'PROCUREMENT', links: [{ title: 'Purchase Orders', to: '/dashboard/purchase-orders', icon: ClipboardList }, { title: 'Suppliers', to: '/dashboard/suppliers', icon: Users }, { title: 'Invoices & Contracts', to: '/dashboard/invoices', icon: FileText }] },
    { label: 'GOVERNANCE', links: [{ title: 'Audit Logs', to: '/dashboard/audit-logs', icon: ShieldCheck }, { title: 'Settings', to: '/dashboard/settings', icon: Settings }] },
];
export default function DashboardLayout() {
    const [collapsed, setCollapsed] = useState(false);
    const [drawerOpen, setDrawerOpen] = useState(false);
    const [notificationsOpen, setNotificationsOpen] = useState(false);
    const [profileOpen, setProfileOpen] = useState(false);
    const [search, setSearch] = useState('');
    const [workspaceSettings, setWorkspaceSettings] = useState(() => getWorkspaceSettings());
    const location = useLocation();
    const accountEmail = getAuthSession()?.user.email;
    const accountName = accountEmail?.split('@')[0] ?? 'Guest account';
    const accountInitials = accountEmail ? accountEmail.slice(0, 2).toUpperCase() : 'G';
    const title = sections.flatMap(section => section.links).find(link => link.to === location.pathname)?.title ?? 'Overview';
    const dismissMenus = () => { setNotificationsOpen(false); setProfileOpen(false); };
    useEffect(() => {
      const syncSettings = () => setWorkspaceSettings(getWorkspaceSettings());
      window.addEventListener('procuremind:settings-updated', syncSettings);
      return () => window.removeEventListener('procuremind:settings-updated', syncSettings);
    }, []);
    const notifications = [
      workspaceSettings.criticalAlerts && { label: 'High risk alert', detail: 'Payment change needs attention · 2 hrs ago', tone: 'red' },
      workspaceSettings.approvalNotifications && { label: 'Review required', detail: 'Price benchmark is ready · 8 min ago', tone: 'amber' },
      workspaceSettings.weeklyDigest && { label: 'Weekly digest', detail: 'Your procurement activity summary is ready.', tone: '' },
    ].filter(Boolean);
    return <div className={`dashboard-app ${collapsed ? 'sidebar-collapsed' : ''} ${workspaceSettings.compactTables ? 'compact-tables' : ''}`}>
    {drawerOpen && <button className="dashboard-scrim" aria-label="Close navigation" onClick={() => setDrawerOpen(false)}/>}
    <aside className={`dashboard-sidebar ${drawerOpen ? 'drawer-open' : ''}`}>
      <div className="sidebar-brand"><Logo /><button className="sidebar-collapse" onClick={() => setCollapsed(!collapsed)} aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}>{collapsed ? <ChevronRight size={16}/> : <ChevronLeft size={16}/>}</button><button className="drawer-close" onClick={() => setDrawerOpen(false)} aria-label="Close navigation"><X size={18}/></button></div>
      <div className="workspace-switch"><span className="workspace-mark">{workspaceSettings.workspaceName.slice(0, 1).toUpperCase()}</span><span className="workspace-text"><b>{workspaceSettings.workspaceName}</b><small>Enterprise workspace</small></span><ChevronDown size={14}/></div>
      <nav className="sidebar-nav" aria-label="Dashboard navigation">{sections.map(section => <div className="nav-section" key={section.label}><span className="nav-section-label">{section.label}</span>{section.links.map(link => <NavLink end={link.to === '/dashboard'} to={link.to} onClick={() => setDrawerOpen(false)} className={({ isActive }) => `side-link ${isActive ? 'active' : ''}`} key={link.to} title={collapsed ? link.title : undefined}><link.icon size={17}/><span>{link.title}</span></NavLink>)}</div>)}</nav>
      <Link to="/dashboard/api" className="sidebar-foot"><span className="security-indicator"><Activity size={15}/></span><span className="security-copy"><b>Backend API</b><small>View live connection</small></span></Link>
    </aside>
    <div className="dashboard-main">
      <header className="dashboard-topbar"><div className="topbar-left"><button className="drawer-trigger" onClick={() => setDrawerOpen(true)} aria-label="Open navigation"><Menu size={20}/></button><div className="breadcrumbs"><Link to={workspaceSettings.defaultModule || '/dashboard'}>Workspace</Link><ChevronRight size={14}/><span>{title}</span></div></div><div className="topbar-actions"><label className="global-search"><Search size={16}/><input value={search} onChange={event => setSearch(event.target.value)} placeholder="Search dashboard..." aria-label="Search dashboard"/></label><div className="menu-anchor"><button className={`top-icon-button ${notificationsOpen ? 'selected' : ''}`} aria-label="Notifications" onClick={() => { setNotificationsOpen(!notificationsOpen); setProfileOpen(false); }}><Bell size={18}/>{notifications.length > 0 && <i />}</button>{notificationsOpen && <div className="popover notification-popover"><div className="popover-head"><b>Notifications</b><span>{notifications.length} enabled</span></div>{notifications.length ? notifications.map((item, index) => <div className="notification-item" key={`${item.label}-${index}`}><span className={`notification-dot ${item.tone}`}/><div><b>{item.label}</b><small>{item.detail}</small></div></div>) : <div className="notification-item"><span className="notification-dot muted-pip"/><div><b>All notifications are off</b><small>Update your preferences in Settings.</small></div></div>}<Link to="/dashboard/settings" onClick={() => setNotificationsOpen(false)} className="popover-link">Notification settings <ChevronRight size={14}/></Link></div>}</div><div className="menu-anchor"><button className="user-menu" onClick={() => { setProfileOpen(!profileOpen); setNotificationsOpen(false); }} aria-expanded={profileOpen}><span className="avatar">{accountInitials}</span><span className="user-copy"><b>{accountName}</b><small>{accountEmail ? 'Signed in' : 'Not signed in'}</small></span><ChevronDown size={14}/></button>{profileOpen && <div className="popover profile-popover"><div className="profile-summary"><span className="avatar">{accountInitials}</span><span><b>{accountName}</b><small>{accountEmail ?? 'Sign in to manage API data'}</small></span></div>{accountEmail ? <Link to="/dashboard/data" onClick={() => setProfileOpen(false)}>Profile and API data</Link> : <Link to="/login" onClick={() => setProfileOpen(false)}>Sign in</Link>}<Link to="/" onClick={() => setProfileOpen(false)}>Back to landing page</Link></div>}</div></div></header>
      <div className="dashboard-page-content" onClick={dismissMenus}><Outlet context={{ search }}/></div>
    </div>
  </div>;
}
