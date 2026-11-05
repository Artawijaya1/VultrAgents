import { create } from 'zustand';

// Discard legacy browser-only demo records from earlier versions of this app.
try {
  ['procuremind-demo-procurement-v1', 'procuremind-demo-fraud-alerts-v1', 'procuremind-audit-logs-v1'].forEach(key => window.localStorage.removeItem(key));
} catch { /* Browser storage may be unavailable. */ }

// This store intentionally starts empty. Procurement records are loaded from Backend.
export const useProcurementStore = create((set) => ({
  suppliers: [],
  purchaseOrders: [],
  invoices: [],
  contracts: [],
  audit: [],
  selectedSupplierId: null,
  selectedPurchaseOrderId: null,
  selectedInvoiceId: null,
  selectedContractId: null,
  recordsLoading: false,
  recordsError: '',
  setRecordsLoading: (recordsLoading) => set({ recordsLoading }),
  setRecordsError: (recordsError) => set({ recordsError }),
  setRecords: (records) => set({ ...records, recordsError: '' }),
  selectContext: (supplierId, purchaseOrderId) => set({ selectedSupplierId: supplierId, selectedPurchaseOrderId: purchaseOrderId }),
  selectInvoice: (invoiceId) => set({ selectedInvoiceId: invoiceId }),
  selectContract: (contractId) => set({ selectedContractId: contractId }),
  updateSupplierStatus: () => {},
  updateOrderStatus: () => {},
  updateInvoiceStatus: () => {},
}));
