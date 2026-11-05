import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Handshake, RefreshCw, ShieldCheck } from 'lucide-react';
import { createNegotiation, getNegotiations } from '../services/api';
import { getPurchaseOrders, getSuppliers } from '../services/procurementService';
import './negotiation.css';

const money = (value, currency = 'IDR') => new Intl.NumberFormat('en-US', { style: 'currency', currency: currency || 'IDR', maximumFractionDigits: 0 }).format(value || 0);

export default function NegotiationPage() {
  const [orders, setOrders] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [history, setHistory] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [targetPrice, setTargetPrice] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const [purchaseOrders, supplierRows, negotiations] = await Promise.all([getPurchaseOrders(), getSuppliers(), getNegotiations()]);
      setOrders(purchaseOrders);
      setSuppliers(supplierRows);
      setHistory(Array.isArray(negotiations) ? negotiations : negotiations?.items ?? []);
      setSelectedId(current => current && purchaseOrders.some(order => order.id === current) ? current : purchaseOrders[0]?.id ?? '');
    } catch (err) {
      setError(err?.message || 'Could not load purchase orders from Backend.');
    } finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const order = orders.find(item => item.id === selectedId);
  const supplier = suppliers.find(item => item.id === order?.supplierId);
  useEffect(() => { if (order) setTargetPrice(String(order.targetPrice || '')); }, [order?.id, order?.targetPrice]);
  const proposed = Number(targetPrice);
  const savings = order && Number.isFinite(proposed) ? Math.max(0, (order.currentOffer - proposed) * order.quantity) : 0;
  const recommendations = useMemo(() => {
    if (!order) return [];
    const reference = order.historicalPrice;
    return [
      { title: 'Price target', value: money(proposed || order.targetPrice, order.currency), reason: `Database budget ceiling is ${money(order.targetPrice, order.currency)} per unit; previous unit price is ${money(reference, order.currency)}.` },
      { title: 'Current offer', value: money(order.currentOffer, order.currency), reason: `Difference from previous recorded price: ${money(order.currentOffer - reference, order.currency)} per unit.` },
      { title: 'Potential price gap', value: money(savings, order.currency), reason: 'Calculated from this purchase order quantity and the target price entered above.' },
    ];
  }, [order, proposed, savings]);

  const saveAnalysis = async () => {
    if (!order || !Number.isFinite(proposed) || proposed <= 0) return;
    setSaving(true); setNotice(''); setError('');
    try {
      const record = await createNegotiation({ po_id: order.id, context: { target_unit_price: proposed, offered_unit_price: order.currentOffer, quantity: order.quantity, currency: order.currency } });
      setHistory(current => [record, ...current]);
      setNotice('Analysis saved in the Backend database.');
    } catch (err) { setError(err?.message || 'Could not save the analysis.'); }
    finally { setSaving(false); }
  };

  return <main className="negotiation-page">
    <header className="neg-page-header"><div className="neg-page-title"><div className="neg-breadcrumb"><Link to="/dashboard">Dashboard</Link><ArrowRight size={13} /><span>Negotiation Copilot</span></div><div className="neg-title-line"><span className="neg-title-icon"><Handshake size={21} /></span><div><h1>Negotiation Copilot</h1><p>Review negotiation guidance grounded in your database purchase order and supplier records.</p></div></div></div><button className="neg-button neg-button-quiet" onClick={load}><RefreshCw size={14} /> Refresh records</button></header>
    <div className="neg-demo-banner"><ShieldCheck size={15} /><span>Database-backed procurement records</span><span className="banner-separator">·</span><span>Recommendations use the selected order's actual prices and quantity.</span></div>
    {error && <div className="fraud-page-error" role="alert">{error}</div>}{notice && <div className="neg-demo-banner" role="status">{notice}</div>}
    <section className="negotiation-context-panel"><header><div><small>PROCUREMENT CONTEXT</small><h2>Select a purchase order</h2></div></header><div className="negotiation-context-grid"><label className="neg-field"><span>Purchase order</span><select value={selectedId} onChange={event => setSelectedId(event.target.value)}><option value="">Select a database purchase order</option>{orders.map(item => <option key={item.id} value={item.id}>{item.id} · {item.productName}</option>)}</select></label><div className="neg-field"><span>Supplier</span><b>{supplier?.name || '—'}</b></div><div className="neg-field"><span>Order quantity</span><b>{order ? `${order.quantity} ${order.unit || 'units'}` : '—'}</b></div><div className="neg-field"><span>Current offer</span><b>{order ? money(order.currentOffer, order.currency) : '—'}</b></div><div className="neg-field"><span>Previous unit price</span><b>{order ? money(order.historicalPrice, order.currency) : '—'}</b></div><div className="neg-field"><span>Budget ceiling</span><b>{order ? money(order.targetPrice, order.currency) : '—'}</b></div></div></section>
    {order && <><section className="negotiation-context-panel"><header><div><small>GUIDANCE BASED ON DATABASE VALUES</small><h2>Negotiation reference</h2></div></header><label className="neg-field"><span>Target unit price</span><input type="number" min="1" value={targetPrice} onChange={event => setTargetPrice(event.target.value)} /></label><div className="negotiation-strategy-grid">{recommendations.map(item => <article className="neg-strategy-card" key={item.title}><h3>{item.title}</h3><strong>{item.value}</strong><p>{item.reason}</p></article>)}</div><p>Estimated savings against current offer: <b>{money(savings, order.currency)}</b></p><button className="neg-button neg-button-primary" onClick={saveAnalysis} disabled={saving || !Number.isFinite(proposed) || proposed <= 0}>{saving ? 'Saving…' : 'Save analysis'} <ArrowRight size={14} /></button></section>
      <section className="negotiation-context-panel"><header><div><small>DATABASE HISTORY</small><h2>Saved negotiations</h2></div></header>{history.length ? <div className="negotiation-history-list">{history.map((item, index) => <article key={item.negotiation_id ?? item.id ?? index}><b>{item.purchase_order_id ?? item.po_id}</b><span>{item.supplier_name || 'Supplier record'}</span><span>{item.status}</span><time>{item.created_at ? new Date(item.created_at).toLocaleString() : ''}</time></article>)}</div> : <p>{loading ? 'Loading saved negotiations…' : 'No saved negotiations for this account yet.'}</p>}</section></>}
    {!order && !loading && !error && <section className="negotiation-context-panel"><h2>No purchase orders available</h2><p>This account has no purchase orders in the Backend database.</p><Link to="/dashboard/purchase-orders">Open Purchase Orders <ArrowRight size={14} /></Link></section>}
    {loading && <p>Loading purchase orders from Backend…</p>}
  </main>;
}
