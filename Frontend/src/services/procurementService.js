import {
  ApiError,
  getContracts as apiGetContracts,
  getInvoices as apiGetInvoices,
  getPurchaseOrders as apiGetPurchaseOrders,
  getVendors as apiGetVendors,
} from './api';
import { useProcurementStore } from './procurementStore';

const delay = (ms) => new Promise(resolve => window.setTimeout(resolve, ms));

// ── Mock adapter (reads from local procurement store) ────────────────
const mockAdapter = {
  async getPurchaseOrders() {
    await delay(100);
    return useProcurementStore.getState().purchaseOrders;
  },
  async getSuppliers() {
    await delay(100);
    return useProcurementStore.getState().suppliers;
  },
  async getInvoices() {
    await delay(100);
    return useProcurementStore.getState().invoices;
  },
  async getContracts() {
    await delay(100);
    return useProcurementStore.getState().contracts;
  },
};

// ── Normalizers for live responses ──────────────────────────────────
function normalizeOrder(raw) {
  return {
    id: raw.id ?? raw.po_id ?? raw.purchase_order_id ?? 'PO-UNKNOWN',
    supplierId: raw.supplier_id ?? raw.supplierId ?? '',
    productName: raw.product_name ?? raw.productName ?? raw.description ?? 'Procurement Item',
    category: raw.category ?? 'General',
    quantity: Number(raw.quantity ?? 1),
    unit: raw.unit ?? 'units',
    currentOffer: Number(raw.current_offer ?? raw.offered_unit_price ?? raw.unit_price ?? 0),
    targetPrice: Number(raw.target_price ?? raw.budget_ceiling_unit ?? 0),
    historicalPrice: Number(raw.historical_price ?? raw.previous_unit_price ?? 0),
    contractUnitPrice: Number(raw.contract_unit_price ?? 0),
    contractId: raw.contract_id ?? raw.contractId ?? '',
    createdDate: (raw.created_at ?? raw.createdDate ?? new Date().toISOString()).slice(0, 10),
    status: raw.status ?? 'Pending Approval',
    requester: raw.requester ?? 'Procurement Team',
    offeredDeliveryDate: raw.offered_delivery_date ?? raw.offeredDeliveryDate ?? '',
    preferredDeliveryDate: raw.preferred_delivery_date ?? raw.preferredDeliveryDate ?? '',
    paymentTerms: raw.payment_terms ?? raw.paymentTerms ?? 'Net 30 days',
    deliveryTerms: raw.delivery_terms ?? raw.deliveryTerms ?? 'Standard delivery',
    minimumOrderQuantity: Number(raw.minimum_order_quantity ?? raw.minimumOrderQuantity ?? 1),
    priceHistory: Array.isArray(raw.price_history ?? raw.priceHistory) ? (raw.price_history ?? raw.priceHistory) : [],
    deliveryHistory: Array.isArray(raw.delivery_history ?? raw.deliveryHistory) ? (raw.delivery_history ?? raw.deliveryHistory) : [],
  };
}

function normalizeSupplier(raw) {
  return {
    id: raw.id ?? raw.supplier_id ?? raw.vendor_id ?? 'SUP-UNKNOWN',
    name: raw.name ?? raw.supplier_name ?? raw.vendor_name ?? 'Unknown Supplier',
    category: raw.category ?? 'General',
    location: raw.location ?? '—',
    rating: Number(raw.rating ?? 4.0),
    spendYtd: Number(raw.spend_ytd ?? raw.spendYtd ?? 0),
    risk: raw.risk ?? 'Low',
    status: raw.status ?? 'Active',
    email: raw.email ?? '',
    phone: raw.phone ?? '',
    averageDeliveryDays: Number(raw.average_delivery_days ?? raw.averageDeliveryDays ?? 14),
    onTimeRate: Number(raw.on_time_rate ?? raw.onTimeRate ?? 90),
    previousOrders: Number(raw.previous_orders ?? raw.previousOrders ?? 0),
  };
}

function normalizeInvoice(raw) {
  return {
    id: raw.id ?? raw.invoice_id ?? raw.invoice_number ?? 'INV-UNKNOWN',
    supplierId: raw.supplier_id ?? raw.supplierId ?? '',
    purchaseOrderId: raw.purchase_order_id ?? raw.purchaseOrderId ?? raw.po_id ?? '',
    contractId: raw.contract_id ?? raw.contractId ?? '',
    issueDate: (raw.issue_date ?? raw.issueDate ?? raw.invoice_date ?? new Date().toISOString()).slice(0, 10),
    dueDate: (raw.due_date ?? raw.dueDate ?? new Date().toISOString()).slice(0, 10),
    amount: Number(raw.amount ?? 0),
    currency: raw.currency ?? 'USD',
    status: raw.status ?? 'Under Review',
    description: raw.description ?? raw.item_description ?? 'Procurement invoice',
  };
}

function normalizeContract(raw) {
  return {
    id: raw.id ?? raw.contract_id ?? 'CTR-UNKNOWN',
    supplierId: raw.supplier_id ?? raw.supplierId ?? '',
    title: raw.title ?? raw.contract_title ?? 'Supply Agreement',
    category: raw.category ?? 'General',
    startDate: (raw.start_date ?? raw.startDate ?? new Date().toISOString()).slice(0, 10),
    endDate: (raw.end_date ?? raw.endDate ?? raw.valid_through ?? new Date().toISOString()).slice(0, 10),
    value: Number(raw.value ?? raw.contract_value ?? 0),
    currency: raw.currency ?? 'USD',
    status: raw.status ?? 'Active',
    owner: raw.owner ?? 'Procurement Officer',
    purchaseOrderIds: Array.isArray(raw.purchase_order_ids ?? raw.purchaseOrderIds) ? (raw.purchase_order_ids ?? raw.purchaseOrderIds) : [],
  };
}

// ── Live adapter (Backend endpoints, currently return 501) ───────────
const liveAdapter = {
  async getPurchaseOrders() {
    const raw = await apiGetPurchaseOrders();
    const list = Array.isArray(raw) ? raw : (raw.items ?? raw.purchase_orders ?? []);
    return list.map(normalizeOrder);
  },
  async getSuppliers() {
    const raw = await apiGetVendors();
    const list = Array.isArray(raw) ? raw : (raw.items ?? raw.vendors ?? []);
    return list.map(normalizeSupplier);
  },
  async getInvoices() {
    const raw = await apiGetInvoices();
    const list = Array.isArray(raw) ? raw : (raw.items ?? raw.invoices ?? []);
    return list.map(normalizeInvoice);
  },
  async getContracts() {
    const raw = await apiGetContracts();
    const list = Array.isArray(raw) ? raw : (raw.items ?? raw.contracts ?? []);
    return list.map(normalizeContract);
  },
};

// ── Mode selection ──────────────────────────────────────────────────
const procurementMode = import.meta.env.VITE_PROCUREMENT_MODE || 'mock';
export const isProcurementMockMode = () => procurementMode === 'mock';

function getAdapter(forceMock = false) {
  if (forceMock || procurementMode === 'mock') return mockAdapter;
  return liveAdapter;
}

// ── Exported API ────────────────────────────────────────────────────
export async function getPurchaseOrders(forceMock = false) {
  return getAdapter(forceMock).getPurchaseOrders();
}

export async function getSuppliers(forceMock = false) {
  return getAdapter(forceMock).getSuppliers();
}

export async function getInvoices(forceMock = false) {
  return getAdapter(forceMock).getInvoices();
}

export async function getContracts(forceMock = false) {
  return getAdapter(forceMock).getContracts();
}

export { ApiError };
