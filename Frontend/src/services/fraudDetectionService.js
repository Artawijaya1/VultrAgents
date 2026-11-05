import { explainFraudAlert, getFraudAlert, getFraudAlerts as apiGetAlerts, getFraudDashboard, updateFraudAlert } from './api';

const list = (value, key) => Array.isArray(value) ? value : value?.[key] ?? [];
const colors = ['#20b9f2', '#f0b648', '#f06a79', '#8a79fa'];
function normalizeAlert(raw) {
  const evidence = raw.evidence && !Array.isArray(raw.evidence)
    ? Object.entries(raw.evidence).map(([label, value]) => ({ label, value: typeof value === 'string' ? value : JSON.stringify(value) }))
    : raw.evidence ?? [];
  return {
    id: raw.id ?? raw.alert_id,
    transactionId: raw.po_id ?? raw.transaction_id ?? '—',
    invoiceId: raw.invoice_id ?? raw.invoiceId ?? '—',
    supplier: raw.supplier_name ?? raw.supplier ?? raw.supplier_id ?? '—',
    anomalyType: raw.anomaly_type ?? raw.title ?? 'Procurement risk alert',
    amount: Number(raw.amount ?? 0),
    currency: raw.currency ?? 'IDR',
    riskScore: raw.risk_score == null ? null : Number(raw.risk_score),
    severity: raw.severity ?? 'Unknown',
    detectedAt: raw.created_at ?? raw.detected_at ?? new Date().toISOString(),
    status: raw.status ?? 'Unknown',
    explanation: Array.isArray(raw.explanation) ? raw.explanation : raw.explanation ? [String(raw.explanation)] : [],
    evidence,
    riskFactors: Array.isArray(raw.risk_factors ?? raw.riskFactors) ? (raw.risk_factors ?? raw.riskFactors) : [],
    recommendedActions: Array.isArray(raw.recommended_actions ?? raw.recommendedActions) ? (raw.recommended_actions ?? raw.recommendedActions) : [],
    auditTrail: Array.isArray(raw.audit_trail ?? raw.auditTrail) ? (raw.audit_trail ?? raw.auditTrail) : [],
  };
}

export async function getFraudAlerts() { return list(await apiGetAlerts(), 'alerts').map(normalizeAlert); }
export async function getRiskOverview() {
  const raw = await getFraudDashboard();
  return {
    transactionsAnalyzed: Number(raw.transactionsAnalyzed ?? raw.transactions_analyzed ?? raw.totalScans ?? 0),
    suspiciousTransactions: Number(raw.suspiciousTransactions ?? raw.suspicious_transactions ?? 0),
    highRiskSuppliers: Number(raw.highRiskSuppliers ?? raw.high_risk_suppliers ?? 0),
    potentialExposure: Number(raw.potentialExposure ?? raw.potential_exposure ?? 0),
  };
}
export async function getRiskTrend() {
  const raw = await getFraudDashboard();
  return list(raw.trend, 'items');
}
export async function getAnomalyDistribution() {
  const raw = await getFraudDashboard();
  return list(raw.distribution, 'items').map((item, index) => ({ type: item.type ?? item.name ?? 'Unclassified', count: Number(item.count ?? item.value ?? 0), color: item.color ?? colors[index % colors.length] }));
}
export async function getInvestigationDetails(id) { const value = await getFraudAlert(id); return value ? normalizeAlert(value) : null; }
export async function updateInvestigationStatus(id, status, notes) { const value = await updateFraudAlert(id, { status, notes }); return value ? normalizeAlert(value) : null; }
export async function appendAuditEvent(id, event) { return explainFraudAlert(id, { action: event.action, notes: event.notes, previous_status: event.previousStatus, new_status: event.newStatus }); }
export async function analyzeTransaction(alert) { return { riskScore: alert.riskScore, explanation: alert.explanation, riskFactors: alert.riskFactors }; }

export function statusForFraudAction(action) {
  switch (action) {
    case 'Mark as Reviewed': return 'Under Review';
    case 'Request Documents': return 'Documents Requested';
    case 'Escalate to Auditor': return 'Escalated';
    case 'Dismiss as False Positive': return 'False Positive';
    case 'Mark as Confirmed Anomaly': return 'Confirmed Anomaly';
    default: return 'Under Review';
  }
}
