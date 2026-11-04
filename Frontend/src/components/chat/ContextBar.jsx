import { useState } from 'react';
import { Handshake, ShieldAlert } from 'lucide-react';

const REFERENCE_ID_RE = /^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$/;

export default function ContextBar({ task, referenceId, onStart, disabled, hasMessages }) {
  const [localTask, setLocalTask] = useState(task || 'negotiation');
  const [localRef, setLocalRef] = useState(referenceId || '');
  const [error, setError] = useState('');
  const [confirming, setConfirming] = useState(false);

  const handleStart = () => {
    if (!localRef.trim()) { setError('Purchase Order ID is required.'); return; }
    if (!REFERENCE_ID_RE.test(localRef.trim())) { setError('Invalid PO ID format.'); return; }
    setError('');

    if (hasMessages && (localTask !== task || localRef.trim() !== referenceId)) {
      setConfirming(true);
      return;
    }
    onStart(localTask, localRef.trim());
  };

  const confirmNew = () => {
    setConfirming(false);
    onStart(localTask, localRef.trim());
  };

  return (
    <div className="chat-context-bar">
      <div className="context-bar-fields">
        <label className="context-field">
          <span className="context-label">Task</span>
          <div className="context-select-wrap">
            {localTask === 'negotiation' ? <Handshake size={15} /> : <ShieldAlert size={15} />}
            <select value={localTask} onChange={e => { setLocalTask(e.target.value); setConfirming(false); }} disabled={disabled}>
              <option value="negotiation">Negotiation Copilot</option>
              <option value="fraud">Fraud Detection</option>
            </select>
          </div>
        </label>
        <label className="context-field">
          <span className="context-label">Purchase Order</span>
          <input
            type="text"
            value={localRef}
            onChange={e => { setLocalRef(e.target.value); setError(''); setConfirming(false); }}
            placeholder="e.g. AGENT-DEMO-PO-001"
            maxLength={100}
            disabled={disabled}
          />
        </label>
        <button className="chat-btn chat-btn-primary" onClick={handleStart} disabled={disabled}>
          {hasMessages ? 'New conversation' : 'Start conversation'}
        </button>
      </div>
      <p className="context-hint">Use a PO stored in Backend and assigned to your account. Demo ID: AGENT-DEMO-PO-001 (requires demo data setup).</p>
      {error && <p className="context-error">{error}</p>}
      {confirming && (
        <div className="context-confirm">
          <span>Starting a new conversation will clear the current messages. Continue?</span>
          <button className="chat-btn chat-btn-small" onClick={confirmNew}>Yes, start new</button>
          <button className="chat-btn chat-btn-small chat-btn-quiet" onClick={() => setConfirming(false)}>Cancel</button>
        </div>
      )}
    </div>
  );
}
