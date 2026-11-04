import { anomalyDistribution, fraudAlerts, riskOverview, riskTrend } from '../data/fraudMockData';
import {
  ApiError,
  explainFraudAlert as apiExplainAlert,
  getFraudAlert as apiGetAlert,
  getFraudAlerts as apiGetAlerts,
  getFraudDashboard as apiGetDashboard,
  updateFraudAlert as apiUpdateAlert,
} from './api';

const wait = (milliseconds) => new Promise(resolve => window.setTimeout(resolve, milliseconds));

const copyAlert = (alert) => ({
  ...alert,
  explanation: [...(alert.explanation ?? [])],
  evidence: (alert.evidence ?? []).map(item => ({ ...item })),
  riskFactors: (alert.riskFactors ?? []).map(item => ({ ...item })),
  recommendedActions: [...(alert.recommendedActions ?? [])],
  auditTrail: (alert.auditTrail ?? []).map(item => ({ ...item })),
});

let eventSequence = 1;

// ── Mock adapter (local in-memory + demo storage) ───────────────────
const loadAlerts = () => {
  try {
    const stored = localStorage.getItem('procuremind-demo-fraud-alerts-v1');
    return stored ? JSON.parse(stored) : fraudAlerts.map(copyAlert);
  } catch {
    return fraudAlerts.map(copyAlert);
  }
};

let localAlerts = loadAlerts();

const saveAlerts = () => {
  try {
    localStorage.setItem('procuremind-demo-fraud-alerts-v1', JSON.stringify(localAlerts));
  } catch { /* The in-memory demo workflow remains usable when browser storage is unavailable. */ }
};

const mockAdapter = {
  async getFraudAlerts() {
    await wait(180);
    return localAlerts.map(copyAlert);
  },
  async getRiskOverview() {
    await wait(110);
    return { ...riskOverview };
  },
  async getRiskTrend() {
    await wait(90);
    return riskTrend.map(point => ({ ...point }));
  },
  async getAnomalyDistribution() {
    await wait(90);
    return anomalyDistribution.map(point => ({ ...point }));
  },
  async getInvestigationDetails(alertId) {
    await wait(100);
    const alert = localAlerts.find(item => item.id === alertId);
    return alert ? copyAlert(alert) : null;
  },
  async updateInvestigationStatus(alertId, status) {
    await wait(80);
    if (!localAlerts.some(item => item.id === alertId)) return null;
    localAlerts = localAlerts.map(item => item.id === alertId ? { ...item, status } : item);
    saveAlerts();
    return status;
  },
  async appendAuditEvent(alertId, event) {
    await wait(40);
    if (!localAlerts.some(item => item.id === alertId)) return null;
    const created = { ...event, id: `EV-${alertId}-LOCAL-${String(eventSequence++).padStart(3, '0')}` };
    localAlerts = localAlerts.map(item => item.id === alertId ? { ...item, auditTrail: [created, ...item.auditTrail] } : item);
    saveAlerts();
    return created;
  },
  async analyzeTransaction(alert) {
    await wait(220);
    const riskScore = alert.riskFactors.reduce((total, factor) => total + factor.score, 0);
    return {
      riskScore,
      explanation: [...alert.explanation],
      riskFactors: alert.riskFactors.map(factor => ({ ...factor })),
    };
  },
};

// ── Live adapter (Backend endpoints, currently return 501) ───────────
function normalizeAlert(raw) {
  return {
    id: raw.id ?? raw.alert_id ?? 'ALT-UNKNOWN',
    transactionId: raw.transaction_id ?? raw.transactionId ?? '—',
    invoiceId: raw.invoice_id ?? raw.invoiceId ?? '—',
    supplier: raw.supplier_name ?? raw.supplier ?? '—',
    anomalyType: raw.anomaly_type ?? raw.anomalyType ?? 'Suspicious Activity',
    amount: Number(raw.amount ?? 0),
    riskScore: Number(raw.risk_score ?? raw.riskScore ?? 0),
    severity: raw.severity ?? 'Medium',
    detectedAt: raw.detected_at ?? raw.detectedAt ?? new Date().toISOString(),
    status: raw.status ?? 'New',
    explanation: Array.isArray(raw.explanation) ? raw.explanation : (raw.explanation ? [String(raw.explanation)] : []),
    evidence: Array.isArray(raw.evidence) ? raw.evidence : [],
    riskFactors: Array.isArray(raw.risk_factors ?? raw.riskFactors) ? (raw.risk_factors ?? raw.riskFactors) : [],
    recommendedActions: Array.isArray(raw.recommended_actions ?? raw.recommendedActions) ? (raw.recommended_actions ?? raw.recommendedActions) : [],
    auditTrail: Array.isArray(raw.audit_trail ?? raw.auditTrail) ? (raw.audit_trail ?? raw.auditTrail) : [],
  };
}

