import { useEffect, useRef } from 'react';
import { ShieldCheck, AlertTriangle, Info, XCircle } from 'lucide-react';
import VerifiedResultCard from './VerifiedResultCard';
import RiskFindings from './RiskFindings';
import ToolTrace from './ToolTrace';
import ApprovalGate from './ApprovalGate';

const STATUS_LABELS = {
  draft: 'AI draft',
  review_required: 'Review required',
  no_flags: 'No risk indicators found',
  no_invoices: 'No invoices available',
  not_found: 'Reference not found',
  invalid_request: 'Invalid request',
  data_unavailable: 'Data unavailable',
  model_unavailable: 'AI model unavailable',
  needs_tool_use: 'Additional analysis needed',
  not_configured: 'Service not configured',
  step_limit: 'Analysis step limit reached',
};

function StatusBadge({ status }) {
  if (!status) return null;
  const isError = ['model_unavailable', 'not_configured', 'data_unavailable', 'invalid_request', 'not_found', 'step_limit'].includes(status);
  const isWarning = ['review_required', 'needs_tool_use'].includes(status);
  const isGood = status === 'no_flags';
  const cn = isError ? 'status-error' : isWarning ? 'status-warning' : isGood ? 'status-good' : 'status-info';
  const Icon = isError ? XCircle : isWarning ? AlertTriangle : isGood ? ShieldCheck : Info;
  return <span className={`chat-status-badge ${cn}`}><Icon size={12} /> {STATUS_LABELS[status] || status}</span>;
}

function AssistantMessage({ msg, task, onApprove, onReject }) {
  return (
    <div className="chat-message chat-message-assistant">
      <div className="chat-message-header">
        <span className="chat-role">Agent</span>
        <StatusBadge status={msg.status} />
        <span className="chat-time">{new Date(msg.createdAt).toLocaleTimeString()}</span>
      </div>
      {msg.error && <div className="chat-error-inline">{msg.error}</div>}
      {msg.notice && <div className="chat-notice-inline">{msg.notice}</div>}
      {msg.content && (
        <div className="chat-draft-label">
          <Info size={13} /> AI draft — not verified output
        </div>
      )}
      {msg.content && <p className="chat-answer-text">{msg.content}</p>}
      {msg.verifiedResult && <VerifiedResultCard data={msg.verifiedResult} task={task} />}
      {msg.precheck && msg.precheck.findings && msg.precheck.findings.length > 0 && (
        <RiskFindings precheck={msg.precheck} />
      )}
      {msg.toolTrace.length > 0 && <ToolTrace trace={msg.toolTrace} />}
      <ApprovalGate
        requiresApproval={msg.requiresApproval}
        approvalId={msg.approvalId}
        onApprove={onApprove}
        onReject={onReject}
      />
    </div>
  );
}

function UserMessage({ msg }) {
  return (
    <div className="chat-message chat-message-user">
      <div className="chat-message-header">
        <span className="chat-role">You</span>
        <span className="chat-time">{new Date(msg.createdAt).toLocaleTimeString()}</span>
      </div>
      <p className="chat-answer-text">{msg.content}</p>
    </div>
  );
}

export default function MessageList({ messages, loading, task, onApprove, onReject }) {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length, loading]);

  return (
    <div className="chat-message-list" role="log" aria-live="polite" aria-label="Chat messages">
      {messages.length === 0 && !loading && (
        <div className="chat-empty">
          <p>Choose a task and Purchase Order above, then ask a question to begin.</p>
        </div>
      )}
      {messages.map(msg =>
        msg.role === 'user'
          ? <UserMessage key={msg.id} msg={msg} />
          : <AssistantMessage key={msg.id} msg={msg} task={task} onApprove={onApprove} onReject={onReject} />
      )}
      {loading && (
        <div className="chat-message chat-message-assistant chat-typing" role="status">
          <span className="typing-dots"><i /><i /><i /></span>
          <span>Agent is thinking…</span>
        </div>
      )}
      <div ref={endRef} />
    </div>
  );
}
