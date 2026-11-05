import { useCallback, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowRight, MessageSquare, RefreshCw } from 'lucide-react';
import ContextBar from '../components/chat/ContextBar';
import MessageList from '../components/chat/MessageList';
import Composer from '../components/chat/Composer';
import {
  isMockMode,
  createChatConversation,
  sendChatMessage,
  approveChatApproval,
  rejectChatApproval,
  validateQuestion,
} from '../services/chatService';
import { ApiError } from '../services/api';
import { recordAuditEvent } from '../services/auditLogService';
import './chat.css';

export default function ChatPage() {
  const navigate = useNavigate();

  // Conversation state (in-memory only, no browser persistence)
  const [task, setTask] = useState('negotiation');
  const [referenceId, setReferenceId] = useState('');
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [approvalPendingId, setApprovalPendingId] = useState(null);
  const [useMock, setUseMock] = useState(isMockMode());

  // Error / banner state
  const [banner, setBanner] = useState('');
  const [bannerType, setBannerType] = useState('error'); // 'error' | '501' | 'network'
  const [inlineError, setInlineError] = useState('');

  const showBanner = (msg, type = 'error') => { setBanner(msg); setBannerType(type); };
  const clearBanner = () => setBanner('');

  const handleError = useCallback((err) => {
    if (err instanceof ApiError) {
      if (err.status === 401) {
        navigate('/login', { replace: true });
        return;
      }
      if (err.status === 404 && err.message?.toLowerCase().includes('purchase order')) {
        setInlineError('Purchase order not found. Use a PO stored in Backend and assigned to your account. For the demo, set up AGENT-DEMO-PO-001 in Backend first.');
        return;
      }
      if (err.status === 501) {
        showBanner('This feature is not available yet.', '501');
        return;
      }
      if (err.status === 502 || err.status === 504) {
        showBanner('The server encountered a temporary error.', 'network');
        return;
      }
      setInlineError(err.message || 'An unexpected error occurred.');
      return;
    }
    if (err?.name === 'TypeError' || err?.message?.includes('fetch')) {
      showBanner('Cannot reach the server. Check your connection.', 'network');
      return;
    }
    setInlineError(err?.message || 'An unexpected error occurred.');
  }, [navigate]);

  const switchToMock = () => { setUseMock(true); clearBanner(); };

  // Start or restart conversation
  const handleStart = useCallback(async (newTask, newRef) => {
    setTask(newTask);
    setReferenceId(newRef);
    setMessages([]);
    setConversationId(null);
    setApprovalPendingId(null);
    clearBanner();
    setInlineError('');
    setLoading(true);
    try {
      const conv = await createChatConversation(newTask, newRef, useMock);
      setConversationId(conv.id);
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  }, [useMock, handleError]);

  // Send message
  const handleSend = useCallback(async (questionText) => {
    const qErr = validateQuestion(questionText);
    if (qErr) { setInlineError(qErr); return; }
    setInlineError('');

    // Add user message immediately
    const userMsg = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: questionText,
      status: null,
      verifiedResult: null,
      precheck: null,
      toolTrace: [],
      requiresApproval: false,
      approvalId: null,
      error: null,
      notice: null,
      createdAt: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    // If no conversation yet, create one first
    let cid = conversationId;
    if (!cid) {
      try {
        const conv = await createChatConversation(task, referenceId, useMock);
        cid = conv.id;
        setConversationId(cid);
      } catch (err) {
        setLoading(false);
        handleError(err);
        return;
      }
    }

    try {
      const assistantMsg = await sendChatMessage(cid, questionText, task, referenceId, useMock);
      setMessages(prev => [...prev, assistantMsg]);
      recordAuditEvent({ category: 'Agent', action: 'Agent chat response received', entityType: 'Purchase order', entityId: referenceId, outcome: assistantMsg.status || 'Completed', summary: `Agent chat handled a ${task} request for ${referenceId}.`, details: { task, sessionId: cid } });
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  }, [conversationId, task, referenceId, useMock, handleError]);

  const decideApproval = useCallback(async (approvalId, decision) => {
    setApprovalPendingId(approvalId);
    setInlineError('');
    try {
      const result = decision === 'approved'
        ? await approveChatApproval(approvalId, useMock)
        : await rejectChatApproval(approvalId, useMock);
      const status = result?.status || decision;
      setMessages(current => current.map(message => message.approvalId === approvalId
        ? { ...message, approvalStatus: status }
        : message));
      recordAuditEvent({ category: 'Agent', action: `Agent approval ${status}`, entityType: 'Approval request', entityId: approvalId, outcome: status, summary: `Approval request ${approvalId} was ${status}.`, details: { status } });
    } catch (err) {
      handleError(err);
    } finally {
      setApprovalPendingId(null);
    }
  }, [useMock, handleError]);

  const handleApprove = useCallback(approvalId => decideApproval(approvalId, 'approved'), [decideApproval]);
  const handleReject = useCallback(approvalId => decideApproval(approvalId, 'rejected'), [decideApproval]);

  const hasConversation = !!conversationId;

  return (
    <main className="chat-page">
      <header className="chat-page-header">
        <div className="chat-page-title">
          <div className="chat-breadcrumb">
            <Link to="/dashboard">Dashboard</Link>
            <ArrowRight size={13} />
            <span>Agent Chat</span>
          </div>
          <div className="chat-title-line">
            <span className="chat-title-icon"><MessageSquare size={21} /></span>
            <div>
              <h1>Agent Chat</h1>
              <p>Chat with the procurement AI agent about a specific Purchase Order.</p>
            </div>
          </div>
        </div>
      </header>

      {useMock && (
        <div className="chat-demo-banner">
          <span className="demo-info">i</span>
          <span>Simulated data</span>
          <span className="banner-separator">&middot;</span>
          <span>Running in mock mode. Responses use local demonstration data.</span>
        </div>
      )}

      {banner && (
        <div className={`chat-banner chat-banner-${bannerType}`}>
          <span>{banner}</span>
          {bannerType === '501' && !isMockMode() && (
            <button className="chat-btn chat-btn-small" onClick={switchToMock}>Switch to mock mode</button>
          )}
          {bannerType === 'network' && (
            <button className="chat-btn chat-btn-small" onClick={clearBanner}><RefreshCw size={13} /> Dismiss</button>
          )}
          {bannerType === 'error' && (
            <button className="chat-btn chat-btn-small" onClick={clearBanner}>Dismiss</button>
          )}
        </div>
      )}

      <ContextBar
        task={task}
        referenceId={referenceId}
        onStart={handleStart}
        disabled={loading}
        hasMessages={messages.length > 0}
      />

      <div className="chat-body">
        <MessageList
          messages={messages}
          loading={loading}
          task={task}
          approvalPendingId={approvalPendingId}
          onApprove={handleApprove}
          onReject={handleReject}
        />
      </div>

      {inlineError && <div className="chat-inline-error">{inlineError}</div>}

      <Composer onSend={handleSend} disabled={!hasConversation || loading} />
    </main>
  );
}
