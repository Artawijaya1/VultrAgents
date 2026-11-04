const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/+$/, '');
const apiOrigin = apiBaseUrl.replace(/\/api\/v1$/, '');
const SESSION_STORAGE_KEY = 'procuremind-auth-session';
// One-time migration from the old project name key
const _LEGACY_KEY = 'life-purpose-auth-session';
try {
    if (!sessionStorage.getItem(SESSION_STORAGE_KEY) && sessionStorage.getItem(_LEGACY_KEY)) {
        sessionStorage.setItem(SESSION_STORAGE_KEY, sessionStorage.getItem(_LEGACY_KEY));
        sessionStorage.removeItem(_LEGACY_KEY);
    }
} catch { /* storage unavailable — session will be null */ }
export class ApiError extends Error {
    constructor(message, status) {
        super(message);
        this.status = status;
        this.name = 'ApiError';
    }
}
function readSession() {
    try {
        const raw = sessionStorage.getItem(SESSION_STORAGE_KEY);
        if (!raw)
            return null;
        const value = JSON.parse(raw);
        if (typeof value === 'object'
            && value !== null
            && 'access_token' in value
            && 'refresh_token' in value
            && typeof value.access_token === 'string'
            && typeof value.refresh_token === 'string') {
            return value;
        }
    }
    catch {
        sessionStorage.removeItem(SESSION_STORAGE_KEY);
    }
    return null;
}
let session = readSession();
let refreshInFlight = null;
export function getAuthSession() {
    return session;
}
function saveAuthSession(value) {
    session = value;
    if (value) {
        sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(value));
    }
    else {
        sessionStorage.removeItem(SESSION_STORAGE_KEY);
    }
}
async function request(path, init = {}, authenticated = false, timeoutMs = 10000) {
    const firstResponse = await sendRequest(path, init, authenticated ? session?.access_token : undefined, timeoutMs);
    if (firstResponse.status === 401 && authenticated && session?.refresh_token) {
        const refreshed = await refreshAuthSession();
        return parseResponse(await sendRequest(path, init, refreshed.access_token, timeoutMs));
    }
    return parseResponse(firstResponse);
}
async function sendRequest(path, init, accessToken, timeoutMs = 10000) {
    const headers = new Headers(init.headers);
    headers.set('Accept', 'application/json');
    if (init.body && !headers.has('Content-Type')) {
        headers.set('Content-Type', 'application/json');
    }
    if (accessToken)
        headers.set('Authorization', `Bearer ${accessToken}`);
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);
    try {
        return await fetch(`${apiBaseUrl}${path}`, {
            ...init,
            headers,
            signal: controller.signal,
        });
    }
    catch (error) {
        if (controller.signal.aborted) {
            throw new ApiError('Backend request timed out.', 0);
        }
        throw new ApiError('Backend is unreachable. Check that the API server is running.', 0);
    }
    finally {
        window.clearTimeout(timeoutId);
    }
}
async function parseResponse(response) {
    if (response.status === 204)
        return undefined;
    let body;
    try {
        body = await response.json();
    }
    catch {
        body = null;
    }
    if (!response.ok) {
        let message = `Backend returned HTTP ${response.status}.`;
        if (typeof body === 'object' && body !== null && 'detail' in body) {
            const detail = body.detail;
            if (typeof detail === 'string')
                message = detail;
            else if (Array.isArray(detail)) {
                message = detail.map(entry => {
                    if (typeof entry === 'object' && entry !== null && 'msg' in entry) {
                        return String(entry.msg);
                    }
                    return 'Invalid request.';
                }).join(' ');
            }
        }
        throw new ApiError(message, response.status);
    }
    return body;
}
async function refreshAuthSession() {
    if (refreshInFlight)
        return refreshInFlight;
    const current = session;
    if (!current)
        throw new ApiError('Your sign-in session has expired.', 401);
    refreshInFlight = (async () => {
        try {
            const refreshed = await request('/auth/refresh', {
                method: 'POST',
                body: JSON.stringify({ refresh_token: current.refresh_token }),
            });
            saveAuthSession(refreshed);
            return refreshed;
        }
        catch (error) {
            if (error instanceof ApiError && (error.status === 400 || error.status === 401)) {
                saveAuthSession(null);
            }
            throw error;
        }
        finally {
            refreshInFlight = null;
        }
    })();
    return refreshInFlight;
}
async function getStatus(path) {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), 8000);
    let response;
    try {
        response = await fetch(`${apiOrigin}${path}`, {
            headers: { Accept: 'application/json' },
            signal: controller.signal,
        });
    }
    catch {
        if (controller.signal.aborted) {
            throw new ApiError('Backend request timed out.', 0);
        }
        throw new ApiError('Backend is unreachable. Check that the API server is running.', 0);
    }
    finally {
        window.clearTimeout(timeoutId);
    }
    return parseResponse(response);
}
export const getApiHealth = () => getStatus('/health');
export const getApiReadiness = () => getStatus('/ready');
export async function login(email, password) {
    const result = await request('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });
    saveAuthSession(result);
    return result;
}
export async function logout() {
    try {
        await request('/auth/logout', { method: 'POST' }, true);
    }
    finally {
        saveAuthSession(null);
    }
}
export const getCurrentUser = () => request('/auth/me', {}, true);
export const updateCurrentUser = (changes) => request('/auth/me', { method: 'PATCH', body: JSON.stringify(changes) }, true);
export const getUsers = (skip = 0, limit = 100) => request(`/users/?skip=${skip}&limit=${limit}`, {}, true);
export const getUser = (id) => request(`/users/${id}`, {}, true);
export const updateUser = (id, changes) => request(`/users/${id}`, { method: 'PATCH', body: JSON.stringify(changes) }, true);
export const getItems = (skip = 0, limit = 100) => request(`/items/?skip=${skip}&limit=${limit}`, {}, true);
export const createItem = (item) => request('/items/', { method: 'POST', body: JSON.stringify(item) }, true);
export const updateItem = (id, changes) => request(`/items/${id}`, { method: 'PATCH', body: JSON.stringify(changes) }, true);
export const deleteItem = (id) => request(`/items/${id}`, { method: 'DELETE' }, true);
// Live Agent goes through the authenticated Backend proxy, never directly to Agent.
export const chatWithAgent = (task, referenceId, sessionId, question) =>
    request('/agents/chat', { method: 'POST', body: JSON.stringify({
        task, reference_id: referenceId, session_id: sessionId, question
    }) }, true, Number(import.meta.env.VITE_AGENT_REQUEST_TIMEOUT_MS || 185000));
// --- Chat / Conversation helpers ---
export const getConversations = () => request('/conversations', {}, true);
export const createConversation = (task, referenceId) => request('/conversations', { method: 'POST', body: JSON.stringify({ task, reference_id: referenceId }) }, true);
export const getConversationMessages = (conversationId) => request(`/conversations/${conversationId}/messages`, {}, true);
export const sendConversationMessage = (conversationId, question) => request(`/conversations/${conversationId}/messages`, { method: 'POST', body: JSON.stringify({ question }) }, true);
export const sendMessageFeedback = (messageId, rating) => request(`/messages/${messageId}/feedback`, { method: 'POST', body: JSON.stringify({ rating }) }, true);
export const getApprovals = () => request('/approvals', {}, true);
export const approveApproval = (approvalId) => request(`/approvals/${approvalId}/approve`, { method: 'POST', body: JSON.stringify({}) }, true);
export const rejectApproval = (approvalId) => request(`/approvals/${approvalId}/reject`, { method: 'POST', body: JSON.stringify({}) }, true);
// --- Negotiation helpers (all 501 placeholder) ---
export const getNegotiations = () => request('/negotiations', {}, true);
export const createNegotiation = (body) => request('/negotiations', { method: 'POST', body: JSON.stringify(body) }, true);
export const getNegotiation = (id) => request(`/negotiations/${id}`, {}, true);
export const getNegotiationContext = (id) => request(`/negotiations/${id}/context`, {}, true);
export const getNegotiationOptions = (id) => request(`/negotiations/${id}/options`, {}, true);
export const createNegotiationOptions = (id, body) => request(`/negotiations/${id}/options`, { method: 'POST', body: JSON.stringify(body) }, true);
export const getNegotiationDrafts = (id) => request(`/negotiations/${id}/drafts`, {}, true);
export const createNegotiationDraft = (id, body) => request(`/negotiations/${id}/drafts`, { method: 'POST', body: JSON.stringify(body) }, true);
export const getPurchaseHistory = () => request('/purchase-history', {}, true);
export const getPriceHistory = () => request('/price-history', {}, true);
// --- Fraud helpers (all 501 placeholder) ---
export const getFraudAlerts = () => request('/fraud/alerts', {}, true);
export const getFraudAlert = (id) => request(`/fraud/alerts/${id}`, {}, true);
export const updateFraudAlert = (id, body) => request(`/fraud/alerts/${id}`, { method: 'PATCH', body: JSON.stringify(body) }, true);
export const getFraudDashboard = () => request('/fraud/dashboard', {}, true);
export const createFraudScan = (body) => request('/fraud/scans', { method: 'POST', body: JSON.stringify(body) }, true);
export const explainFraudAlert = (id, body) => request(`/fraud/alerts/${id}/explain`, { method: 'POST', body: JSON.stringify(body) }, true);
export const holdFraudulentPayment = (id, body) => request(`/fraud/alerts/${id}/hold-payment`, { method: 'POST', body: JSON.stringify(body) }, true);
export const getFraudRules = () => request('/fraud/rules', {}, true);
// --- Procurement helpers (all 501 placeholder) ---
export const getPurchaseOrders = () => request('/purchase-orders', {}, true);
export const getPurchaseOrder = (id) => request(`/purchase-orders/${id}`, {}, true);
export const getVendors = () => request('/vendors', {}, true);
export const getVendor = (id) => request(`/vendors/${id}`, {}, true);
export const getContracts = () => request('/contracts', {}, true);
export const getContract = (id) => request(`/contracts/${id}`, {}, true);
export const getInvoices = () => request('/invoices', {}, true);
export const getInvoice = (id) => request(`/invoices/${id}`, {}, true);
export const apiRoutes = {
    health: `${apiOrigin}/health`,
    readiness: `${apiOrigin}/ready`,
    users: `${apiBaseUrl}/users/`,
    items: `${apiBaseUrl}/items/`,
    internal: `${apiBaseUrl}/internal/*`,
};
