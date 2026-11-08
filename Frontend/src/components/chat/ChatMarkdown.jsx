import React from 'react';

// Render a deliberately small, safe subset of Markdown from LLM output.
// Never interpret HTML or inject raw markup from the Agent.
const INLINE_PATTERN = /(\*\*[^*\n]+\*\*|`[^`\n]+`|\*[^*\n]+\*)/g;

function renderInline(text) {
  return String(text).split(INLINE_PATTERN).filter(Boolean).map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return <code key={index}>{part.slice(1, -1)}</code>;
    }
    if (part.startsWith('*') && part.endsWith('*')) {
      return <em key={index}>{part.slice(1, -1)}</em>;
    }
    return <React.Fragment key={index}>{part}</React.Fragment>;
  });
}

export default function ChatMarkdown({ content }) {
  const lines = String(content ?? '').replace(/\r\n?/g, '\n').split('\n');
  const blocks = [];
  let paragraph = [];
  let listType = null;
  let listItems = [];

  const flushParagraph = () => {
    if (paragraph.length) {
      blocks.push({ type: 'paragraph', text: paragraph.join(' ') });
      paragraph = [];
    }
  };
  const flushList = () => {
    if (listItems.length) {
      blocks.push({ type: listType, items: listItems });
      listItems = [];
      listType = null;
    }
  };

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) {
      flushParagraph();
      flushList();
      continue;
    }
    const numbered = trimmed.match(/^(\d+)[.)]\s+(.+)$/);
    const bulleted = trimmed.match(/^[-*]\s+(.+)$/);
    const heading = trimmed.match(/^#{1,4}\s+(.+)$/);
    if (heading) {
      flushParagraph(); flushList();
      blocks.push({ type: 'heading', text: heading[1] });
    } else if (numbered || bulleted) {
      flushParagraph();
      const type = numbered ? 'ol' : 'ul';
      if (listType && listType !== type) flushList();
      listType = type;
      listItems.push(numbered ? numbered[2] : bulleted[1]);
    } else if (listItems.length) {
      // A wrapped list item belongs to the preceding item, not a new paragraph.
      listItems[listItems.length - 1] += ` ${trimmed}`;
    } else {
      paragraph.push(trimmed);
    }
  }
  flushParagraph();
  flushList();

  return <div className="chat-richtext">
    {blocks.map((block, index) => {
      if (block.type === 'heading') return <h3 key={index}>{renderInline(block.text)}</h3>;
      if (block.type === 'ol') return <ol key={index}>{block.items.map((item, i) => <li key={i}>{renderInline(item)}</li>)}</ol>;
      if (block.type === 'ul') return <ul key={index}>{block.items.map((item, i) => <li key={i}>{renderInline(item)}</li>)}</ul>;
      return <p key={index}>{renderInline(block.text)}</p>;
    })}
  </div>;
}
