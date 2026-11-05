import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useOutletContext, useParams } from 'react-router-dom';
import { ArrowRight, Building2, ChevronLeft, ChevronRight, FileText, Search, ShieldCheck } from 'lucide-react';
import { useProcurementStore } from '../services/procurementStore';
import { getContracts, getInvoices, getPurchaseOrders, getSuppliers } from '../services/procurementService';
import './procurement-pages.css';

const pages = {
  'purchase-orders': { title: 'Purchase Orders', description: 'Review purchase orders stored in the procurement database.' },
  suppliers: { title: 'Suppliers', description: 'Review suppliers linked to your purchase orders.' },
  invoices: { title: 'Invoices & Contracts', description: 'Review database invoices and available contract records.' },
};
const money = (value, currency = 'IDR') => value == null ? '—' : new Intl.NumberFormat('en-US', { style: 'currency', currency: currency || 'IDR', maximumFractionDigits: 0 }).format(value);
const date = value => value ? new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(`${value.slice(0, 10)}T12:00:00`)) : '—';

export default function ProcurementPages({ section: routeSection }) {
  const { section: routeParam } = useParams();
  const section = routeSection ?? routeParam ?? 'purchase-orders';
  const page = pages[section];
  const { search: globalSearch = '' } = useOutletContext() ?? {};
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [tab, setTab] = useState('Invoices');
  const [error, setError] = useState('');
  const [selected, setSelected] = useState(null);
  const orders = useProcurementStore(state => state.purchaseOrders);
  const suppliers = useProcurementStore(state => state.suppliers);
  const invoices = useProcurementStore(state => state.invoices);
  const contracts = useProcurementStore(state => state.contracts);
  const loading = useProcurementStore(state => state.recordsLoading);
  const setRecords = useProcurementStore(state => state.setRecords);
  const setRecordsLoading = useProcurementStore(state => state.setRecordsLoading);

  useEffect(() => {
    let active = true;
    setRecords({ purchaseOrders: [], suppliers: [], invoices: [], contracts: [] });
    setError('');
    setRecordsLoading(true);
    Promise.all([getPurchaseOrders(), getSuppliers(), getInvoices(), getContracts()])
      .then(([purchaseOrders, suppliers, invoices, contracts]) => { if (active) setRecords({ purchaseOrders, suppliers, invoices, contracts }); })
      .catch(err => { if (active) setError(err?.message || 'Could not load records from Backend.'); })
      .finally(() => { if (active) setRecordsLoading(false); });
    return () => { active = false; };
  }, [section, setRecords, setRecordsLoading]);

  const visible = useMemo(() => {
    const term = `${query} ${globalSearch}`.trim().toLowerCase();
    let result;
    if (section === 'purchase-orders') result = orders.map(item => ({ id: item.id, supplier: item.supplierName || suppliers.find(s => s.id === item.supplierId)?.name || item.supplierId, detail: item.productName, amount: item.quantity * item.currentOffer, date: item.createdDate, status: item.status, record: item }));
    else if (section === 'suppliers') result = suppliers.map(item => ({ id: item.id, supplier: item.name, detail: item.category || 'Supplier', amount: item.rating, date: item.bankLastChangedAt, status: item.status, record: item }));
    else if (tab === 'Invoices') result = invoices.map(item => ({ id: item.invoiceNumber || item.id, supplier: item.supplierName || suppliers.find(s => s.id === item.supplierId)?.name || item.supplierId, detail: item.purchaseOrderId, amount: item.amount, date: item.issueDate, status: item.status || 'Not recorded', record: item }));
    else result = contracts.map(item => ({ id: item.id ?? item.contract_id, supplier: item.supplier_name ?? item.supplier_id ?? '—', detail: item.title ?? item.name ?? 'Contract', amount: item.value ?? null, date: item.end_date ?? '', status: item.status ?? '—', record: item }));
    return result.filter(row => !term || Object.values(row).filter(value => typeof value === 'string' || typeof value === 'number').join(' ').toLowerCase().includes(term));
  }, [section, tab, orders, suppliers, invoices, contracts, globalSearch, query]);

  if (!page) return null;
  const openNegotiation = order => { useProcurementStore.getState().selectContext(order.supplierId, order.id); navigate('/negotiation'); };
  const detail = selected?.record;
  return <main className="procurement-page">
    <header className="proc-page-header"><div><div className="dashboard-eyebrow"><span className="live-dot" /> DATABASE RECORDS</div><h1>{page.title}</h1><p>{page.description}</p></div><div className="proc-header-actions">{section === 'purchase-orders' && <Link className="proc-primary-button" to="/negotiation">Open Negotiation Copilot <ArrowRight size={14} /></Link>}</div></header>
    <div className="proc-demo-banner"><span className="demo-info">i</span><b>Backend database</b><span>{error || 'Showing records returned by the authenticated Backend API.'}</span><ShieldCheck size={14} /><strong>Database-backed</strong></div>
    {error && <div className="fraud-page-error" role="alert"><span>{error}</span><button onClick={() => window.location.reload()}>Retry</button></div>}
    {section === 'invoices' && <div className="proc-table-heading"><div><button className={tab === 'Invoices' ? 'active' : ''} onClick={() => setTab('Invoices')}>Invoices</button><button className={tab === 'Contracts' ? 'active' : ''} onClick={() => setTab('Contracts')}>Contracts</button></div></div>}
    <section className="proc-table-card">
      <div className="proc-table-heading"><div><h2>{section === 'invoices' ? `${tab} register` : `${page.title} register`}</h2><p>{loading ? 'Loading records…' : `${visible.length} database record${visible.length === 1 ? '' : 's'}`}</p></div><label className="proc-search"><Search size={15} /><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Search database records" /></label></div>
      <div className="proc-table-scroll"><table><thead><tr><th>RECORD</th><th>SUPPLIER</th><th>{section === 'suppliers' ? 'CATEGORY' : section === 'purchase-orders' ? 'PRODUCT' : 'REFERENCE'}</th><th>{section === 'suppliers' ? 'RATING' : 'AMOUNT'}</th><th>DATE</th><th>STATUS</th><th></th></tr></thead><tbody>
        {visible.map(row => <tr key={row.id} onClick={() => setSelected(row)}><td className="proc-id-cell">{row.id}</td><td>{row.supplier}</td><td>{row.detail || '—'}</td><td>{section === 'suppliers' ? row.amount == null ? '—' : `${row.amount}/5` : money(row.amount, (row.record.currency || 'IDR').toUpperCase())}</td><td>{date(row.date)}</td><td><span className="proc-pill">{row.status || '—'}</span></td><td><button className="proc-open-row" onClick={event => { event.stopPropagation(); setSelected(row); }}>Open <ArrowRight size={14} /></button></td></tr>)}
        {!visible.length && <tr><td colSpan="7" className="proc-empty">{loading ? 'Loading records from database…' : error ? 'Records are unavailable while Backend is unreachable.' : section === 'invoices' && tab === 'Contracts' ? 'No contract records are available in the Backend database schema.' : 'No database records found.'}</td></tr>}
      </tbody></table></div>
      <footer className="proc-table-footer"><span>Rows: {visible.length}</span></footer>
    </section>
    {selected && <><button className="proc-detail-backdrop" aria-label="Close details" onClick={() => setSelected(null)} /><aside className="proc-detail-drawer"><header><div><small>DATABASE RECORD</small><h2>{selected.id}</h2></div><button onClick={() => setSelected(null)}>×</button></header><div className="proc-detail-grid">{Object.entries(detail || {}).filter(([, value]) => value == null || ['string', 'number', 'boolean'].includes(typeof value)).map(([key, value]) => <div key={key}><small>{key.replaceAll('_', ' ')}</small><b>{value == null || value === '' ? '—' : String(value)}</b></div>)}</div>{section === 'purchase-orders' && <div className="proc-drawer-actions"><button className="primary" onClick={() => openNegotiation(detail)}>Open Negotiation Copilot <ArrowRight size={14} /></button></div>}</aside></>}
  </main>;
}
