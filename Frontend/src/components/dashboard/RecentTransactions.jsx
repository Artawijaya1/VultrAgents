import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useMemo, useState } from 'react';
import { ArrowDown, ArrowUp, ArrowUpDown, ChevronLeft, ChevronRight, ExternalLink, Search, SlidersHorizontal } from 'lucide-react';
import { transactions } from '../../data/mockData';
const statuses = ['All statuses', 'Approved', 'Pending', 'Under Review', 'Flagged'];
const formatAmount = (amount) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(amount);
export default function RecentTransactions({ search: globalSearch }) {
    const [search, setSearch] = useState('');
    const [status, setStatus] = useState('All statuses');
    const [sortKey, setSortKey] = useState('date');
    const [ascending, setAscending] = useState(false);
    const [page, setPage] = useState(1);
    const pageSize = 6;
    const filtered = useMemo(() => transactions.filter(row => {
        const query = `${search} ${globalSearch}`.trim().toLowerCase();
        const matchesQuery = !query || `${row.id} ${row.supplier} ${row.purchaseOrder} ${row.amount} ${row.status}`.toLowerCase().includes(query);
        return matchesQuery && (status === 'All statuses' || row.status === status);
    }).sort((a, b) => {
        const left = a[sortKey], right = b[sortKey];
        const comparison = typeof left === 'number' && typeof right === 'number' ? left - right : String(left).localeCompare(String(right));
        return ascending ? comparison : -comparison;
    }), [search, globalSearch, status, sortKey, ascending]);
    const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
    const currentPage = Math.min(page, pageCount);
    const currentRows = filtered.slice((currentPage - 1) * pageSize, currentPage * pageSize);
    const sort = (key) => { if (sortKey === key)
        setAscending(!ascending);
    else {
        setSortKey(key);
        setAscending(true);
    } setPage(1); };
    const heading = (label, key) => _jsxs("button", { className: "sort-heading", onClick: () => sort(key), children: [label, sortKey === key ? (ascending ? _jsx(ArrowUp, { size: 12 }) : _jsx(ArrowDown, { size: 12 })) : _jsx(ArrowUpDown, { size: 12 })] });
    return _jsxs("section", { className: "dashboard-section transactions-section", children: [_jsxs("div", { className: "dashboard-section-heading", children: [_jsxs("div", { children: [_jsx("h2", { children: "Recent transactions" }), _jsx("p", { children: "Review purchase activity across your organization" })] }), _jsxs("button", { className: "table-view-all", onClick: () => { setStatus('All statuses'); setSearch(''); setPage(1); }, children: ["Reset filters ", _jsx(ExternalLink, { size: 13 })] })] }), _jsxs("div", { className: "dashboard-panel transaction-panel", children: [_jsxs("div", { className: "transaction-toolbar", children: [_jsxs("label", { className: "transaction-search", children: [_jsx(Search, { size: 15 }), _jsx("input", { value: search, onChange: event => { setSearch(event.target.value); setPage(1); }, placeholder: "Search transactions...", "aria-label": "Search transactions" })] }), _jsxs("label", { className: "status-select", children: [_jsx(SlidersHorizontal, { size: 14 }), _jsx("select", { value: status, onChange: event => { setStatus(event.target.value); setPage(1); }, "aria-label": "Filter transactions by status", children: statuses.map(item => _jsx("option", { children: item }, item)) })] })] }), _jsxs("div", { className: "table-scroll", children: [_jsxs("table", { className: "transactions-table", children: [_jsx("thead", { children: _jsxs("tr", { children: [_jsx("th", { children: heading('Transaction ID', 'id') }), _jsx("th", { children: heading('Supplier', 'supplier') }), _jsx("th", { children: heading('Purchase order', 'purchaseOrder') }), _jsx("th", { children: heading('Amount', 'amount') }), _jsx("th", { children: heading('Date', 'date') }), _jsx("th", { children: heading('Status', 'status') }), _jsx("th", { children: _jsx("span", { className: "sr-only", children: "Action" }) })] }) }), _jsx("tbody", { children: currentRows.map(row => _jsxs("tr", { children: [_jsx("td", { className: "transaction-id", children: row.id }), _jsx("td", { children: _jsxs("span", { className: "supplier-cell", children: [_jsx("i", { children: row.supplier.slice(0, 1) }), row.supplier] }) }), _jsx("td", { className: "po-cell", children: row.purchaseOrder }), _jsx("td", { className: "amount-cell", children: formatAmount(row.amount) }), _jsx("td", { className: "date-cell", children: new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(`${row.date}T12:00:00`)) }), _jsx("td", { children: _jsxs("span", { className: `transaction-status status-${row.status.toLowerCase().replace(/ /g, '-')}`, children: [_jsx("i", {}), row.status] }) }), _jsx("td", { children: _jsx("button", { className: "row-action", "aria-label": `View ${row.id}`, title: `View ${row.id}`, onClick: () => window.alert(`${row.id}\n${row.supplier} · ${formatAmount(row.amount)}\nStatus: ${row.status}`), children: _jsx(ExternalLink, { size: 14 }) }) })] }, row.id)) })] }), currentRows.length === 0 && _jsx("div", { className: "table-empty", children: "No transactions match these filters." })] }), _jsxs("div", { className: "table-footer", children: [_jsxs("span", { children: ["Showing ", _jsxs("b", { children: [filtered.length ? ((currentPage - 1) * pageSize) + 1 : 0, "\u2013", Math.min(currentPage * pageSize, filtered.length)] }), " of ", _jsx("b", { children: filtered.length }), " transactions"] }), _jsxs("div", { className: "pagination", children: [_jsx("button", { disabled: currentPage === 1, onClick: () => setPage(Math.max(1, currentPage - 1)), "aria-label": "Previous page", children: _jsx(ChevronLeft, { size: 15 }) }), _jsxs("span", { children: ["Page ", currentPage, " of ", pageCount] }), _jsx("button", { disabled: currentPage >= pageCount, onClick: () => setPage(Math.min(pageCount, currentPage + 1)), "aria-label": "Next page", children: _jsx(ChevronRight, { size: 15 }) })] })] })] })] });
}
