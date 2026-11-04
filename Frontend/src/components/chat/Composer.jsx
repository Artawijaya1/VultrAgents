import { useRef, useState } from 'react';
import { Send } from 'lucide-react';

export default function Composer({ onSend, disabled }) {
  const [text, setText] = useState('');
  const textareaRef = useRef(null);

  const charCount = text.length;
  const overLimit = charCount > 1000;
  const canSend = text.trim().length > 0 && !overLimit && !disabled;

  const submit = () => {
    if (!canSend) return;
    onSend(text.trim());
    setText('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const handleInput = (e) => {
    setText(e.target.value);
    const el = e.target;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
  };

  return (
    <div className="chat-composer">
      <div className="composer-input-wrap">
        <textarea
          ref={textareaRef}
          className="composer-textarea"
          value={text}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about this Purchase Order…"
          rows={1}
          maxLength={1001}
          disabled={disabled}
          aria-label="Chat message input"
        />
        <div className="composer-meta">
          <span className={overLimit ? 'char-over' : ''}>{charCount}/1000</span>
          <span className="composer-hint">Enter to send · Shift+Enter for new line</span>
        </div>
      </div>
      <button className="chat-btn chat-btn-primary composer-send" onClick={submit} disabled={!canSend} aria-label="Send message">
        <Send size={16} />
      </button>
    </div>
  );
}