const liveAdapter = {
  async getFraudAlerts() {
    const raw = await apiGetAlerts();
    const list = Array.isArray(raw) ? raw : (raw.items ?? raw.alerts ?? []);
    return list.map(normalizeAlert);
  },
  async getRiskOverview() {
    const raw = await apiGetDashboard();
    return {
      transactionsAnalyzed: Number(raw.transactions_analyzed ?? raw.transactionsAnalyzed ?? 0),
      suspiciousTransactions: Number(raw.suspicious_transactions ?? raw.suspiciousTransactions ?? 0),
      highRiskSuppliers: Number(raw.high_risk_suppliers ?? raw.highRiskSuppliers ?? 0),
      potentialExposure: Number(raw.potential_exposure ?? raw.potentialExposure ?? 0),
    };
  },
  async getRiskTrend() {
    try {
      const raw = await apiGetDashboard();
      if (Array.isArray(raw.trend)) return raw.trend;
      return [];
    } catch {
      return [];
    }
  },
  async getAnomalyDistribution() {
    try {
      const raw = await apiGetDashboard();
      if (Array.isArray(raw.distribution)) return raw.distribution;
      return [];
    } catch {
      return [];
    }
  },
  async getInvestigationDetails(alertId) {
    const raw = await apiGetAlert(alertId);
    return raw ? normalizeAlert(raw) : null;
  },
  async updateInvestigationStatus(alertId, status) {
    const res = await apiUpdateAlert(alertId, { status });
    return res?.status ?? status;
  },
  async appendAuditEvent(alertId, event) {
    const res = await apiExplainAlert(alertId, {
      action: event.action,
      notes: event.notes,
      previous_status: event.previousStatus,
      new_status: event.newStatus,
    });
    return {
      id: res.id ?? `EV-${alertId}-${Date.now()}`,
      timestamp: res.timestamp ?? event.timestamp ?? new Date().toISOString(),
      actor: res.actor ?? event.actor ?? 'Procurement Officer',
      action: event.action,
      previousStatus: event.previousStatus,
      newStatus: event.newStatus,
      notes: event.notes,
    };
  },
  async analyzeTransaction(alert) {
    const res = await apiExplainAlert(alert.id, { action: 'analyze' });
    return {
      riskScore: Number(res.risk_score ?? alert.riskScore ?? 0),
      explanation: Array.isArray(res.explanation) ? res.explanation : alert.explanation,
      riskFactors: Array.isArray(res.risk_factors) ? res.risk_factors : alert.riskFactors,
    };
  },
};

// ── Mode selection ──────────────────────────────────────────────────
const fraudMode = import.meta.env.VITE_FRAUD_MODE || 'mock';
export const isFraudMockMode = () => fraudMode === 'mock';

function getAdapter(forceMock = false) {
  if (forceMock || fraudMode === 'mock') return mockAdapter;
  return liveAdapter;
}

// ── Exported API ────────────────────────────────────────────────────
export async function getFraudAlerts(forceMock = false) {
  return getAdapter(forceMock).getFraudAlerts();
}

export async function getRiskOverview(forceMock = false) {
  return getAdapter(forceMock).getRiskOverview();
}

export async function getRiskTrend(forceMock = false) {
  return getAdapter(forceMock).getRiskTrend();
}

export async function getAnomalyDistribution(forceMock = false) {
  return getAdapter(forceMock).getAnomalyDistribution();
}

export async function getInvestigationDetails(alertId, forceMock = false) {
  return getAdapter(forceMock).getInvestigationDetails(alertId);
}

export async function updateInvestigationStatus(alertId, status, forceMock = false) {
  return getAdapter(forceMock).updateInvestigationStatus(alertId, status);
}

export async function appendAuditEvent(alertId, event, forceMock = false) {
  return getAdapter(forceMock).appendAuditEvent(alertId, event);
}

export async function analyzeTransaction(alert, forceMock = false) {
  return getAdapter(forceMock).analyzeTransaction(alert);
}

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

export { ApiError };
