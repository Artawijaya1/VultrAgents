import { getAuthSession } from './api';

const STORAGE_KEY = 'procuremind-audit-logs-v1';
const LEGACY_PROCUREMENT_KEY = 'procuremind-demo-procurement-v1';
const LEGACY_FRAUD_KEY = 'procuremind-demo-fraud-alerts-v1';
const CHANGE_EVENT = 'procuremind:audit-logs-updated';

const DEMO_EVENTS = [
  { id: 'AUD-DEMO-01', timestamp: '2026-11-04T09:42:00+08:00', category: 'Fraud', action: 'Potential duplicate invoice flagged', entityType: 'Fraud alert', entityId: 'ALT-2026-0428', actor: 'ProcureMind Monitor', outcome: 'Review required', summary: 'Invoice references matched an earlier local demonstration record.', demo: true },
  { id: 'AUD-DEMO-02', timestamp: '2026-11-04T08:18:00+08:00', category: 'Fraud', action: 'Price variance review opened', entityType: 'Fraud alert', entityId: 'ALT-2026-0427', actor: 'ProcureMind Monitor', outcome: 'Under review', summary: 'A price variance exceeded the configured demonstration threshold.', demo: true },
  { id: 'AUD-DEMO-03', timestamp: '2026-11-03T15:24:00+08:00', category: 'Procurement', action: 'Purchase order submitted for approval', entityType: 'Purchase order', entityId: 'PO-2026-00142', actor: 'Jordan Davis', outcome: 'Pending approval', summary: 'A purchase order was submitted to the human review queue.', demo: true },
  { id: 'AUD-DEMO-04', timestamp: '2026-11-03T13:10:00+08:00', category: 'Negotiation', action: 'Negotiation analysis generated', entityType: 'Purchase order', entityId: 'PO-2026-00138', actor: 'Maya Chen', outcome: 'Draft created', summary: 'A pricing recommendation was generated from demonstration purchasing history.', demo: true },
  { id: 'AUD-DEMO-05', timestamp: '2026-11-02T11:05:00+08:00', category: 'Procurement', action: 'Supplier review status updated', entityType: 'Supplier', entityId: 'SUP-0056', actor: 'Jordan Davis', outcome: 'Under review', summary: 'Supplier status changed for demonstration review.', demo: true },
  { id: 'AUD-DEMO-06', timestamp: '2026-11-01T16:35:00+08:00', category: 'Procurement', action: 'Invoice matched to purchase order', entityType: 'Invoice', entityId: 'INV-2026-0694', actor: 'Ava Patel', outcome: 'Matched', summary: 'Invoice and purchase order references were matched in the local demo.', demo: true },
];

function readArray(key) {
  try {
    const value = JSON.parse(window.localStorage.getItem(key) || '[]');
    return Array.isArray(value) ? value : [];
  } catch {
    return [];
  }
}

function readProcurementLegacy() {
  try {
    const value = JSON.parse(window.localStorage.getItem(LEGACY_PROCUREMENT_KEY) || 'null');
    const records = value?.state?.audit;
    return Array.isArray(records) ? records.map(item => ({
      id: item.id,
      timestamp: item.date,
      category: 'Procurement',
      action: item.action,
      entityType: 'Procurement record',
      entityId: item.entityId,
      actor: item.actor || 'Procurement Officer',
      outcome: 'Recorded',
      summary: item.action,
      demo: true,
    })) : [];
  } catch {
    return [];
  }
}

function readFraudLegacy() {
  return readArray(LEGACY_FRAUD_KEY).flatMap(alert => (Array.isArray(alert.auditTrail) ? alert.auditTrail : []).map(item => ({
    id: item.id,
    timestamp: item.timestamp,
    category: 'Fraud',
    action: item.action,
    entityType: 'Fraud alert',
    entityId: alert.id,
    actor: item.actor || 'Procurement Officer',
    outcome: item.newStatus || 'Recorded',
    summary: item.notes || item.action,
    details: { previousStatus: item.previousStatus, newStatus: item.newStatus },
    demo: true,
  })));
}

export function getAuditEvents() {
  const seen = new Set();
  return [...readArray(STORAGE_KEY), ...readProcurementLegacy(), ...readFraudLegacy(), ...DEMO_EVENTS]
    .filter(item => {
      const id = item.id || `${item.timestamp}-${item.action}-${item.entityId}`;
      if (seen.has(id)) return false;
      seen.add(id);
      return true;
    })
    .sort((a, b) => new Date(b.timestamp || b.date || 0) - new Date(a.timestamp || a.date || 0));
}

export function recordAuditEvent({ id, category = 'System', action, entityType = 'Workspace', entityId = 'workspace', outcome = 'Recorded', summary, details = {} }) {
  if (!action) return null;
  const user = getAuthSession()?.user;
  const event = {
    id: id || `AUD-${globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`}`,
    timestamp: new Date().toISOString(),
    category,
    action,
    entityType,
    entityId: String(entityId),
    actor: user?.email || user?.user_metadata?.full_name || 'Local demo user',
    outcome,
    summary: summary || action,
    details,
    demo: false,
  };

  try {
    const events = readArray(STORAGE_KEY);
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify([event, ...events].slice(0, 1500)));
    window.dispatchEvent(new CustomEvent(CHANGE_EVENT));
  } catch {
    // Keep the procurement action working if browser storage is unavailable.
  }
  return event;
}

export function subscribeToAuditEvents(callback) {
  window.addEventListener(CHANGE_EVENT, callback);
  window.addEventListener('storage', callback);
  return () => {
    window.removeEventListener(CHANGE_EVENT, callback);
    window.removeEventListener('storage', callback);
  };
}

export const AUDIT_STORAGE_KEY = STORAGE_KEY;
