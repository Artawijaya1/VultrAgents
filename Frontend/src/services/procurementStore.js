import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import { negotiationPurchaseOrders, negotiationSuppliers } from '../data/negotiationData';
const supplierMeta = {
    'SUP-0018': { email: 'procurement@globalsupply.example', phone: '+62 21 5550 0180', location: 'Jakarta, Indonesia', status: 'Active', spendYtd: 186400, risk: 'Low' },
    'SUP-0024': { email: 'account.team@mitratech.example', phone: '+62 22 5550 0240', location: 'Bandung, Indonesia', status: 'Active', spendYtd: 294800, risk: 'Medium' },
    'SUP-0031': { email: 'ops@sumberlogistik.example', phone: '+62 31 5550 0310', location: 'Surabaya, Indonesia', status: 'Active', spendYtd: 97200, risk: 'Low' },
    'SUP-0042': { email: 'sales@primaindustrial.example', phone: '+62 21 5550 0420', location: 'Jakarta, Indonesia', status: 'Active', spendYtd: 338500, risk: 'Low' },
    'SUP-0056': { email: 'finance@nusantaracomponents.example', phone: '+62 21 5550 0560', location: 'Tangerang, Indonesia', status: 'Under Review', spendYtd: 142700, risk: 'High' },
};
const seedSuppliers = negotiationSuppliers.map(supplier => ({ ...supplier, ...supplierMeta[supplier.id] }));
const seedOrders = negotiationPurchaseOrders.map((order, index) => ({ ...order, requester: ['Jordan Davis', 'Maya Chen', 'Rizky Pratama', 'Jordan Davis', 'Ava Patel'][index], createdDate: ['2026-11-02', '2026-10-29', '2026-10-26', '2026-10-23', '2026-10-19'][index], status: ['Pending Approval', 'Approved', 'In Progress', 'Pending Approval', 'Under Review'][index] }));
const seedContracts = Array.from(new Map(seedOrders.map(order => [order.contractId, order])).values()).map(order => ({ id: order.contractId, supplierId: order.supplierId, title: `${order.category} Supply Agreement`, category: order.category, startDate: order.contractValidThrough.startsWith('2027') ? '2025-04-01' : '2025-01-01', endDate: order.contractValidThrough, value: Math.round(order.contractUnitPrice * order.quantity * 5), currency: 'USD', status: (order.contractValidThrough < '2026-11-04' ? 'Expired' : order.contractValidThrough <= '2026-12-31' ? 'Expiring Soon' : 'Active'), owner: 'Jordan Davis', purchaseOrderIds: seedOrders.filter(item => item.contractId === order.contractId).map(item => item.id) }));
const seedInvoices = [
    { id: 'INV-2026-0842', supplierId: 'SUP-0018', purchaseOrderId: 'PO-2026-00142', contractId: 'CTR-2025-0184', issueDate: '2026-11-04', dueDate: '2026-12-04', amount: 148500, currency: 'USD', status: 'Under Review', description: 'Precision steel fasteners · delivery 01' },
    { id: 'INV-2026-0819', supplierId: 'SUP-0024', purchaseOrderId: 'PO-2026-00138', contractId: 'CTR-2025-0227', issueDate: '2026-11-03', dueDate: '2026-12-18', amount: 226800, currency: 'USD', status: 'Flagged', description: 'Enterprise network switches · phase 2' },
    { id: 'INV-2026-0771', supplierId: 'SUP-0042', purchaseOrderId: 'PO-2026-00119', contractId: 'CTR-2024-0316', issueDate: '2026-11-02', dueDate: '2027-01-01', amount: 184000, currency: 'USD', status: 'Under Review', description: 'Hydraulic pump assembly · lot A' },
    { id: 'INV-2026-0739', supplierId: 'SUP-0056', purchaseOrderId: 'PO-2026-00115', contractId: 'CTR-2025-0261', issueDate: '2026-11-01', dueDate: '2026-12-16', amount: 92750, currency: 'USD', status: 'Pending Match', description: 'Sensor control modules · batch 06' },
    { id: 'INV-2026-0694', supplierId: 'SUP-0031', purchaseOrderId: 'PO-2026-00125', contractId: 'CTR-2025-0091', issueDate: '2026-10-29', dueDate: '2026-11-28', amount: 58600, currency: 'USD', status: 'Matched', description: 'Reinforced shipping cartons · monthly replenishment' },
];
const addAudit = (audit, entityId, action) => [{ id: `AUD-${Date.now()}`, date: new Date().toISOString(), actor: 'Jordan Davis', action, entityId }, ...audit];
export const useProcurementStore = create()(persist((set) => ({
    suppliers: seedSuppliers,
    purchaseOrders: seedOrders,
    invoices: seedInvoices,
    contracts: seedContracts,
    audit: [],
    selectedSupplierId: seedSuppliers[0].id,
    selectedPurchaseOrderId: seedOrders[0].id,
    selectedInvoiceId: null,
    selectedContractId: null,
    selectContext: (supplierId, purchaseOrderId) => set({ selectedSupplierId: supplierId, selectedPurchaseOrderId: purchaseOrderId }),
    selectInvoice: (invoiceId) => set({ selectedInvoiceId: invoiceId }),
    selectContract: (contractId) => set({ selectedContractId: contractId }),
    updateSupplierStatus: (id, status, action) => set(state => ({ suppliers: state.suppliers.map(item => item.id === id ? { ...item, status } : item), audit: addAudit(state.audit, id, action) })),
    updateOrderStatus: (id, status, action) => set(state => ({ purchaseOrders: state.purchaseOrders.map(item => item.id === id ? { ...item, status } : item), audit: addAudit(state.audit, id, action) })),
    updateInvoiceStatus: (id, status, action) => set(state => ({ invoices: state.invoices.map(item => item.id === id ? { ...item, status } : item), audit: addAudit(state.audit, id, action) })),
}), { name: 'procuremind-demo-procurement-v1', storage: createJSONStorage(() => localStorage) }));
