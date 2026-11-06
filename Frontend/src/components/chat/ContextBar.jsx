import { useState } from 'react';
import { Handshake, ShieldAlert } from 'lucide-react';

const REFERENCE_ID_RE = /^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$/;
const AGENTS = [
  { id: 'negotiation', name: 'Negotiation Copilot', Icon: Handshake },
  { id: 'fraud', name: 'Fraud Detection', Icon: ShieldAlert },
];

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
        <fieldset className="context-agent-field" disabled={disabled}>
          <legend className="context-label">Choose an AI agent</legend>
          <div className="context-agent-choices" aria-label="Choose an AI agent">
            {AGENTS.map(({ id, name, Icon }) => (
              <button
                key={id}
                type="button"
                className={`context-agent-choice${localTask === id ? ' is-selected' : ''}`}
                aria-pressed={localTask === id}
                onClick={() => { setLocalTask(id); setConfirming(false); }}
                disabled={disabled}
              >
                <Icon size={19} aria-hidden="true" />
                <span>{name}</span>
              </button>
            ))}
          </div>
        </fieldset>
        <label className="context-field context-po-field">
          <span className="context-label">Purchase Order ID</span>
          <input
            type="text"
            value={localRef}
            onChange={e => { setLocalRef(e.target.value); setError(''); setConfirming(false); }}
            placeholder="e.g. AGENT-DEMO-PO-002"
            maxLength={100}
            disabled={disabled}
          />
        </label>
        <button type="button" className="chat-btn chat-btn-primary context-start-btn" onClick={handleStart} disabled={disabled}>
          {hasMessages ? 'New conversation' : 'Start conversation'}
        </button>
      </div>
      <p className="context-hint">Select either agent above. Only purchase orders assigned to your account can be used.</p>
      {error && <p className="context-error" role="alert">{error}</p>}
      {confirming && (
        <div className="context-confirm">
          <span>Starting a new conversation will clear the current messages. Continue?</span>
          <button type="button" className="chat-btn chat-btn-small" onClick={confirmNew}>Yes, start new</button>
          <button type="button" className="chat-btn chat-btn-small chat-btn-quiet" onClick={() => setConfirming(false)}>Cancel</button>
        </div>
      )}
    </div>
  );
}
