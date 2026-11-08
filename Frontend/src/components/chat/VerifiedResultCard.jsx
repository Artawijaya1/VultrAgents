import { CheckCircle2 } from 'lucide-react';

const LABELS = {
  po_id: 'Purchase Order ID', supplier_id: 'Supplier ID',
  offered_unit_price: 'Offered unit price', budget_ceiling_unit: 'Budget ceiling per unit',
  previous_unit_price: 'Previous unit price', opening_offer_unit: 'Recommended opening offer',
  potential_savings_vs_offer: 'Potential savings vs current offer',
  requires_approval: 'Human approval required', draft_message: 'Draft negotiation message',
  next_action: 'Recommended next action', rule_id: 'Rule ID',
};
const HIGHLIGHT_KEYS = new Set(['status', 'agent', 'po_id', 'currency', 'offered_unit_price', 'budget_ceiling_unit', 'previous_unit_price', 'quantity', 'opening_offer_unit', 'potential_savings_vs_offer', 'requires_approval']);
const MONETARY_KEYS = /(?:price|offer|savings|ceiling|amount|value|cost)/i;
function prettyLabel(key) {
  return LABELS[key] || String(key).replaceAll('_', ' ').replace(/([a-z])([A-Z])/g, '$1 $2').replace(/^./, char => char.toUpperCase());
}
function displayScalar(val, key, currency) {
  if (val == null || val === '') return 'Not provided';
  if (typeof val === 'boolean') return val ? 'Yes' : 'No';
  if (typeof val === 'number') {
    if (MONETARY_KEYS.test(key)) return `${currency || 'IDR'} ${val.toLocaleString('en-US', { maximumFractionDigits: 2 })}`;
    return val.toLocaleString('en-US');
  }
  return String(val);
}
function DetailValue({ value, field, currency }) {
  if (Array.isArray(value)) {
    if (!value.length) return <span>None recorded</span>;
    return <ol className="verified-detail-list">{value.map((item, i) => <li key={i}>{item && typeof item === 'object' ? <div className="verified-detail-object">
      {Object.entries(item).map(([key, val]) => <div className="verified-detail-row" key={key}><span>{prettyLabel(key)}</span><strong>{val && typeof val === 'object' ? JSON.stringify(val) : displayScalar(val, key, currency)}</strong></div>)}
    </div> : displayScalar(item, field, currency)}</li>)}</ol>;
  }
  if (value && typeof value === 'object') {
    return <div className="verified-detail-object">{Object.entries(value).map(([key, val]) => <div key={key} className="verified-detail-row">
      <span>{prettyLabel(key)}</span><strong>{val && typeof val === 'object' ? JSON.stringify(val) : displayScalar(val, key, currency)}</strong>
    </div>)}</div>;
  }
  return <span>{displayScalar(value, field, currency)}</span>;
}

export default function VerifiedResultCard({ data, task }) {
  if (!data || typeof data !== 'object') return null;
  const entries = Object.entries(data);
  if (!entries.length) return null;
  const highlights = entries.filter(([key, value]) => HIGHLIGHT_KEYS.has(key) && (value == null || typeof value !== 'object'));
  const details = entries.filter(([key]) => !highlights.some(([selected]) => selected === key));
  const currency = typeof data.currency === 'string' ? data.currency : 'IDR';

  return <section className="chat-verified-card" aria-label="Verified procurement data">
    <div className="verified-header"><CheckCircle2 size={19} /><span>Verified data — {task === 'fraud' ? 'Fraud Detection' : 'Negotiation Copilot'}</span></div>
    {highlights.length > 0 && <dl className="verified-grid">
      {highlights.map(([key, value]) => <div key={key} className="verified-item">
        <dt>{prettyLabel(key)}</dt>
        <dd>{displayScalar(value, key, currency)}</dd>
      </div>)}
    </dl>}
    {details.length > 0 && <div className="verified-details">
      {details.map(([key, value]) => <section key={key} className="verified-detail-panel">
        <h4>{key === 'options' ? 'Negotiation options' : prettyLabel(key)}</h4>
        <DetailValue value={value} field={key} currency={currency} />
      </section>)}
    </div>}
  </section>;
}
