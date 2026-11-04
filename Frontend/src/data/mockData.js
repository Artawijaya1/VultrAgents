export const monthlySpend = [
    { month: 'Jan', spend: 48 }, { month: 'Feb', spend: 64 }, { month: 'Mar', spend: 52 },
    { month: 'Apr', spend: 74 }, { month: 'May', spend: 58 }, { month: 'Jun', spend: 82 },
    { month: 'Jul', spend: 91 }, { month: 'Aug', spend: 68 }, { month: 'Sep', spend: 86 },
    { month: 'Oct', spend: 77 }, { month: 'Nov', spend: 98 }, { month: 'Dec', spend: 83 },
];
export const overviewData = [
    { month: 'Jan', spend: 35 }, { month: 'Feb', spend: 48 }, { month: 'Mar', spend: 42 },
    { month: 'Apr', spend: 61 }, { month: 'May', spend: 53 }, { month: 'Jun', spend: 72 },
];
export const features = [
    { icon: 'Handshake', title: 'AI Negotiation Copilot', text: 'Build confident supplier strategies from purchasing history, contract terms, price trends, and delivery performance.', items: ['Historical price analysis', 'Smarter negotiation strategies', 'Delivery optimization', 'AI communication drafts'] },
    { icon: 'ShieldAlert', title: 'Procurement Fraud Detection', text: 'Spot suspicious patterns and transaction anomalies early, with clear context to support transparent investigations.', items: ['Duplicate invoice detection', 'Unusual price monitoring', 'Transaction pattern analysis', 'Supplier risk monitoring'] },
];
export const procurementDashboard = {
    monthlySpending: [
        { month: 'Jan', spending: 182 }, { month: 'Feb', spending: 196 }, { month: 'Mar', spending: 174 },
        { month: 'Apr', spending: 228 }, { month: 'May', spending: 214 }, { month: 'Jun', spending: 246 },
        { month: 'Jul', spending: 221 }, { month: 'Aug', spending: 264 }, { month: 'Sep', spending: 238 },
        { month: 'Oct', spending: 279 }, { month: 'Nov', spending: 252 }, { month: 'Dec', spending: 301 },
    ],
    categories: [
        { name: 'Technology', value: 34, color: '#20b9f2' },
        { name: 'Operations', value: 26, color: '#168fd0' },
        { name: 'Facilities', value: 19, color: '#3375a5' },
        { name: 'Logistics', value: 13, color: '#5e7894' },
        { name: 'Other', value: 8, color: '#39495e' },
    ],
    supplierPerformance: [
        { supplier: 'Nexa Systems', score: 98 }, { supplier: 'Atlas Industrial', score: 94 },
        { supplier: 'BluePeak Logistics', score: 91 }, { supplier: 'Vertex Office Co.', score: 87 },
    ],
};
export const transactions = [
    { id: 'TXN-2026-0847', supplier: 'Nexa Systems', purchaseOrder: 'PO-48291', amount: 48250, date: '2026-11-04', status: 'Approved' },
    { id: 'TXN-2026-0846', supplier: 'Atlas Industrial', purchaseOrder: 'PO-48290', amount: 127800, date: '2026-11-04', status: 'Pending' },
    { id: 'TXN-2026-0845', supplier: 'BluePeak Logistics', purchaseOrder: 'PO-48286', amount: 18640, date: '2026-11-03', status: 'Under Review' },
    { id: 'TXN-2026-0844', supplier: 'Vertex Office Co.', purchaseOrder: 'PO-48281', amount: 9360, date: '2026-11-03', status: 'Approved' },
    { id: 'TXN-2026-0843', supplier: 'Meridian Cloud', purchaseOrder: 'PO-48277', amount: 68200, date: '2026-11-02', status: 'Flagged' },
    { id: 'TXN-2026-0842', supplier: 'Summit Components', purchaseOrder: 'PO-48273', amount: 32400, date: '2026-11-01', status: 'Approved' },
    { id: 'TXN-2026-0841', supplier: 'Nexa Systems', purchaseOrder: 'PO-48268', amount: 21800, date: '2026-10-31', status: 'Pending' },
    { id: 'TXN-2026-0840', supplier: 'Atlas Industrial', purchaseOrder: 'PO-48261', amount: 75890, date: '2026-10-30', status: 'Approved' },
    { id: 'TXN-2026-0839', supplier: 'Harborline Freight', purchaseOrder: 'PO-48258', amount: 14200, date: '2026-10-29', status: 'Under Review' },
    { id: 'TXN-2026-0838', supplier: 'Meridian Cloud', purchaseOrder: 'PO-48254', amount: 55200, date: '2026-10-28', status: 'Flagged' },
    { id: 'TXN-2026-0837', supplier: 'Vertex Office Co.', purchaseOrder: 'PO-48249', amount: 8700, date: '2026-10-27', status: 'Approved' },
    { id: 'TXN-2026-0836', supplier: 'BluePeak Logistics', purchaseOrder: 'PO-48242', amount: 41600, date: '2026-10-26', status: 'Pending' },
];
export const agentActivities = [
    { id: 'ACT-01', agent: 'Negotiation Copilot', module: 'negotiation', icon: 'Handshake', description: 'Price benchmark is ready for review', related: 'Nexa Systems · PO-48291', timestamp: '8 min ago', status: 'Pending Review' },
    { id: 'ACT-02', agent: 'Fraud Detection', module: 'fraud-detection', icon: 'ShieldAlert', description: 'Duplicate invoice pattern identified', related: 'Meridian Cloud · INV-19042', timestamp: '24 min ago', status: 'Investigation' },
    { id: 'ACT-03', agent: 'Negotiation Copilot', module: 'negotiation', icon: 'Handshake', description: 'Supplier delivery analysis completed', related: 'Atlas Industrial · PO-48290', timestamp: '1 hr ago', status: 'Completed' },
    { id: 'ACT-04', agent: 'Fraud Detection', module: 'fraud-detection', icon: 'ShieldAlert', description: 'Unusual payment change requires attention', related: 'BluePeak Logistics · INV-19018', timestamp: '2 hrs ago', status: 'High Risk' },
];
