import { AlertTriangle } from 'lucide-react';

const SEVERITY_CLASS = { high: 'sev-high', medium: 'sev-medium', low: 'sev-low' };

export default function RiskFindings({ precheck }) {
  if (!precheck || !precheck.findings || precheck.findings.length === 0) return null;

  return (
    <div className="chat-risk-findings">
      <div className="findings-header">
        <AlertTriangle size={14} />
        <span>{precheck.flag_count} indicator{precheck.flag_count !== 1 ? 's' : ''} for review</span>
      </div>
      <p className="findings-disclaimer">Indicator for review, not proof of fraud.</p>
      <ul className="findings-list">
        {precheck.findings.map((f, i) => (
          <li key={f.rule_id || i} className="finding-item">
            <div className="finding-top">
              <code className="finding-rule">{f.rule_id}</code>
              <span className={`finding-severity ${SEVERITY_CLASS[f.severity] || ''}`}>{f.severity}</span>
            </div>
            <p className="finding-desc">{f.description}</p>
            {f.evidence_record_ids && f.evidence_record_ids.length > 0 && (
              <div className="finding-evidence">
                <span>Evidence records:</span>
                {f.evidence_record_ids.map(id => <code key={id}>{id}</code>)}
              </div>
            )}
            {f.next_action && <p className="finding-action">Next step: {f.next_action}</p>}
          </li>
        ))}
      </ul>
    </div>
  );
}
