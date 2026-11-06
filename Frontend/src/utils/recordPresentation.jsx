/** Display-only labels for known demo IDs. No API payloads or database IDs change. */
export function presentRecordCode(value, kind = 'auto') {
  const raw = String(value ?? '').trim();
  if (!raw) return { title: '—', raw: '', transformed: false };
  const recognized = [
    ['purchase-order', /^AGENT-DEMO-PO-(\d+)$/i, digits => `Purchase Order ${digits}`],
    ['supplier', /^AGENT-DEMO-SUP-(\d+)$/i, digits => `Supplier ${digits}`],
    ['product', /^AGENT-DEMO-PRODUCT-(\d+)$/i, digits => `Product ${digits}`],
    ['invoice', /^DEMO-DUPLICATE-(\d{4})-(\d+)$/i, (year, serial) => `Invoice ${year}-${serial}`],
  ];
  for (const [type, pattern, createTitle] of recognized) {
    if (kind !== 'auto' && type !== kind) continue;
    const match = raw.match(pattern);
    if (match) return { title: createTitle(...match.slice(1)), raw, transformed: true };
  }
  return { title: raw, raw, transformed: false };
}
export function RecordIdentity({ value, kind = 'auto', compact = false }) {
  const record = presentRecordCode(value, kind);
  return (
    <span className={`proc-record-identity${compact ? ' proc-record-identity--compact' : ''}`} title={record.raw}>
      <span className="proc-record-title">{record.title}</span>
      {record.transformed && <span className="proc-record-code">{record.raw}</span>}
    </span>
  );
}
