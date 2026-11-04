import {
  ApiError,
  createConversation as apiCreateConversation,
  getConversationMessages as apiGetMessages,
  sendConversationMessage as apiSendMessage,
  sendMessageFeedback as apiSendFeedback,
  approveApproval as apiApprove,
  rejectApproval as apiReject,
} from './api';

// ── Internal message model ──────────────────────────────────────────
// Every component reads ONLY this shape. Raw backend/agent fields are
// normalized here and nowhere else.
//
// {
//   id:               string
//   role:             'user' | 'assistant'
//   content:          string          (answer text or user question)
//   status:           string | null   (draft, review_required, no_flags, …)
//   verifiedResult:   object | null
//   precheck:         object | null   ({ flag_count, findings[] })
//   toolTrace:        array           ([{ tool, reference_id, ok }])
//   requiresApproval: boolean
//   approvalId:       string | null
//   error:            string | null
//   notice:           string | null
//   createdAt:        string          (ISO)
// }

const REFERENCE_ID_RE = /^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$/;
const TASKS = ['negotiation', 'fraud'];

export function validateTask(task) {
  if (!TASKS.includes(task)) return 'Task must be "negotiation" or "fraud".';
  return '';
}

export function validateReferenceId(id) {
  if (!id) return 'Purchase Order ID is required.';
  if (!REFERENCE_ID_RE.test(id)) return 'Invalid PO ID format (alphanumeric, max 100 chars).';
  return '';
}

export function validateQuestion(q) {
  if (!q || !q.trim()) return 'Question is required.';
  if (q.length > 1000) return `Question too long (${q.length}/1000 chars).`;
  return '';
}

// ── Normalize raw backend/agent payload into internal model ─────────
function normalize(raw, role = 'assistant') {
  return {
    id: raw.id ?? raw.message_id ?? crypto.randomUUID(),
    role,
    content: role === 'user' ? (raw.question ?? raw.content ?? '') : (raw.answer ?? raw.content ?? ''),
    status: raw.status ?? null,
    verifiedResult: raw.verified_result ?? null,
    precheck: raw.precheck ?? null,
    toolTrace: Array.isArray(raw.tool_trace) ? raw.tool_trace : [],
    requiresApproval: raw.requires_approval === true,
    approvalId: raw.approval_id ?? null,
    error: raw.error ?? null,
    notice: raw.notice ?? null,
    createdAt: raw.created_at ?? new Date().toISOString(),
  };
}

// ── Live adapter (Backend endpoints) ────────────────────────────────
const liveAdapter = {
  async createConversation(task, referenceId) {
    const res = await apiCreateConversation(task, referenceId);
    return { id: res.id, task: res.task, referenceId: res.reference_id, sessionId: res.session_id };
  },

  async getMessages(conversationId) {
    const res = await apiGetMessages(conversationId);
    const list = Array.isArray(res) ? res : (res.messages ?? []);
    return list.map(m => normalize(m, m.role ?? 'assistant'));
  },

  async sendMessage(conversationId, question) {
    const res = await apiSendMessage(conversationId, question);
    return normalize(res, 'assistant');
  },

  async sendFeedback(messageId, rating) {
    return apiSendFeedback(messageId, rating);
  },

  async approve(approvalId) {
    return apiApprove(approvalId);
  },

  async reject(approvalId) {
    return apiReject(approvalId);
  },
};

// ── Mock adapter ────────────────────────────────────────────────────
const delay = (ms) => new Promise(r => setTimeout(r, ms));

let mockConversationCounter = 0;
let mockMessageCounter = 0;
const mockTurnCounters = {};

