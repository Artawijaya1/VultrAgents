import { getContracts as apiGetContracts, getInvoices as apiGetInvoices, getPurchaseOrders as apiGetPurchaseOrders, getVendors as apiGetVendors } from './api';

const rows = (response, key) => Array.isArray(response) ? response : response?.items ?? response?.[key] ?? [];
const day = (value) => value ? String(value).slice(0, 10) : '';

function normalizeOrder(raw) {
  return {
    id: raw.po_id ?? raw.id,
    supplierId: raw.supplier_id,
    supplierName: raw.supplier_name ?? '',
    productName: raw.product_name ?? raw.product_id ?? '',
    category: raw.category ?? '',
    quantity: Number(raw.quantity ?? 0),
    unit: raw.unit ?? '',
    currentOffer: Number(raw.offered_unit_price ?? 0),
    targetPrice: Number(raw.budget_ceiling_unit ?? 0),
    historicalPrice: Number(raw.previous_unit_price ?? 0),
    contractUnitPrice: null,
    contractId: null,
    createdDate: day(raw.created_at),
    requiredDeliveryDate: day(raw.required_delivery_date),
    status: raw.status ?? 'Unknown',
    requester: raw.requester ?? '',
    offeredDeliveryDate: '',
    preferredDeliveryDate: day(raw.required_delivery_date),
    paymentTerms: '',
    deliveryTerms: '',
    minimumOrderQuantity: null,
    priceHistory: [],
    deliveryHistory: [],
    currency: raw.currency ?? '',
  };
}

function normalizeSupplier(raw) {
  return {
    id: raw.supplier_id ?? raw.id,
    name: raw.name ?? '',
    category: raw.category ?? '',
    location: raw.location ?? '',
    email: raw.email ?? '',
    phone: raw.phone ?? '',
    rating: raw.rating == null ? null : Number(raw.rating),
    onTimeRate: raw.on_time_rate == null ? null : Number(raw.on_time_rate),
    averageDeliveryDays: raw.metrics?.average_delivery_days ?? null,
    spendYtd: null,
    status: raw.status ?? 'Unknown',
    risk: raw.risk ?? 'Unknown',
    bankLastChangedAt: raw.bank_last_changed_at ?? null,
    purchaseOrderCount: Number(raw.purchase_order_count ?? 0),
  };
}

function normalizeInvoice(raw) {
  return {
    id: raw.record_id ?? raw.id,
    invoiceNumber: raw.invoice_number ?? '',
    supplierId: raw.supplier_id,
    supplierName: raw.supplier_name ?? '',
    purchaseOrderId: raw.po_id ?? raw.purchase_order_id,
    contractId: null,
    issueDate: day(raw.invoice_date),
    dueDate: '',
    amount: Number(raw.amount ?? 0),
    unitPrice: Number(raw.unit_price ?? 0),
    currency: raw.currency ?? '',
    status: raw.status ?? null,
    description: raw.product_id ?? '',
  };
}

export const getPurchaseOrders = async () => rows(await apiGetPurchaseOrders(), 'purchase_orders').map(normalizeOrder);
export const getSuppliers = async () => rows(await apiGetVendors(), 'vendors').map(normalizeSupplier);
export const getInvoices = async () => rows(await apiGetInvoices(), 'invoices').map(normalizeInvoice);
export const getContracts = async () => rows(await apiGetContracts(), 'contracts');
