import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Activity, CircleDollarSign, ShieldAlert, Users } from 'lucide-react';
const rupiah = new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 });
export default function RiskOverviewCards({ overview, suspiciousCount, exposure }) {
    const cards = [
        { label: 'Transactions analyzed', value: overview.transactionsAnalyzed.toLocaleString('en-US'), description: 'Across the monitored period', icon: Activity, trend: '+12.4%', accent: 'cyan' },
        { label: 'Suspicious transactions', value: suspiciousCount.toLocaleString('en-US'), description: 'Potential anomalies for review', icon: ShieldAlert, trend: '8 need review', accent: 'amber' },
        { label: 'High-risk suppliers', value: String(overview.highRiskSuppliers), description: 'Suppliers with open risk indicators', icon: Users, trend: 'Across 4 categories', accent: 'orange' },
        { label: 'Potential financial exposure', value: rupiah.format(exposure), description: 'Estimated value for investigation', icon: CircleDollarSign, trend: 'Demo estimate', accent: 'blue' },
    ];
    return _jsx("section", { className: "fraud-kpi-grid", "aria-label": "Fraud detection overview", children: cards.map(card => _jsxs("article", { className: `fraud-kpi-card accent-${card.accent}`, children: [_jsxs("div", { className: "fraud-kpi-head", children: [_jsx("span", { children: card.label }), _jsx("i", { children: _jsx(card.icon, { size: 17 }) })] }), _jsx("strong", { children: card.value }), _jsxs("div", { className: "fraud-kpi-foot", children: [_jsx("span", { children: card.description }), _jsx("b", { children: card.trend })] }), _jsx("span", { className: "kpi-glimmer" })] }, card.label)) });
}