const MOCK_RESPONSES = {
  'negotiation:PO-001': {
    status: 'draft',
    answer: 'Based on historical purchase data, I recommend negotiating a 12% reduction from the current offered unit price. The supplier has consistently delivered on time, which gives us leverage to focus on pricing. Consider a volume-based approach for quantities above 500 units.',
    verified_result: {
      current_offer: 85000,
      target_price: 74800,
      historical_average: 78200,
      currency: 'IDR',
      potential_savings: 1020000,
      quantity: 100,
      unit: 'units',
      supplier_on_time_rate: 94.5,
      contract_price: 80000,
    },
    precheck: { flag_count: 0, findings: [] },
    tool_trace: [
      { tool: 'get_purchase_order', reference_id: 'PO-001', ok: true },
      { tool: 'get_price_history', reference_id: 'PO-001', ok: true },
      { tool: 'get_supplier_performance', reference_id: 'SUP-001', ok: true },
    ],
    requires_approval: true,
    approval_id: null,
    error: null,
    notice: null,
  },

  'fraud:PO-002': {
    status: 'review_required',
    answer: 'Two indicators require attention on this purchase order. These are flagged for review and do not confirm any wrongdoing. A procurement officer should examine the evidence records and determine next steps.',
    verified_result: {
      po_id: 'PO-002',
      supplier_id: 'SUP-003',
      scan_scope: 'po',
      total_invoices_checked: 8,
      flagged_count: 2,
    },
    precheck: {
      flag_count: 2,
      findings: [
        {
          rule_id: 'DUP-INV-001',
          severity: 'high',
          description: 'Duplicate invoice number detected across two records with different amounts.',
          evidence_record_ids: ['INV-2026-0441', 'INV-2026-0442'],
          next_action: 'Compare invoice documents and confirm with supplier accounts payable.',
        },
        {
          rule_id: 'BANK-CHG-002',
          severity: 'medium',
          description: 'Supplier bank account changed within 14 days before invoice submission.',
          evidence_record_ids: ['INV-2026-0443'],
          next_action: 'Verify bank account change through an independent channel (phone call to known contact).',
        },
      ],
    },
    tool_trace: [
      { tool: 'get_purchase_order', reference_id: 'PO-002', ok: true },
      { tool: 'get_supplier_invoices', reference_id: 'SUP-003', ok: true },
      { tool: 'check_duplicate_invoices', reference_id: 'PO-002', ok: true },
      { tool: 'check_bank_account_changes', reference_id: 'SUP-003', ok: true },
    ],
    requires_approval: true,
    approval_id: null,
    error: null,
    notice: null,
  },

  'fraud:PO-003': {
    status: 'no_flags',
    answer: 'No risk indicators were found for this purchase order. All invoices match expected patterns and no recent bank account changes were detected.',
    verified_result: {
      po_id: 'PO-003',
      supplier_id: 'SUP-002',
      scan_scope: 'po',
      total_invoices_checked: 5,
      flagged_count: 0,
    },
    precheck: { flag_count: 0, findings: [] },
    tool_trace: [
      { tool: 'get_purchase_order', reference_id: 'PO-003', ok: true },
      { tool: 'get_supplier_invoices', reference_id: 'SUP-002', ok: true },
      { tool: 'check_duplicate_invoices', reference_id: 'PO-003', ok: true },
    ],
    requires_approval: false,
    approval_id: null,
    error: null,
    notice: null,
  },

  __error: {
    status: 'model_unavailable',
    answer: '',
    verified_result: null,
    precheck: null,
    tool_trace: [],
    requires_approval: false,
    approval_id: null,
    error: 'The AI model is temporarily unavailable. Please try again later.',
    notice: null,
  },
};

const mockAdapter = {
  async createConversation(task, referenceId) {
    await delay(150);
    const id = `mock-conv-${++mockConversationCounter}`;
    mockTurnCounters[id] = 0;
    return { id, task, referenceId, sessionId: null };
  },

  async getMessages(_conversationId) {
    await delay(100);
    return [];
  },

  async sendMessage(conversationId, question, task, referenceId) {
    await delay(800 + Math.random() * 400);
    const key = `${task}:${referenceId}`;
    // Pick scenario: known key, or cycle to error on 4th+ message
    const turn = (mockTurnCounters[conversationId] ?? 0) + 1;
    mockTurnCounters[conversationId] = turn;

    let template;
    if (turn >= 4 && !MOCK_RESPONSES[key]) {
      template = MOCK_RESPONSES.__error;
    } else if (MOCK_RESPONSES[key]) {
      template = MOCK_RESPONSES[key];
    } else if (task === 'fraud') {
      template = MOCK_RESPONSES['fraud:PO-003']; // no_flags fallback
    } else {
      template = MOCK_RESPONSES['negotiation:PO-001'];
    }

    // Force error scenario on specific question
    if (question.toLowerCase().includes('trigger error')) {
      template = MOCK_RESPONSES.__error;
    }

    const msgId = `mock-msg-${++mockMessageCounter}`;
    return normalize({
      ...template,
      id: msgId,
      turn_index: turn,
      created_at: new Date().toISOString(),
    }, 'assistant');
  },

  async sendFeedback(_messageId, _rating) {
    await delay(100);
    return { ok: true };
  },

  async approve(_approvalId) {
    await delay(100);
    throw new ApiError('Approval workflow is not available yet.', 501);
  },

  async reject(_approvalId) {
    await delay(100);
    throw new ApiError('Approval workflow is not available yet.', 501);
  },
};

// ── Adapter selection ───────────────────────────────────────────────
const chatMode = import.meta.env.VITE_CHAT_MODE || 'mock';
export const isMockMode = () => chatMode === 'mock';

function getAdapter(forceMock) {
  if (forceMock || chatMode === 'mock') return mockAdapter;
  return liveAdapter;
}

// ── Public API ──────────────────────────────────────────────────────
// The `useMock` param lets the UI force mock mode when live returns 501.

export async function createChatConversation(task, referenceId, useMock = false) {
  return getAdapter(useMock).createConversation(task, referenceId);
}

export async function getChatMessages(conversationId, useMock = false) {
  return getAdapter(useMock).getMessages(conversationId);
}

export async function sendChatMessage(conversationId, question, task, referenceId, useMock = false) {
  // The mock adapter needs task/referenceId to pick a scenario;
  // the live adapter ignores the extra params.
  return getAdapter(useMock).sendMessage(conversationId, question, task, referenceId);
}

export async function sendChatFeedback(messageId, rating, useMock = false) {
  return getAdapter(useMock).sendFeedback(messageId, rating);
}

export async function approveChatApproval(approvalId, useMock = false) {
  return getAdapter(useMock).approve(approvalId);
}

export async function rejectChatApproval(approvalId, useMock = false) {
  return getAdapter(useMock).reject(approvalId);
}

export { normalize, ApiError };
