import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Activity, ArrowRight, BellRing, RefreshCw, ShieldAlert, ShieldCheck } from 'lucide-react';
import RiskOverviewCards from '../components/fraud/RiskOverviewCards';
import RiskAnalytics from '../components/fraud/RiskAnalytics';
import SuspiciousAlertsTable from '../components/fraud/SuspiciousAlertsTable';
import InvestigationDrawer from '../components/fraud/InvestigationDrawer';
import { appendAuditEvent, getAnomalyDistribution, getFraudAlerts, getInvestigationDetails, getRiskOverview, getRiskTrend, updateInvestigationStatus, statusForFraudAction } from '../services/fraudDetectionService';
import { fraudAlerts as seedFraudAlerts } from '../data/fraudMockData';
import { useProcurementStore } from '../services/procurementStore';
import './fraud-detection.css';
const initialFalsePositiveCount = seedFraudAlerts.filter(alert => alert.status === 'False Positive').length;
const initialFalsePositiveExposure = seedFraudAlerts.filter(alert => alert.status === 'False Positive').reduce((sum, alert) => sum + alert.amount, 0);
export default function FraudDetectionPage() {
    const [alerts, setAlerts] = useState([]);
    const [overview, setOverview] = useState(null);
    const [trend, setTrend] = useState([]);
    const [distribution, setDistribution] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [selectedId, setSelectedId] = useState(null);
    const [selectedDetail, setSelectedDetail] = useState(null);
    const [detailLoading, setDetailLoading] = useState(false);
    const [toast, setToast] = useState('');
    const selectedInvoiceId = useProcurementStore(state => state.selectedInvoiceId);
    const selectInvoice = useProcurementStore(state => state.selectInvoice);
    const updateInvoiceStatus = useProcurementStore(state => state.updateInvoiceStatus);
    const suppliers = useProcurementStore(state => state.suppliers);
    const updateSupplierStatus = useProcurementStore(state => state.updateSupplierStatus);
    const loadData = useCallback(async () => {
        setLoading(true);
        setError('');
        try {
            const [alertRows, overviewData, trendData, distributionData] = await Promise.all([getFraudAlerts(), getRiskOverview(), getRiskTrend(), getAnomalyDistribution()]);
            setAlerts(alertRows);
            setOverview(overviewData);
            setTrend(trendData);
            setDistribution(distributionData);
        }
        catch (err) {
            if (err && typeof err === 'object' && err.status === 501) {
                setError('Live fraud monitoring is not available yet (backend returns 501).');
            } else if (err && typeof err === 'object' && (err.status === 502 || err.status === 504)) {
                setError('Temporary server error. Please retry.');
            } else {
                setError('Could not load fraud records. Try again.');
            }
        }
        finally {
            setLoading(false);
        }
    }, []);
    useEffect(() => { void loadData(); }, [loadData]);
    const selectedAlert = alerts.find(alert => alert.id === selectedId) ?? selectedDetail;
    useEffect(() => {
        if (!selectedInvoiceId || !alerts.length)
            return;
        const linked = alerts.find(alert => alert.invoiceId === selectedInvoiceId);
        if (linked) {
            setSelectedId(linked.id);
            setSelectedDetail(linked);
        }
    }, [selectedInvoiceId, alerts]);
    const newlyDismissed = useMemo(() => Math.max(0, alerts.filter(alert => alert.status === 'False Positive').length - initialFalsePositiveCount), [alerts]);
    const dismissedExposure = useMemo(() => Math.max(0, alerts.filter(alert => alert.status === 'False Positive').reduce((sum, alert) => sum + alert.amount, 0) - initialFalsePositiveExposure), [alerts]);
    const clearToast = () => window.setTimeout(() => setToast(''), 3200);
    const selectAlert = async (alert) => {
        selectInvoice(alert.invoiceId === '—' ? null : alert.invoiceId);
        setSelectedId(alert.id);
        setSelectedDetail(alert);
        setDetailLoading(true);
        try {
            const details = await getInvestigationDetails(alert.id);
            if (details)
                setSelectedDetail({ ...details, status: alert.status, auditTrail: alert.auditTrail });
        }
        catch {
            setToast('Showing the cached local alert record.');
            clearToast();
        }
        finally {
            setDetailLoading(false);
        }
    };
    const applyAction = async (action, notes) => {
        if (!selectedAlert)
            throw new Error('No alert is selected');
        const previousStatus = selectedAlert.status;
        const newStatus = statusForFraudAction(action);
        const updated = await updateInvestigationStatus(selectedAlert.id, newStatus);
        if (!updated)
            throw new Error('Alert is no longer available');
        const auditEvent = await appendAuditEvent(selectedAlert.id, { timestamp: new Date().toISOString(), actor: 'Jordan Davis', action, previousStatus, newStatus, notes: notes || undefined });
        if (!auditEvent)
            throw new Error('Could not append local audit event');
        setAlerts(current => current.map(alert => alert.id === selectedAlert.id ? { ...alert, status: newStatus, auditTrail: [auditEvent, ...alert.auditTrail] } : alert));
        if (selectedAlert.invoiceId !== '—')
            updateInvoiceStatus(selectedAlert.invoiceId, newStatus === 'False Positive' ? 'Matched' : newStatus === 'Confirmed Anomaly' ? 'Flagged' : 'Under Review', `Fraud review updated invoice status to ${newStatus} (demo)`);
        if (newStatus === 'Escalated' || newStatus === 'Confirmed Anomaly') {
            const supplier = suppliers.find(item => item.name === selectedAlert.supplier);
            if (supplier)
                updateSupplierStatus(supplier.id, 'Under Review', `Supplier review opened from fraud case ${selectedAlert.id} (demo)`);
        }
        setToast(`${action} · local demo status updated`);
        clearToast();
    };
    const closeDrawer = useCallback(() => { setSelectedId(null); setSelectedDetail(null); setDetailLoading(false); selectInvoice(null); }, [selectInvoice]);
    const suspiciousCount = overview ? Math.max(0, overview.suspiciousTransactions - newlyDismissed) : 0;
    const exposure = overview ? Math.max(0, overview.potentialExposure - dismissedExposure) : 0;
    return _jsxs("main", { className: "fraud-detection-page", children: [_jsxs("header", { className: "fraud-page-header", children: [_jsxs("div", { children: [_jsxs("div", { className: "fraud-breadcrumb", children: [_jsx(Link, { to: "/dashboard", children: "Dashboard" }), _jsx(ArrowRight, { size: 13 }), _jsx("span", { children: "Fraud Detection" })] }), _jsxs("div", { className: "fraud-title-row", children: [_jsx("span", { className: "fraud-page-icon", children: _jsx(ShieldAlert, { size: 21 }) }), _jsxs("div", { children: [_jsx("h1", { children: "Procurement Fraud Detection" }), _jsx("p", { children: "Monitor suspicious procurement activities, investigate anomalies, and strengthen financial controls." })] })] })] }), _jsxs("div", { className: "fraud-header-actions", children: [_jsxs("span", { className: "monitor-active", children: [_jsx("i", {}), _jsx(Activity, { size: 13 }), " AI Monitoring Active"] }), _jsxs("span", { className: "fraud-update-time", children: [_jsx(BellRing, { size: 13 }), " Updated just now"] })] })] }), _jsxs("div", { className: "fraud-demo-banner", children: [_jsx("span", { className: "fraud-demo-badge", children: "DEMO DATA" }), _jsx("span", { children: "Simulated procurement records \u00B7 No real suppliers, transactions, or fraud findings are represented." }), _jsx("span", { className: "banner-separator", children: "\u00B7" }), _jsxs("span", { className: "human-controlled-label", children: [_jsx(ShieldCheck, { size: 13 }), " Human review required"] })] }), error && _jsxs("div", { className: "fraud-page-error", role: "alert", children: [_jsx("span", { children: error }), _jsxs("button", { onClick: () => void loadData(), children: [_jsx(RefreshCw, { size: 13 }), " Retry"] })] }), overview && _jsx(RiskOverviewCards, { overview: overview, suspiciousCount: suspiciousCount, exposure: exposure }), _jsx(RiskAnalytics, { trend: trend, distribution: distribution }), _jsx(SuspiciousAlertsTable, { alerts: alerts, loading: loading, onSelect: selectAlert }), loading && _jsxs("div", { className: "fraud-summary-loading", children: [_jsx("span", { className: "fraud-loading-spinner" }), " Loading overview metrics\u2026"] }), _jsxs("div", { className: "fraud-human-note", children: [_jsx(ShieldCheck, { size: 14 }), " Risk indicators support procurement officers and auditors. They do not determine fraud or perform payment and supplier actions."] }), selectedId && detailLoading && _jsxs("div", { className: "investigation-opening", children: [_jsx("span", { className: "fraud-loading-spinner" }), "Loading investigation record\u2026"] }), selectedAlert && _jsx(InvestigationDrawer, { alert: selectedAlert, onClose: closeDrawer, onAction: applyAction, toast: toast }), toast && _jsxs("div", { className: "fraud-page-toast", role: "status", children: [_jsx(ShieldCheck, { size: 15 }), toast] })] });
}
