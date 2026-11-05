import { ApiError, chatWithAgent, approveApproval, rejectApproval } from './api';

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
    approvalStatus: raw.approval_status ?? (raw.approval_id ? 'pending' : null),
    error: raw.error ?? null,
    notice: raw.notice ?? null,
    createdAt: raw.created_at ?? new Date().toISOString(),
  };
}

const REFERENCE_ID_RE = /^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$/;
export function validateTask(task) { return ['negotiation', 'fraud'].includes(task) ? '' : 'Task must be "negotiation" or "fraud".'; }
export function validateReferenceId(id) { return !id ? 'Purchase Order ID is required.' : !REFERENCE_ID_RE.test(id) ? 'Invalid PO ID format (alphanumeric, max 100 chars).' : ''; }
export function validateQuestion(question) { return !question?.trim() ? 'Question is required.' : question.length > 1000 ? `Question too long (${question.length}/1000 chars).` : ''; }

const conversations = new Map();
export async function createChatConversation(task, referenceId) {
  const id = crypto.randomUUID();
  conversations.set(id, { task, referenceId, messages: [] });
  return { id, task, referenceId, sessionId: id };
}
export async function getChatMessages(id) { return conversations.get(id)?.messages ?? []; }
export async function sendChatMessage(id, question, task, referenceId) {
  const conversation = conversations.get(id);
  if (!conversation || conversation.task !== task || conversation.referenceId !== referenceId) throw new ApiError('Agent session context has changed. Start a new chat.', 400);
  const raw = await chatWithAgent(task, referenceId, id, question);
  const userMessage = normalize({ id: crypto.randomUUID(), question }, 'user');
  const assistantMessage = normalize(raw, 'assistant');
  conversation.messages.push(userMessage, assistantMessage);
  return assistantMessage;
}
export async function sendChatFeedback() { throw new ApiError('Message feedback is not implemented by Backend yet.', 501); }
export const approveChatApproval = id => approveApproval(id);
export const rejectChatApproval = id => rejectApproval(id);
export { normalize, ApiError };
