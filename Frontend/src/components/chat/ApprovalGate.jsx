import { ShieldCheck } from 'lucide-react';

export default function ApprovalGate({ requiresApproval, approvalId, approvalStatus, busy, onApprove, onReject }) {
  if (!requiresApproval) return null;

  const noId = !approvalId;
  const canDecide = !noId && (approvalStatus === 'pending' || !approvalStatus) && !busy;
  const statusLabel = approvalStatus === 'approved'
    ? 'Approved by human reviewer'
    : approvalStatus === 'rejected'
      ? 'Rejected by human reviewer'
      : noId
        ? 'No approval request was created for this response.'
        : null;

  return (
    <div className="chat-approval-gate">
      <div className="approval-banner">
        <ShieldCheck size={14} />
        <span>Human approval required — the agent has not taken any action.</span>
      </div>
      {statusLabel && <div className={`approval-result ${approvalStatus || 'unavailable'}`} role="status">{statusLabel}</div>}
      <div className="approval-actions">
        <button
          className="chat-btn chat-btn-approve"
          disabled={!canDecide}
          title={noId ? 'No approval request is attached to this response' : undefined}
          aria-busy={busy}
          onClick={() => approvalId && onApprove?.(approvalId)}
        >
          {busy ? 'Saving…' : approvalStatus === 'approved' ? 'Approved' : 'Approve'}
        </button>
        <button
          className="chat-btn chat-btn-reject"
          disabled={!canDecide}
          title={noId ? 'No approval request is attached to this response' : undefined}
          aria-busy={busy}
          onClick={() => approvalId && onReject?.(approvalId)}
        >
          {busy ? 'Saving…' : approvalStatus === 'rejected' ? 'Rejected' : 'Reject'}
        </button>
      </div>
    </div>
  );
}
