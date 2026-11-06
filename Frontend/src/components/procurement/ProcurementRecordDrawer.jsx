import { useEffect } from 'react';
import { ArrowRight, X, FileText } from 'lucide-react';
import { presentRecordCode } from '../../utils/recordPresentation';

const LABELS = {
  id: 'Record ID', supplierId: 'Supplier ID', supplierName: 'Supplier name',
  productId: 'Product ID', productName: 'Product name', invoiceNumber: 'Invoice number',
  purchaseOrderId: 'Purchase Order ID', contractId: 'Contract ID',
  quantity: 'Quantity', unit: 'Unit', currency: 'Currency',
  currentOffer: 'Offered unit price', targetPrice: 'Budget ceiling per unit',
  historicalPrice: 'Previous unit price', contractUnitPrice: 'Contract unit price',
  amount: 'Invoice amount', value: 'Contract value', total: 'Order value',
  rating: 'Supplier rating', category: 'Category', status: 'Status',
  createdDate: 'Created on', issueDate: 'Issue date', dueDate: 'Due date',
  requiredDeliveryDate: 'Required delivery', offeredDeliveryDate: 'Offered delivery',
  preferredDeliveryDate: 'Preferred delivery', bankLastChangedAt: 'Bank details last changed',
  paymentTerms: 'Payment terms', deliveryTerms: 'Delivery terms',
  minimumOrderQuantity: 'Minimum order quantity', requester: 'Requested by',
};
const PRICE_KEYS = /(?:Price|Offer|Amount|Value|^total$)/i;
const DATE_KEYS = /(?:Date|At|_date)$/i;
const FIRST = ['id', 'supplierId', 'supplierName', 'productId', 'productName', 'invoiceNumber', 'purchaseOrderId', 'contractId', 'status', 'category', 'rating'];
const SECOND = ['quantity', 'unit', 'currentOffer', 'targetPrice', 'historicalPrice', 'contractUnitPrice', 'amount', 'value', 'total', 'currency'];
const THIRD = ['createdDate', 'issueDate', 'dueDate', 'requiredDeliveryDate', 'offeredDeliveryDate', 'preferredDeliveryDate', 'bankLastChangedAt', 'paymentTerms', 'deliveryTerms', 'minimumOrderQuantity', 'requester'];

function formatLabel(key) {
  return LABELS[key] || key.replaceAll('_', ' ').replace(/([a-z])([A-Z])/g, '$1 $2').replace(/^./, c => c.toUpperCase());
}
function formatValue(key, value, record) {
  if (value === null || value === undefined || value === '') return 'Not provided';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (typeof value === 'number' && PRICE_KEYS.test(key)) {
    const currency = typeof record.currency === 'string' && /^[A-Z]{3}$/.test(record.currency) ? record.currency : 'IDR';
    try { return new Intl.NumberFormat('en-US', { style: 'currency', currency, maximumFractionDigits: 0 }).format(value); }
    catch { return value.toLocaleString('en-US'); }
  }
  if (typeof value === 'number') return value.toLocaleString('en-US');
  if (DATE_KEYS.test(key) && /^\d{4}-\d{2}-\d{2}/.test(String(value))) {
    const parsed = new Date(String(value).slice(0, 10) + 'T12:00:00');
    if (!Number.isNaN(parsed.getTime())) return new Intl.DateTimeFormat('en-US', { dateStyle: 'medium' }).format(parsed);
  }
  if (typeof value === 'object') return JSON.stringify(value, null, 2);
  return String(value);
}

function FieldSection({ title, entries, record }) {
  if (!entries.length) return null;
  return <section className="proc-drawer-section">
    <h3>{title}</h3>
    <dl className="proc-drawer-fields">
      {entries.map(([key, value]) => <div className="proc-drawer-field" key={key}>
        <dt>{formatLabel(key)}</dt>
        <dd className={value == null || value === '' ? 'proc-value-empty' : ''}>{formatValue(key, value, record)}</dd>
      </div>)}
    </dl>
  </section>;
}

export default function ProcurementRecordDrawer({ row, section, tab, onClose, onNegotiate }) {
  useEffect(() => {
    const onKeyDown = event => { if (event.key === 'Escape') onClose(); };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [onClose]);

  if (!row) return null;
  const record = row.record || {};
  const kind = section === 'purchase-orders' ? 'purchase-order' : section === 'suppliers' ? 'supplier' : tab === 'Invoices' ? 'invoice' : 'auto';
  const title = presentRecordCode(row.id, kind).title;
  const entries = Object.entries(record).filter(([, value]) => typeof value !== 'function');
  const group = keys => keys.flatMap(key => entries.filter(([field]) => field === key));
  const used = new Set([...FIRST, ...SECOND, ...THIRD]);
  const remainder = entries.filter(([key]) => !used.has(key));

  return <>
    <button type="button" className="proc-detail-backdrop" aria-label="Close record details" onClick={onClose} />
    <aside className="proc-detail-drawer proc-detail-drawer--polished" role="dialog" aria-modal="true" aria-label={`Details for ${row.id}`}>
      <header className="proc-drawer-header">
        <div className="proc-drawer-heading">
          <span className="proc-drawer-eyebrow"><FileText size={15} /> Procurement record</span>
          <h2>{title}</h2>
          <p className="proc-drawer-raw-code">{row.id}</p>
        </div>
        <button type="button" aria-label="Close details" onClick={onClose}><X size={20} /></button>
      </header>
      <div className="proc-drawer-content">
        <FieldSection title="Record information" entries={group(FIRST)} record={record} />
        <FieldSection title="Pricing & quantities" entries={group(SECOND)} record={record} />
        <FieldSection title="Dates & terms" entries={group(THIRD)} record={record} />
        <FieldSection title="Additional information" entries={remainder} record={record} />
      </div>
      {section === 'purchase-orders' && <div className="proc-drawer-actions">
        <button type="button" className="primary" onClick={() => onNegotiate(record)}>
          Open Negotiation Copilot <ArrowRight size={17} />
        </button>
      </div>}
    </aside>
  </>;
}
