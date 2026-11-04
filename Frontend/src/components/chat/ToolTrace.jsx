import { useState } from 'react';
import { ChevronDown, ChevronRight, Wrench } from 'lucide-react';

export default function ToolTrace({ trace }) {
  const [open, setOpen] = useState(false);

  if (!trace || trace.length === 0) return null;

  return (
    <div className="chat-tool-trace">
      <button className="trace-toggle" onClick={() => setOpen(!open)} aria-expanded={open}>
        <Wrench size={13} />
        <span>What the agent did ({trace.length} tool{trace.length !== 1 ? 's' : ''})</span>
        {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
      </button>
      {open && (
        <ul className="trace-list">
          {trace.map((t, i) => (
            <li key={i} className={t.ok === false ? 'trace-fail' : 'trace-ok'}>
              <code>{t.tool}</code>
              {t.reference_id && <span className="trace-ref">{t.reference_id}</span>}
              <span className="trace-status">{t.ok === false ? '✗ failed' : '✓'}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
