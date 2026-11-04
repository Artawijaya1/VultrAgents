"""Data access contract. Replace MockProvider with a database/API adapter later."""
from copy import deepcopy
from typing import Protocol

class ProcurementProvider(Protocol):
    def get_po(self, po_id: str) -> dict | None: ...
    def get_supplier(self, supplier_id: str) -> dict | None: ...
    def get_invoices(self, supplier_id: str) -> list[dict]: ...

class MockProvider:
    def __init__(self):
        self.pos = {
            'PO-001': {
                'po_id': 'PO-001', 'supplier_id': 'SUP-001',
                'product_id': 'LAPTOP-01', 'quantity': 100,
                'offered_unit_price': 150000, 'budget_ceiling_unit': 135000,
                'previous_unit_price': 140000, 'currency': 'IDR',
                'required_delivery_date': '2026-11-20'
            }
        }
        self.suppliers = {
            'SUP-001': {'supplier_id': 'SUP-001', 'name': 'PT Contoh Pemasok',
                        'bank_last_changed_at': '2026-11-01'}
        }
        self.invoices = [
            {'record_id': 'REC-01', 'invoice_number': 'TAG-100',
             'supplier_id': 'SUP-001', 'po_id': 'PO-001', 'product_id': 'LAPTOP-01',
             'amount': 15000000, 'unit_price': 150000, 'invoice_date': '2026-11-02'},
            {'record_id': 'REC-02', 'invoice_number': 'TAG-100',
             'supplier_id': 'SUP-001', 'po_id': 'PO-001', 'product_id': 'LAPTOP-01',
             'amount': 15000000, 'unit_price': 150000, 'invoice_date': '2026-11-03'},
        ]

    def get_po(self, po_id: str) -> dict | None:
        row = self.pos.get(po_id)
        return deepcopy(row) if row else None

    def get_supplier(self, supplier_id: str) -> dict | None:
        row = self.suppliers.get(supplier_id)
        return deepcopy(row) if row else None

    def get_invoices(self, supplier_id: str) -> list[dict]:
        return deepcopy([i for i in self.invoices if i['supplier_id'] == supplier_id])
