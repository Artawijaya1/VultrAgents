import { useEffect, useMemo, useState } from 'react';
import { Link, useOutletContext } from 'react-router-dom';
import { ArrowRight, CircleDollarSign, ClipboardList, FileText, RefreshCw, ShieldCheck, Users } from 'lucide-react';
import { useProcurementStore } from '../../services/procurementStore';
import { getContracts, getInvoices, getPurchaseOrders, getSuppliers } from '../../services/procurementService';

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
      <div className="proc-table-card"><div className="proc-table-scroll"><table><thead><tr><th>PO</th><th>SUPPLIER</th><th>PRODUCT</th><th>QUANTITY</th><th>UNIT OFFER</th><th>STATUS</th></tr></thead><tbody>{filteredOrders.slice(0, 8).map(order => <tr key={order.id}><td>{order.id}</td><td>{order.supplierName || order.supplierId}</td><td>{order.productName}</td><td>{order.quantity}</td><td>{currency(order.currentOffer, order.currency)}</td><td>{order.status}</td></tr>)}{!filteredOrders.length && <tr><td colSpan="6" className="proc-empty">{loading ? 'Loading database records…' : error ? 'Records are unavailable while Backend is unreachable.' : 'No purchase orders are assigned to this account yet.'}</td></tr>}</tbody></table></div></div>
    </section>
    <section className="dashboard-section"><div className="dashboard-section-heading"><div><h2>Administration</h2><p>Review recorded changes and workspace preferences.</p></div></div><div className="dashboard-panel"><ShieldCheck size={18} /><span>Audit entries are retrieved from Backend database activity.</span><Link to="/dashboard/audit-logs">Open audit logs <ArrowRight size={14} /></Link></div></section>
  </div>;
}
