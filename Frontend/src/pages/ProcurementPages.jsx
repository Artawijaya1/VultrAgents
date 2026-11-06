import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useOutletContext, useParams } from 'react-router-dom';
import { ArrowRight, ClipboardList, FileText, Search, ShieldCheck, Users, Wallet, Star, RefreshCw, AlertTriangle, Layers } from 'lucide-react';
import { useProcurementStore } from '../services/procurementStore';
import { getContracts, getInvoices, getPurchaseOrders, getSuppliers } from '../services/procurementService';
import './procurement-pages.css';
import '../styles/procurement-typography.css';
import { RecordIdentity } from '../utils/recordPresentation';
import ProcurementRecordDrawer from '../components/procurement/ProcurementRecordDrawer';
import '../styles/ui-readability-fix.css';

const pageCopy = {
  'purchase-orders': { title: 'Purchase Orders', description: 'Explore your purchase orders, compare supplier offers, and track procurement status.' },
  suppliers: { title: 'Suppliers', description: 'Review supplier performance, purchasing relationships, and recorded business information.' },
  invoices: { title: 'Invoices & Contracts', description: 'Examine invoice records, contract availability, and items requiring closer review.' },
};
const money = (value, currency = 'IDR') => Number.isFinite(Number(value)) && value != null
  ? new Intl.NumberFormat('en-US', { style: 'currency', currency: currency || 'IDR', maximumFractionDigits: 0 }).format(Number(value)) : '—';
const date = value => {
  if (!value) return '—';
  const parsed = new Date(`${String(value).slice(0, 10)}T12:00:00`);
  return Number.isNaN(parsed.getTime()) ? '—' : new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(parsed);
};
const text = value => value == null || value === '' ? '—' : String(value);
const label = value => String(value ?? 'Unknown').replaceAll('_', ' ');

function Metric({ icon: Icon, label: title, value, note }) {
  return <article className="proc-stat-card">
    <div className="proc-stat-symbol"><Icon size={23} /></div>
    <div className="proc-stat-copy"><span>{title}</span><strong>{value}</strong><small>{note}</small></div>
  </article>;
}

