import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Boxes } from 'lucide-react';
import { Link } from 'react-router-dom';
export default function Logo() {
    return _jsxs(Link, { className: "brand", to: "/", "aria-label": "ProcureMind AI home", children: [_jsx("span", { className: "brand-mark", children: _jsx(Boxes, { size: 19, strokeWidth: 1.7 }) }), _jsxs("span", { className: "brand-name", children: ["PROCUREMIND", _jsx("span", { children: " AI" })] })] });
}
