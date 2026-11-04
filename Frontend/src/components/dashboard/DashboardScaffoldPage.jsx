import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Link, useOutletContext, useParams } from 'react-router-dom';
import { ArrowRight, FileSearch, Settings2, ShieldCheck, Users } from 'lucide-react';
const pages = {
    'purchase-orders': { title: 'Purchase Orders', description: 'Track purchase requests and order progress across the organization.', icon: FileSearch },
    suppliers: { title: 'Suppliers', description: 'Review supplier records, performance, and relationship details.', icon: Users },
    invoices: { title: 'Invoices & Contracts', description: 'A consolidated workspace for invoice and contract review.', icon: FileSearch },
    'audit-logs': { title: 'Audit Logs', description: 'A clear view of procurement actions and review history.', icon: ShieldCheck },
    settings: { title: 'Workspace Settings', description: 'Manage workspace preferences and team configuration.', icon: Settings2 },
};
export default function DashboardScaffoldPage() {
    const { section } = useParams();
    const { search } = useOutletContext();
    const page = section ? pages[section] : undefined;
    if (!page)
        return null;
    const Icon = page.icon;
    return _jsxs("div", { className: "dashboard-scaffold", children: [_jsxs("div", { className: "dashboard-eyebrow", children: [_jsx("span", { className: "live-dot" }), " PROCUREMENT WORKSPACE"] }), _jsxs("div", { className: "scaffold-title", children: [_jsxs("span", { children: [_jsx("h1", { children: page.title }), _jsx("p", { children: page.description })] }), _jsx("span", { className: "scaffold-icon", children: _jsx(Icon, { size: 22 }) })] }), _jsxs("div", { className: "scaffold-placeholder", children: [_jsx("span", { className: "scaffold-placeholder-icon", children: _jsx(Icon, { size: 22 }) }), _jsxs("h2", { children: [page.title, " workspace"] }), _jsx("p", { children: "This section is prepared for the next product phase. No live procurement records are connected yet." }), search && _jsxs("small", { children: ["Dashboard search: \u201C", search, "\u201D"] }), _jsxs(Link, { className: "dashboard-text-link", to: "/dashboard", children: ["Return to overview ", _jsx(ArrowRight, { size: 14 })] })] })] });
}
