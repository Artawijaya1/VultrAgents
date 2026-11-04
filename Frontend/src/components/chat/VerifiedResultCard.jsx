import { CheckCircle } from 'lucide-react';

function formatValue(val) {
  if (val === null || val === undefined) return '—';
  if (typeof val === 'number') return val.toLocaleString();
  if (typeof val === 'boolean') return val ? 'Yes' : 'No';
  return String(val);
}

export default function VerifiedResultCard({ data, task }) {
  if (!data || typeof data !== 'object') return null;

  const entries = Object.entries(data);
  if (entries.length === 0) return null;

  return (
    <div className="chat-verified-card">
      <div className="verified-header">
        <CheckCircle size={14} />
        <span>Verified data{task === 'negotiation' ? ' — Negotiation' : task === 'fraud' ? ' — Fraud scan' : ''}</span>
      </div>
      <dl className="verified-grid">
        {entries.map(([key, val]) => (
          <div key={key} className="verified-item">
            <dt>{key.replace(/_/g, ' ')}</dt>
            <dd>{formatValue(val)}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
