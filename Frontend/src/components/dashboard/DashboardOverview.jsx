import { useEffect, useMemo, useState } from 'react';
import { Link, useOutletContext } from 'react-router-dom';
import { ArrowRight, CircleDollarSign, ClipboardList, FileText, RefreshCw, ShieldCheck, Users, Handshake, AlertTriangle, Database } from 'lucide-react';
import { useProcurementStore } from '../../services/procurementStore';
import { getContracts, getInvoices, getPurchaseOrders, getSuppliers } from '../../services/procurementService';
import { RecordIdentity } from '../../utils/recordPresentation';
import '../../styles/procurement-typography.css';

const currency = (value, code = 'IDR') => new Intl.NumberFormat('en-US', { style: 'currency', currency: code || 'IDR', maximumFractionDigits: 0 }).format(value);

export default function DashboardOverview() {
  const { search = '' } = useOutletContext() ?? {};
  const orders = useProcurementStore(state => state.purchaseOrders);
  const suppliers = useProcurementStore(state => state.suppliers);
  const invoices = useProcurementStore(state => state.invoices);
  const setRecords = useProcurementStore(state => state.setRecords);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = () => {
    setLoading(true);
    setError('');
    setRecords({ purchaseOrders: [], suppliers: [], invoices: [], contracts: [] });
    Promise.all([getPurchaseOrders(), getSuppliers(), getInvoices(), getContracts()])
      .then(([purchaseOrders, suppliers, invoices, contracts]) => setRecords({ purchaseOrders, suppliers, invoices, contracts }))
      .catch(err => setError(err?.message || 'Could not load database records.'))
      .finally(() => setLoading(false));
  };
  useEffect(() => { load(); }, []);

  const filteredOrders = useMemo(() => orders.filter(order => `${order.id} ${order.supplierName} ${order.productName} ${order.status}`.toLowerCase().includes(search.toLowerCase())), [orders, search]);
  const amount = orders.reduce((sum, order) => sum + order.currentOffer * order.quantity, 0);
  const openCount = orders.filter(order => String(order.status).toLowerCase() === 'open').length;
  const otherCount = orders.length - openCount;
  const metrics = [
    { label: 'Purchase order value', value: currency(amount, orders[0]?.currency), detail: `${orders.length} database purchase orders`, icon: CircleDollarSign },
    { label: 'Purchase orders', value: String(orders.length), detail: 'Records assigned to your account', icon: ClipboardList },
    { label: 'Suppliers', value: String(suppliers.length), detail: 'Suppliers linked to your orders', icon: Users },
    { label: 'Invoices', value: String(invoices.length), detail: 'Invoice rows stored in the database', icon: FileText },
  ];

  return <div className="dashboard-overview">
    <div className="overview-heading"><div><div className="dashboard-eyebrow"><span className="live-dot" /> DATABASE CONNECTED</div><h1>Procurement Overview</h1><p>Current procurement records from your Backend database.</p></div><div className="overview-controls"><button className="dashboard-control export-button" onClick={load}><RefreshCw size={15} /> Refresh records</button></div></div>
    {error && <div className="fraud-page-error" role="alert"><span>{error}</span><button onClick={load}>Retry</button></div>}
    <section className="kpi-grid-dashboard" aria-label="Database procurement metrics">{metrics.map(({ label, value, detail, icon: Icon }) => <article className="dashboard-kpi" key={label}><div className="kpi-top"><span>{label}</span><span className="kpi-icon"><Icon size={18} /></span></div><div className="kpi-number">{loading ? '—' : value}</div><div className="kpi-support">{detail}</div></article>)}</section>
    <section className="dashboard-section"><div className="dashboard-section-heading"><div><h2>Purchase orders</h2><p>Most recently updated database records</p></div><Link to="/dashboard/purchase-orders">View all <ArrowRight size={14} /></Link></div>
      <div className="proc-table-card"><div className="proc-table-scroll"><table className="proc-table"><thead><tr><th>PO</th><th>SUPPLIER</th><th>PRODUCT</th><th>QUANTITY</th><th>UNIT OFFER</th><th>STATUS</th></tr></thead><tbody>{filteredOrders.slice(0, 8).map(order => <tr key={order.id}><td className="proc-id-cell"><RecordIdentity value={order.id} kind="purchase-order" /></td><td className="proc-supplier-name">{order.supplierName || order.supplierId}</td><td className="proc-product-cell"><RecordIdentity value={order.productName} kind="product" compact /></td><td>{order.quantity}</td><td>{currency(order.currentOffer, order.currency)}</td><td><span className="proc-pill proc-pill-positive">{order.status}</span></td></tr>)}{!filteredOrders.length && <tr><td colSpan="6" className="proc-empty">{loading ? 'Loading database records…' : error ? 'Records are unavailable while Backend is unreachable.' : 'No purchase orders are assigned to this account yet.'}</td></tr>}</tbody></table></div></div>
    </section>
    <section className="overview-bottom-grid" aria-label="Procurement next steps">
      <article className="overview-secondary-panel">
        <div className="overview-panel-title"><span className="overview-panel-icon"><ShieldCheck size={23} /></span><div><h2>Governance &amp; Next Actions</h2><p>Continue your procurement workflow with connected services.</p></div></div>
        <div className="overview-action-list">
          <Link to="/negotiation"><span className="overview-action-icon"><Handshake size={20}/></span><span><b>Review negotiation opportunities</b><small>Compare supplier pricing and budget constraints.</small></span><ArrowRight size={20}/></Link>
          <Link to="/fraud-detection"><span className="overview-action-icon"><AlertTriangle size={20}/></span><span><b>Investigate procurement risks</b><small>View anomalies recorded by the Backend.</small></span><ArrowRight size={20}/></Link>
          <Link to="/dashboard/audit-logs"><span className="overview-action-icon"><ShieldCheck size={20}/></span><span><b>Review activity and approvals</b><small>Inspect the database-backed audit trail.</small></span><ArrowRight size={20}/></Link>
        </div>
      </article>
      <article className="overview-secondary-panel">
        <div className="overview-panel-title"><span className="overview-panel-icon"><Database size={23} /></span><div><h2>Procurement Status</h2><p>Live status of purchase orders assigned to your account.</p></div></div>
        <div className="overview-status-total"><strong>{loading ? '—' : orders.length}</strong><span>Total Purchase Orders</span></div>
        <div className="overview-status-track" role="img" aria-label={`${openCount} open purchase orders out of ${orders.length}`}><span style={{ width: `${orders.length ? (openCount / orders.length) * 100 : 0}%` }}/></div>
        <div className="overview-status-row"><span><i className="positive"/>Open</span><strong>{loading ? '—' : openCount}</strong></div>
        <div className="overview-status-row"><span><i/>Other statuses</span><strong>{loading ? '—' : otherCount}</strong></div>
        <Link className="overview-status-link" to="/dashboard/purchase-orders">Explore all orders <ArrowRight size={17}/></Link>
      </article>
    </section>
  </div>;
}
