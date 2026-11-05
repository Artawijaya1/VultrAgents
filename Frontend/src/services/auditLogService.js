import { getAuditLogs } from './api';

let auditEvents = [];
const CHANGE_EVENT = 'procuremind:audit-logs-updated';

export async function refreshAuditEvents() {
  auditEvents = [];
  const response = await getAuditLogs();
  auditEvents = Array.isArray(response) ? response : response?.items ?? [];
  window.dispatchEvent(new CustomEvent(CHANGE_EVENT));
  return auditEvents;
}

export function getAuditEvents() {
  return auditEvents;
}

// Audit records are written by Backend alongside the database mutation.
export function recordAuditEvent() {
  return null;
}

export function subscribeToAuditEvents(callback) {
  window.addEventListener(CHANGE_EVENT, callback);
  return () => window.removeEventListener(CHANGE_EVENT, callback);
}
