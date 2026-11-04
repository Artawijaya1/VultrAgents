import { Fragment, useCallback, useEffect, useState } from 'react';
import { LogOut, RefreshCw, Save, Trash2, UserRound, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { ApiError, deleteItem, getCurrentUser, getItems, getUser, getUsers, logout, updateCurrentUser, updateItem, updateUser, createItem, } from '../services/api';
import './data-management.css';
function messageFor(error) {
    if (error instanceof ApiError && error.status === 503) {
        return 'The backend database or Supabase service is not ready. Check the backend configuration.';
    }
    return error instanceof Error ? error.message : 'The request could not be completed.';
}
export default function DataManagementPage() {
    const [tab, setTab] = useState('items');
    const [profile, setProfile] = useState(null);
    const [items, setItems] = useState([]);
    const [users, setUsers] = useState([]);
    const [userDetails, setUserDetails] = useState({});
    const [dataLoading, setDataLoading] = useState(true);
    const [itemsLoadError, setItemsLoadError] = useState('');
    const [usersLoading, setUsersLoading] = useState(false);
    const [usersLoaded, setUsersLoaded] = useState(false);
    const [usersLoadError, setUsersLoadError] = useState('');
    const [itemDraft, setItemDraft] = useState({ title: '', description: '' });
    const [editingItemId, setEditingItemId] = useState(null);
    const [savingItem, setSavingItem] = useState(false);
    const [savingProfile, setSavingProfile] = useState(false);
    const [savingUserId, setSavingUserId] = useState(null);
    const [profileName, setProfileName] = useState('');
    const [userNames, setUserNames] = useState({});
    const [error, setError] = useState('');
    const [notice, setNotice] = useState('');
    const navigate = useNavigate();
    const loadData = useCallback(async () => {
        setDataLoading(true);
        setError('');
        const [profileResult, itemsResult] = await Promise.allSettled([getCurrentUser(), getItems()]);
        if (profileResult.status === 'fulfilled') {
            setProfile(profileResult.value);
            setProfileName(profileResult.value.full_name ?? '');
        }
        else {
            setError(messageFor(profileResult.reason));
        }
        if (itemsResult.status === 'fulfilled') {
            setItems(itemsResult.value);
            setItemsLoadError('');
        }
        else {
            const message = messageFor(itemsResult.reason);
            setItemsLoadError(message);
            setError(current => [current, message].filter(Boolean).join(' '));
        }
        setDataLoading(false);
    }, []);
    const loadUsers = useCallback(async () => {
        setUsersLoading(true);
        setUsersLoadError('');
        setError('');
        try {
            const result = await getUsers();
            setUsers(result);
            setUserNames(Object.fromEntries(result.map(user => [user.id, user.full_name ?? ''])));
            setUsersLoaded(true);
        }
        catch (reason) {
            setError(reason instanceof ApiError && reason.status === 403
                ? 'User administration is restricted to admin accounts.'
                : messageFor(reason));
            setUsersLoadError(reason instanceof ApiError && reason.status === 403
                ? 'Only admin accounts can view users.'
                : messageFor(reason));
        }
        finally {
            setUsersLoaded(true);
            setUsersLoading(false);
        }
    }, []);
    useEffect(() => {
        void loadData();
    }, [loadData]);
    useEffect(() => {
        if (tab === 'users' && !usersLoaded && !usersLoading)
            void loadUsers();
    }, [tab, usersLoaded, usersLoading, loadUsers]);
    async function submitItem(event) {
        event.preventDefault();
        setError('');
        setNotice('');
        setSavingItem(true);
        try {
            const values = {
                title: itemDraft.title.trim(),
                description: itemDraft.description.trim() || null,
            };
            if (editingItemId === null) {
                await createItem(values);
                setNotice('Item created.');
            }
            else {
                await updateItem(editingItemId, values);
                setNotice('Item updated.');
            }
            setItemDraft({ title: '', description: '' });
            setEditingItemId(null);
            setItems(await getItems());
        }
        catch (reason) {
            setError(messageFor(reason));
        }
        finally {
            setSavingItem(false);
        }
    }
    async function removeItem(item) {
        if (!window.confirm(`Delete "${item.title}"? This cannot be undone.`))
            return;
        setError('');
        setNotice('');
        try {
            await deleteItem(item.id);
            setItems(current => current.filter(entry => entry.id !== item.id));
            setNotice('Item deleted.');
            if (editingItemId === item.id)
                cancelItemEdit();
        }
        catch (reason) {
            setError(messageFor(reason));
        }
    }
    function startItemEdit(item) {
        setEditingItemId(item.id);
        setItemDraft({ title: item.title, description: item.description ?? '' });
        setError('');
        setNotice('');
    }
    function cancelItemEdit() {
        setEditingItemId(null);
        setItemDraft({ title: '', description: '' });
    }
    async function submitProfile(event) {
        event.preventDefault();
        setSavingProfile(true);
        setError('');
        setNotice('');
        try {
            const updated = await updateCurrentUser({ full_name: profileName.trim() || null });
            setProfile(updated);
            setProfileName(updated.full_name ?? '');
            setNotice('Profile updated.');
        }
        catch (reason) {
            setError(messageFor(reason));
        }
        finally {
            setSavingProfile(false);
        }
    }
    async function saveUser(user) {
        setSavingUserId(user.id);
        setError('');
        setNotice('');
        try {
            const updated = await updateUser(user.id, { full_name: userNames[user.id]?.trim() || null });
            setUsers(current => current.map(entry => entry.id === updated.id ? updated : entry));
            setUserNames(current => ({ ...current, [updated.id]: updated.full_name ?? '' }));
            setNotice(`Updated ${updated.email}.`);
        }
        catch (reason) {
            setError(messageFor(reason));
        }
        finally {
            setSavingUserId(null);
        }
    }
    async function toggleUser(user) {
        setSavingUserId(user.id);
        setError('');
        setNotice('');
        try {
            const updated = await updateUser(user.id, { is_active: !user.is_active });
            setUsers(current => current.map(entry => entry.id === updated.id ? updated : entry));
            setNotice(`${updated.email} ${updated.is_active ? 'activated' : 'deactivated'}.`);
        }
        catch (reason) {
            setError(messageFor(reason));
        }
        finally {
            setSavingUserId(null);
        }
    }
    async function toggleUserDetails(id) {
        if (userDetails[id]) {
            setUserDetails(current => {
                const next = { ...current };
                delete next[id];
                return next;
            });
            return;
        }
        setError('');
        try {
            const details = await getUser(id);
            setUserDetails(current => ({ ...current, [id]: details }));
        }
        catch (reason) {
            setError(messageFor(reason));
        }
    }
    async function signOut() {
        setError('');
        try {
            await logout();
        }
        catch (reason) {
            setError(`Signed out locally, but the backend logout request failed: ${messageFor(reason)}`);
        }
        navigate('/login', { replace: true });
    }
    return (<main className="data-management-page">
      <div className="data-page-heading">
        <div>
          <div className="dashboard-eyebrow"><span className="live-dot"/> AUTHENTICATED API V1</div>
          <h1>Data management</h1>
          <p>Manage your profile and owner-scoped items through the FastAPI v1 endpoints.</p>
        </div>
        <button className="dashboard-control" onClick={() => void signOut()}><LogOut size={15}/> Sign out</button>
      </div>

      <section className="profile-card">
        <div className="data-section-title"><span className="data-icon"><UserRound size={17}/></span><div><h2>Your profile</h2><p>{profile?.email ?? 'Loading account details…'}</p></div></div>
        <form className="profile-form" onSubmit={event => void submitProfile(event)}>
          <label htmlFor="profile-name">Full name</label>
          <input id="profile-name" value={profileName} onChange={event => setProfileName(event.target.value)} maxLength={200}/>
          <button type="submit" className="small-primary" disabled={savingProfile || !profile}><Save size={14}/>{savingProfile ? 'Saving…' : 'Save profile'}</button>
        </form>
      </section>

      {error && <div className="data-alert error" role="alert">{error}</div>}
      {notice && <div className="data-alert success" role="status">{notice}</div>}

      <div className="data-tabs" role="tablist" aria-label="API data">
        <button role="tab" aria-selected={tab === 'items'} className={tab === 'items' ? 'selected' : ''} onClick={() => { setTab('items'); setError(''); setNotice(''); }}>My items</button>
        <button role="tab" aria-selected={tab === 'users'} className={tab === 'users' ? 'selected' : ''} onClick={() => { setTab('users'); setError(''); setNotice(''); }}>User administration</button>
      </div>

      {tab === 'items' && <section className="data-panel">
        <div className="data-panel-heading">
          <div><h2>Items</h2><p>Only items owned by your account are returned by the API.</p></div>
          <button className="dashboard-control" onClick={() => void loadData()} disabled={dataLoading}><RefreshCw size={14} className={dataLoading ? 'api-spinning' : ''}/> Refresh</button>
        </div>
        <form className="crud-form" onSubmit={event => void submitItem(event)}>
          <h3>{editingItemId === null ? 'Create item' : `Edit item #${editingItemId}`}</h3>
          <div className="crud-fields">
            <label>Title<input required minLength={1} maxLength={200} value={itemDraft.title} onChange={event => setItemDraft(current => ({ ...current, title: event.target.value }))}/></label>
            <label>Description<textarea rows={2} value={itemDraft.description} onChange={event => setItemDraft(current => ({ ...current, description: event.target.value }))}/></label>
          </div>
          <div className="form-actions"><button type="submit" className="small-primary" disabled={savingItem}><Save size={14}/>{savingItem ? 'Saving…' : editingItemId === null ? 'Create item' : 'Save changes'}</button>{editingItemId !== null && <button type="button" className="small-secondary" onClick={cancelItemEdit}><X size={14}/>Cancel</button>}</div>
        </form>
        <div className="item-list">
          {dataLoading ? <p className="data-empty">Loading items…</p> : itemsLoadError ? <p className="data-empty">Items could not be loaded. Check the error above and retry.</p> : items.length === 0 ? <p className="data-empty">No items yet. Create one above to get started.</p> : items.map(item => <article className="item-row" key={item.id}>
            <div className="item-copy"><h3>{item.title}</h3><p>{item.description || 'No description'}</p><small>Created {new Date(item.created_at).toLocaleString()}</small></div>
            <div className="row-actions"><button className="small-secondary" onClick={() => startItemEdit(item)}>Edit</button><button className="icon-danger" aria-label={`Delete ${item.title}`} onClick={() => void removeItem(item)}><Trash2 size={15}/></button></div>
          </article>)}
        </div>
      </section>}

      {tab === 'users' && <section className="data-panel">
        <div className="data-panel-heading"><div><h2>User administration</h2><p>Admin-only list and update operations. New accounts are provisioned in Supabase.</p></div><button className="dashboard-control" onClick={() => void loadUsers()} disabled={usersLoading}><RefreshCw size={14} className={usersLoading ? 'api-spinning' : ''}/> Refresh</button></div>
        {usersLoading ? <p className="data-empty">Loading users…</p> : usersLoadError ? <p className="data-empty">{usersLoadError}</p> : users.length === 0 ? <p className="data-empty">{usersLoaded ? 'No users are available to display.' : 'Open this tab to load users.'}</p> : <div className="users-table-wrap"><table className="users-table"><thead><tr><th>Email</th><th>Full name</th><th>Status</th><th>Actions</th></tr></thead><tbody>{users.map(user => <Fragment key={user.id}><tr>
          <td>{user.email}</td>
          <td><input className="user-name-input" aria-label={`Full name for ${user.email}`} value={userNames[user.id] ?? ''} maxLength={200} onChange={event => setUserNames(current => ({ ...current, [user.id]: event.target.value }))}/></td>
          <td><span className={`user-status ${user.is_active ? 'active' : 'inactive'}`}>{user.is_active ? 'Active' : 'Inactive'}</span></td>
          <td><div className="row-actions"><button className="small-secondary" onClick={() => void toggleUserDetails(user.id)}>{userDetails[user.id] ? 'Hide details' : 'Details'}</button><button className="small-secondary" onClick={() => void saveUser(user)} disabled={savingUserId === user.id}><Save size={13}/>Save</button><button className="small-secondary" onClick={() => void toggleUser(user)} disabled={savingUserId === user.id}>{user.is_active ? 'Deactivate' : 'Activate'}</button></div></td>
        </tr>{userDetails[user.id] && <tr><td colSpan={4} className="user-details">Account ID: {userDetails[user.id].id} · Created {new Date(userDetails[user.id].created_at).toLocaleString()}</td></tr>}</Fragment>)}</tbody></table></div>}
        <p className="data-footnote">The API does not expose user creation or deletion. Manage account provisioning in Supabase Auth.</p>
      </section>}
    </main>);
}
