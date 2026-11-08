import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Activity, ArrowRight, BellRing, RefreshCw, ShieldAlert, ShieldCheck, MessageSquare } from 'lucide-react';
import RiskOverviewCards from '../components/fraud/RiskOverviewCards';
import RiskAnalytics from '../components/fraud/RiskAnalytics';
import SuspiciousAlertsTable from '../components/fraud/SuspiciousAlertsTable';
import InvestigationDrawer from '../components/fraud/InvestigationDrawer';
import { getAnomalyDistribution, getFraudAlerts, getInvestigationDetails, getRiskOverview, getRiskTrend, updateInvestigationStatus, statusForFraudAction } from '../services/fraudDetectionService';
import { useProcurementStore } from '../services/procurementStore';
import './fraud-detection.css';

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

  const loadData = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const [alertRows, overviewData, trendData, distributionData] = await Promise.all([
        getFraudAlerts(), getRiskOverview(), getRiskTrend(), getAnomalyDistribution(),
      ]);
      setAlerts(alertRows); setOverview(overviewData); setTrend(trendData); setDistribution(distributionData);
    } catch (err) {
      if (err && typeof err === 'object' && err.status === 501) setError('Live fraud monitoring is not available yet (backend returns 501).');
      else if (err && typeof err === 'object' && (err.status === 502 || err.status === 504)) setError('Temporary server error. Please retry.');
      else setError('Could not load fraud records. Try again.');
    } finally { setLoading(false); }
  }, []);
  useEffect(() => { void loadData(); }, [loadData]);
  const selectedAlert = alerts.find(alert => alert.id === selectedId) ?? selectedDetail;
  useEffect(() => {
    if (!selectedInvoiceId || !alerts.length) return;
    const linked = alerts.find(alert => alert.invoiceId === selectedInvoiceId);
    if (linked) { setSelectedId(linked.id); setSelectedDetail(linked); }
  }, [selectedInvoiceId, alerts]);
  const clearToast = () => window.setTimeout(() => setToast(''), 3200);
  const selectAlert = async alert => {
    selectInvoice(alert.invoiceId === '—' ? null : alert.invoiceId);
    setSelectedId(alert.id); setSelectedDetail(alert); setDetailLoading(true);
    try {
      const details = await getInvestigationDetails(alert.id);
      if (details) setSelectedDetail({ ...details, status: alert.status, auditTrail: alert.auditTrail });
    } catch { setToast('Could not load alert details from Backend.'); clearToast(); }
    finally { setDetailLoading(false); }
  };
  const applyAction = async (action, notes) => {
    if (!selectedAlert) throw new Error('No alert is selected');
    const updated = await updateInvestigationStatus(selectedAlert.id, statusForFraudAction(action), notes);
    if (!updated) throw new Error('Alert is no longer available');
    setAlerts(current => current.map(alert => alert.id === selectedAlert.id ? updated : alert));
    setSelectedDetail(updated); setToast(`${action} · saved to Backend`); clearToast();
  };
  const closeDrawer = useCallback(() => {
    setSelectedId(null); setSelectedDetail(null); setDetailLoading(false); selectInvoice(null);
  }, [selectInvoice]);

  return <main className="fraud-detection-page">
    <header className="fraud-page-header">
      <div><div className="fraud-breadcrumb"><Link to="/dashboard">Dashboard</Link><ArrowRight size={15}/><span>Fraud Detection</span></div>
        <div className="fraud-title-row"><span className="fraud-page-icon"><ShieldAlert size={25}/></span><div><h1>Procurement Fraud Detection</h1><p>Monitor procurement anomalies, investigate review signals, and strengthen financial controls.</p></div></div>
      </div>
      <div className="fraud-header-actions"><span className="monitor-active"><i/><Activity size={16}/> Fraud monitoring</span><button className="dashboard-control" onClick={() => void loadData()} disabled={loading}><RefreshCw size={17}/> Refresh data</button></div>
    </header>
    <div className="fraud-demo-banner"><span className="fraud-demo-badge">DATABASE RECORDS</span><span>Risk alerts shown here are loaded from the authenticated Backend.</span><span className="banner-separator">·</span><span className="human-controlled-label"><ShieldCheck size={15}/> Human review required</span></div>
    {error && <div className="fraud-page-error" role="alert"><span>{error}</span><button onClick={() => void loadData()}><RefreshCw size={15}/> Retry</button></div>}
    {overview && <RiskOverviewCards overview={overview} suspiciousCount={overview.suspiciousTransactions ?? 0} exposure={overview.potentialExposure ?? 0} />}
    <RiskAnalytics trend={trend} distribution={distribution}/>
    {!loading && !error && alerts.length === 0 && <section className="fraud-empty-guidance">
      <span className="fraud-empty-guidance-icon"><ShieldCheck size={26}/></span>
      <div><h2>No persisted risk alerts yet</h2><p>The investigation dashboard currently has no saved alerts. Live Agent fraud prechecks can still identify review indicators for a purchase order without automatically recording them as dashboard alerts. Review the underlying evidence before making a decision.</p></div>
      <Link to="/dashboard/chat"><MessageSquare size={19}/> Analyze a purchase order <ArrowRight size={17}/></Link>
    </section>}
    <SuspiciousAlertsTable alerts={alerts} loading={loading} onSelect={selectAlert}/>
    {loading && <div className="fraud-summary-loading"><span className="fraud-loading-spinner"/> Loading overview metrics…</div>}
    <div className="fraud-human-note"><ShieldCheck size={17}/> Risk indicators support procurement officers and auditors. They do not determine fraud or perform payment and supplier actions.</div>
    {selectedId && detailLoading && <div className="investigation-opening"><span className="fraud-loading-spinner"/> Loading investigation record…</div>}
    {selectedAlert && <InvestigationDrawer alert={selectedAlert} onClose={closeDrawer} onAction={applyAction} toast={toast}/>}
    {toast && <div className="fraud-page-toast" role="status"><ShieldCheck size={17}/>{toast}</div>}
  </main>;
}
