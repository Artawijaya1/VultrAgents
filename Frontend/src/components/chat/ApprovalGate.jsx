import { ShieldCheck } from 'lucide-react';

export default function ApprovalGate({ requiresApproval, approvalId, onApprove, onReject }) {
  if (!requiresApproval) return null;

  const noId = !approvalId;
  const tooltip = noId
    ? 'No approval request yet'
    : 'Approval workflow is not available yet (backend returns 501)';

  return (
    <div className="chat-approval-gate">
      <div className="approval-banner">
        <ShieldCheck size={14} />
        <span>Human approval required — the agent has not taken any action.</span>
      </div>
      <div className="approval-actions">
        <button
          className="chat-btn chat-btn-approve"
          disabled
          title={tooltip}
          onClick={() => approvalId && onApprove?.(approvalId)}
        >
          Approve
        </button>
        <button
          className="chat-btn chat-btn-reject"
          disabled
          title={tooltip}
          onClick={() => approvalId && onReject?.(approvalId)}
        >
          Reject
        </button>
      </div>
    </div>
  );
}
