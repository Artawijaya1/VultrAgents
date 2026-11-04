import { anomalyDistribution, fraudAlerts, riskOverview, riskTrend } from '../data/fraudMockData';
const wait = (milliseconds) => new Promise(resolve => window.setTimeout(resolve, milliseconds));
const copyAlert = (alert) => ({ ...alert, explanation: [...alert.explanation], evidence: alert.evidence.map(item => ({ ...item })), riskFactors: alert.riskFactors.map(item => ({ ...item })), recommendedActions: [...alert.recommendedActions], auditTrail: alert.auditTrail.map(item => ({ ...item })) });
let eventSequence = 1;
const loadAlerts = () => { try {
    const stored = localStorage.getItem('procuremind-demo-fraud-alerts-v1');
    return stored ? JSON.parse(stored) : fraudAlerts.map(copyAlert);
}
catch {
    return fraudAlerts.map(copyAlert);
} };
let localAlerts = loadAlerts();
const saveAlerts = () => { try {
    localStorage.setItem('procuremind-demo-fraud-alerts-v1', JSON.stringify(localAlerts));
}
catch { /* The in-memory demo workflow remains usable when browser storage is unavailable. */ } };
const localService = {
    async getFraudAlerts() { await wait(180); return localAlerts.map(copyAlert); },
    async getRiskOverview() { await wait(110); return { ...riskOverview }; },
    async getRiskTrend() { await wait(90); return riskTrend.map(point => ({ ...point })); },
    async getAnomalyDistribution() { await wait(90); return anomalyDistribution.map(point => ({ ...point })); },
    async getInvestigationDetails(alertId) { await wait(100); const alert = localAlerts.find(item => item.id === alertId); return alert ? copyAlert(alert) : null; },
    async updateInvestigationStatus(alertId, status) { await wait(80); if (!localAlerts.some(item => item.id === alertId))
        return null; localAlerts = localAlerts.map(item => item.id === alertId ? { ...item, status } : item); saveAlerts(); return status; },
    async appendAuditEvent(alertId, event) { await wait(40); if (!localAlerts.some(item => item.id === alertId))
        return null; const created = { ...event, id: `EV-${alertId}-LOCAL-${String(eventSequence++).padStart(3, '0')}` }; localAlerts = localAlerts.map(item => item.id === alertId ? { ...item, auditTrail: [created, ...item.auditTrail] } : item); saveAlerts(); return created; },
    async analyzeTransaction(alert) { await wait(220); const riskScore = alert.riskFactors.reduce((total, factor) => total + factor.score, 0); return { riskScore, explanation: [...alert.explanation], riskFactors: alert.riskFactors.map(factor => ({ ...factor })) }; },
};
export const getFraudAlerts = localService.getFraudAlerts;
export const getRiskOverview = localService.getRiskOverview;
export const getRiskTrend = localService.getRiskTrend;
export const getAnomalyDistribution = localService.getAnomalyDistribution;
export const getInvestigationDetails = localService.getInvestigationDetails;
export const updateInvestigationStatus = localService.updateInvestigationStatus;
export const appendAuditEvent = localService.appendAuditEvent;
export const analyzeTransaction = localService.analyzeTransaction;
export function statusForFraudAction(action) {
    switch (action) {
        case 'Mark as Reviewed': return 'Under Review';
        case 'Request Documents': return 'Documents Requested';
        case 'Escalate to Auditor': return 'Escalated';
        case 'Dismiss as False Positive': return 'False Positive';
        case 'Mark as Confirmed Anomaly': return 'Confirmed Anomaly';
    }
}