export default function ProcurementPages({ section: propSection }) {
  const { section: paramSection } = useParams();
  const section = propSection ?? paramSection ?? 'purchase-orders';
  const page = pageCopy[section];
  const navigate = useNavigate();
  const { search: globalSearch = '' } = useOutletContext() ?? {};
  const [query, setQuery] = useState('');
  const [tab, setTab] = useState('Invoices');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState('');
  const orders = useProcurementStore(state => state.purchaseOrders);
  const suppliers = useProcurementStore(state => state.suppliers);
  const invoices = useProcurementStore(state => state.invoices);
  const contracts = useProcurementStore(state => state.contracts);
  const loading = useProcurementStore(state => state.recordsLoading);
  const setRecords = useProcurementStore(state => state.setRecords);
  const setLoading = useProcurementStore(state => state.setRecordsLoading);

  useEffect(() => {
    let active = true;
    setRecords({ purchaseOrders: [], suppliers: [], invoices: [], contracts: [] });
    setError(''); setQuery(''); setStatusFilter('all'); setSelected(null); setLoading(true);
    Promise.all([getPurchaseOrders(), getSuppliers(), getInvoices(), getContracts()])
      .then(([purchaseOrders, supplierRows, invoiceRows, contractRows]) => {
        if (active) setRecords({ purchaseOrders, suppliers: supplierRows, invoices: invoiceRows, contracts: contractRows });
      })
      .catch(err => { if (active) setError(err?.message || 'Unable to load records from the authenticated Backend.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [section, setRecords, setLoading]);

  const dupCounts = useMemo(() => {
    const counts = new Map();
    for (const item of invoices) {
      const key = String(item.invoiceNumber || '').toLowerCase();
      if (key) counts.set(key, (counts.get(key) || 0) + 1);
    }
    return counts;
  }, [invoices]);
  const rows = useMemo(() => {
    if (section === 'purchase-orders') return orders.map(item => ({
      key: item.id, id: item.id, name: item.supplierName || suppliers.find(s => s.id === item.supplierId)?.name || item.supplierId,
      detail: item.productName, quantity: item.quantity, amount: item.currentOffer, total: item.currentOffer * item.quantity,
      status: item.status, record: item, date: item.createdDate, currency: item.currency,
    }));
    if (section === 'suppliers') return suppliers.map(item => ({
      key: item.id, id: item.id, name: item.name, detail: item.category || 'Supplier',
      amount: item.rating, total: orders.filter(o => o.supplierId === item.id).length,
      status: item.status, date: item.bankLastChangedAt, record: item,
    }));
    if (tab === 'Invoices') return invoices.map((item, index) => ({
      key: item.id ?? `${item.invoiceNumber}-${index}`, id: item.invoiceNumber || item.id,
      name: item.supplierName || suppliers.find(s => s.id === item.supplierId)?.name || item.supplierId,
      detail: item.purchaseOrderId, amount: item.amount, date: item.issueDate, currency: item.currency,
      status: (dupCounts.get(String(item.invoiceNumber || '').toLowerCase()) || 0) > 1 ? 'Duplicate number' : item.status || 'Not recorded', record: item,
    }));
    return contracts.map((item, index) => ({
      key: item.contract_id ?? item.id ?? `contract-${index}`, id: item.contract_id ?? item.id,
      name: item.supplier_name ?? item.supplier_id ?? '—', detail: item.title ?? item.name ?? 'Contract',
      amount: item.value ?? null, date: item.end_date ?? '', status: item.status ?? '—', record: item,
    }));
  }, [section, orders, suppliers, invoices, contracts, tab, dupCounts]);
  const statuses = useMemo(() => [...new Set(rows.map(row => label(row.status)))].sort(), [rows]);
  const visible = useMemo(() => {
    const term = `${query} ${globalSearch}`.trim().toLowerCase();
    return rows.filter(row => {
      const matchesText = !term || [row.id, row.name, row.detail, row.status, row.date].map(text).join(' ').toLowerCase().includes(term);
      return matchesText && (statusFilter === 'all' || label(row.status) === statusFilter);
    });
  }, [rows, query, globalSearch, statusFilter]);

  if (!page) return null;
  const openNegotiation = order => {
    useProcurementStore.getState().selectContext(order.supplierId, order.id);
    navigate('/negotiation');
  };
  const totalOrderValue = orders.reduce((sum, order) => sum + order.quantity * order.currentOffer, 0);
  const linkedSupplierIds = new Set(orders.map(order => order.supplierId));
  const duplicateInvoiceCount = invoices.filter(item => (dupCounts.get(String(item.invoiceNumber || '').toLowerCase()) || 0) > 1).length;
  const rated = suppliers.map(s => s.rating).filter(v => Number.isFinite(v));
  const metrics = section === 'purchase-orders' ? [
    { icon: ClipboardList, label: 'Total purchase orders', value: orders.length, note: 'Available for this account' },
    { icon: ShieldCheck, label: 'Open orders', value: orders.filter(o => String(o.status).toLowerCase() === 'open').length, note: 'Currently open purchases' },
    { icon: Wallet, label: 'Total order value', value: money(totalOrderValue, orders[0]?.currency), note: 'Based on recorded quantities and offers' },
    { icon: FileText, label: 'Average unit offer', value: money(orders.length ? orders.reduce((s, o) => s + o.currentOffer, 0) / orders.length : 0, orders[0]?.currency), note: 'Average across available orders' },
  ] : section === 'suppliers' ? [
    { icon: Users, label: 'Total suppliers', value: suppliers.length, note: 'Supplier records available' },
    { icon: ShieldCheck, label: 'Suppliers with orders', value: suppliers.filter(s => linkedSupplierIds.has(s.id)).length, note: 'Linked to current purchase orders' },
    { icon: Star, label: 'Average rating', value: rated.length ? `${(rated.reduce((a, b) => a + b, 0) / rated.length).toFixed(1)} / 5` : '—', note: 'Across suppliers with a rating' },
    { icon: ClipboardList, label: 'Linked purchase orders', value: orders.length, note: 'Available in the current workspace' },
  ] : [
    { icon: FileText, label: 'Total invoices', value: invoices.length, note: 'Records returned by Backend' },
    { icon: Layers, label: 'Contracts available', value: contracts.length, note: 'Contract records accessible' },
    { icon: AlertTriangle, label: 'Repeated invoice numbers', value: duplicateInvoiceCount, note: 'Potential duplicates; human verification required' },
  ];
  const columns = section === 'purchase-orders'
    ? ['PURCHASE ORDER', 'SUPPLIER', 'PRODUCT', 'QUANTITY', 'UNIT OFFER', 'ORDER VALUE', 'STATUS', '']
    : section === 'suppliers'
      ? ['SUPPLIER ID', 'SUPPLIER', 'CATEGORY', 'RATING', 'LINKED POs', 'STATUS', '']
      : tab === 'Invoices'
        ? ['INVOICE NUMBER', 'SUPPLIER', 'PURCHASE ORDER', 'AMOUNT', 'DATE', 'STATUS', '']
        : ['CONTRACT ID', 'SUPPLIER', 'DESCRIPTION', 'VALUE', 'END DATE', 'STATUS', ''];

  return <main className="procurement-page">
    <header className="proc-page-header">
      <div><div className="dashboard-eyebrow"><span className="live-dot" /> DATABASE RECORDS</div><h1>{page.title}</h1><p>{page.description}</p></div>
      <div className="proc-header-actions">{section === 'purchase-orders' && <Link className="proc-primary-button" to="/negotiation">Open Negotiation Copilot <ArrowRight size={18} /></Link>}</div>
    </header>
    <div className="proc-demo-banner"><span className="demo-info">i</span><b>Authenticated Backend</b><span>{error || 'All figures and records are derived from the connected API.'}</span><ShieldCheck size={18} /><strong>Database-backed</strong></div>
    {error && <div className="fraud-page-error" role="alert"><span>{error}</span><button onClick={() => window.location.reload()}>Retry</button></div>}
    <section className="proc-stat-grid" aria-label="Procurement record summary">
      {metrics.map(metric => <Metric key={metric.label} {...metric} value={loading ? '—' : metric.value} />)}
    </section>
    <section className="proc-table-card">
      <div className="proc-table-heading">
        <div><h2>{section === 'invoices' ? `${tab} Register` : `${page.title} Register`}</h2><p>{loading ? 'Loading records from the database…' : `${rows.length} record${rows.length === 1 ? '' : 's'} available`}</p></div>
        {section === 'invoices' && <div className="proc-tabs" role="tablist" aria-label="Record type"><button role="tab" aria-selected={tab === 'Invoices'} className={tab === 'Invoices' ? 'active' : ''} onClick={() => { setTab('Invoices'); setStatusFilter('all'); }}>Invoices</button><button role="tab" aria-selected={tab === 'Contracts'} className={tab === 'Contracts' ? 'active' : ''} onClick={() => { setTab('Contracts'); setStatusFilter('all'); }}>Contracts</button></div>}
      </div>
      <div className="proc-toolbar">
        <label className="proc-search"><Search size={19} /><input value={query} onChange={event => setQuery(event.target.value)} placeholder={`Search ${section === 'purchase-orders' ? 'orders, suppliers, or products' : section === 'suppliers' ? 'suppliers and categories' : 'invoice and contract records'}…`} aria-label="Search procurement records" /></label>
        <label className="proc-status-select"><span>Status</span><select value={statusFilter} onChange={event => setStatusFilter(event.target.value)} aria-label="Filter by status"><option value="all">All statuses</option>{statuses.map(value => <option key={value} value={value}>{value}</option>)}</select></label>
        <span className="proc-result-count">{visible.length} shown</span>
      </div>
      <div className="proc-table-scroll"><table className="proc-table"><thead><tr>{columns.map((column, index) => <th key={index} scope="col">{column}</th>)}</tr></thead><tbody>
        {visible.map(row => <tr key={row.key} onClick={() => setSelected(row)}>
          <td className="proc-id-cell"><RecordIdentity value={row.id} kind={section === 'purchase-orders' ? 'purchase-order' : section === 'suppliers' ? 'supplier' : tab === 'Invoices' ? 'invoice' : 'auto'} /></td><td className="proc-supplier-name">{text(row.name)}</td><td className="proc-product-cell">{section === 'purchase-orders' ? <RecordIdentity value={row.detail} kind="product" compact /> : section === 'invoices' && tab === 'Invoices' ? <RecordIdentity value={row.detail} kind="purchase-order" compact /> : text(row.detail)}</td>
          {section === 'purchase-orders' ? <><td>{row.quantity}</td><td>{money(row.amount, row.currency)}</td><td>{money(row.total, row.currency)}</td></>
            : section === 'suppliers' ? <><td>{row.amount == null ? 'Not rated' : `${row.amount.toFixed(1)} / 5`}</td><td>{row.total}</td></>
            : <><td>{money(row.amount, row.currency)}</td><td>{date(row.date)}</td></>}
          <td><span className={`proc-pill ${/duplicate|high|suspicious/i.test(label(row.status)) ? 'proc-pill-warning' : /open|active|approved/i.test(label(row.status)) ? 'proc-pill-positive' : ''}`}>{label(row.status)}</span></td>
          <td><button className="proc-open-row" aria-label={`View details for ${row.id}`} onClick={event => { event.stopPropagation(); setSelected(row); }}>View <ArrowRight size={16} /></button></td>
        </tr>)}
        {!visible.length && <tr><td colSpan={columns.length} className="proc-empty">{loading ? 'Loading records from the database…' : error ? 'Records unavailable. Check the Backend connection.' : rows.length ? 'No records match the current search or filter.' : section === 'invoices' && tab === 'Contracts' ? 'There are no contract records available for this account.' : 'No records are available for this account.'}</td></tr>}
      </tbody></table></div>
      <footer className="proc-table-footer"><span>Showing {visible.length} of {rows.length} records</span><span>Records are scoped to your authenticated account</span></footer>
    </section>
    {selected && <ProcurementRecordDrawer row={selected} section={section} tab={tab} onClose={() => setSelected(null)} onNegotiate={openNegotiation} />}
  </main>;
}
