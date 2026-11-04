import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import { Check, Clipboard, LoaderCircle, MessageSquareText, RefreshCw, RotateCcw, Sparkles } from 'lucide-react';
import { formatDate } from './NegotiationContext';
export default function NegotiationComposer({ supplier, order, inputs, strategy, onStrategyChange, onGenerate }) {
    const [tone, setTone] = useState('Professional');
    const [language, setLanguage] = useState('English');
    const [draft, setDraft] = useState('');
    const [loading, setLoading] = useState(false);
    const [copied, setCopied] = useState(false);
    const [notice, setNotice] = useState('');
    useEffect(() => { setDraft(''); setNotice(''); }, [supplier.id, order.id, strategy, tone, language, inputs.offeredUnitPrice, inputs.requestedQuantity, inputs.proposedDeliveryDate, inputs.preferredDeliveryDate, inputs.targetUnitPrice, inputs.notes]);
    const strategyName = strategy === 'price' ? 'Price optimization' : strategy === 'delivery' ? 'Delivery optimization' : 'Volume negotiation';
    const generate = async () => { setLoading(true); setNotice(''); try {
        setDraft(await onGenerate(tone, language));
    }
    catch {
        setNotice('Could not create the local draft. Please try again.');
    }
    finally {
        setLoading(false);
    } };
    const copy = async () => { if (!draft)
        return; try {
        await navigator.clipboard.writeText(draft);
        setCopied(true);
        window.setTimeout(() => setCopied(false), 1800);
    }
    catch {
        setNotice('Clipboard access is unavailable. Select and copy the draft manually.');
    } };
    const reset = () => { setDraft(''); setNotice(''); setCopied(false); };
    return _jsxs("section", { className: "neg-section composer-section", id: "message-composer", children: [_jsxs("div", { className: "neg-section-heading", children: [_jsxs("div", { children: [_jsx("span", { className: "neg-step-label", children: "05 / SUPPLIER COMMUNICATION" }), _jsx("h2", { children: "Negotiation Message Composer" }), _jsx("p", { children: "Prepare an editable message for human review. Nothing is sent from this workspace." })] }), _jsx("span", { className: "section-icon", children: _jsx(MessageSquareText, { size: 18 }) })] }), _jsxs("div", { className: "composer-panel", children: [_jsxs("div", { className: "composer-toolbar", children: [_jsxs("div", { className: "composer-context", children: [_jsxs("span", { children: [_jsx("b", { children: "To" }), " ", supplier.name] }), _jsxs("span", { children: [_jsx("b", { children: "PO" }), " ", order.id] }), _jsxs("span", { children: [_jsx("b", { children: "Strategy" }), " ", strategyName] })] }), _jsxs("div", { className: "composer-controls", children: [_jsxs("label", { children: [_jsx("span", { children: "STRATEGY" }), _jsxs("select", { value: strategy, onChange: event => onStrategyChange(event.target.value), "aria-label": "Selected strategy", children: [_jsx("option", { value: "price", children: "Price optimization" }), _jsx("option", { value: "delivery", children: "Delivery optimization" }), _jsx("option", { value: "volume", children: "Volume negotiation" })] })] }), _jsxs("label", { children: [_jsx("span", { children: "TONE" }), _jsx("select", { value: tone, onChange: event => setTone(event.target.value), "aria-label": "Communication tone", children: ['Professional', 'Collaborative', 'Firm'].map(item => _jsx("option", { children: item }, item)) })] }), _jsxs("label", { children: [_jsx("span", { children: "LANGUAGE" }), _jsxs("select", { value: language, onChange: event => setLanguage(event.target.value), "aria-label": "Draft language", children: [_jsx("option", { children: "English" }), _jsx("option", { children: "Bahasa Indonesia" })] })] })] })] }), _jsxs("div", { className: "draft-header", children: [_jsxs("div", { children: [_jsx("b", { children: "Message draft" }), _jsxs("small", { children: ["Proposed delivery: ", formatDate(inputs.proposedDeliveryDate)] })] }), _jsx("span", { className: "editable-label", children: "EDITABLE" })] }), _jsx("textarea", { className: "draft-textarea", value: draft, onChange: event => setDraft(event.target.value), placeholder: "Generate a draft based on the selected purchase context and negotiation strategy. You can edit it here before review.", rows: 10, "aria-label": "Editable negotiation message draft" }), notice && _jsx("p", { className: "draft-notice", role: "status", children: notice }), _jsxs("div", { className: "composer-bottom", children: [_jsxs("span", { className: "human-review-note", children: [_jsx("span", {}), " Suggestion only \u00B7 Review and edit before external use"] }), _jsxs("div", { className: "composer-actions", children: [_jsxs("button", { className: "neg-button neg-button-quiet", onClick: reset, disabled: !draft, children: [_jsx(RotateCcw, { size: 14 }), " Reset"] }), _jsxs("button", { className: "neg-button neg-button-quiet", onClick: copy, disabled: !draft, children: [copied ? _jsx(Check, { size: 14 }) : _jsx(Clipboard, { size: 14 }), " ", copied ? 'Copied' : 'Copy draft'] }), _jsxs("button", { className: "neg-button neg-button-primary", onClick: generate, disabled: loading, children: [loading ? _jsx(LoaderCircle, { className: "spin", size: 14 }) : draft ? _jsx(RefreshCw, { size: 14 }) : _jsx(Sparkles, { size: 14 }), " ", loading ? 'Preparing…' : draft ? 'Regenerate draft' : 'Generate draft'] })] })] })] })] });
}
