"""Synthetic fixtures only. Replace with role-filtered SQL repositories.

DO NOT put banking credentials, personal customer data, or live supplier
correspondence in these fixtures.
"""
from copy import deepcopy

SUPPLIERS = [
    {"id": 1, "name": "PT Sinar Logistik", "active": True, "bank_fingerprint": "verified:sup1:v1"},
    {"id": 2, "name": "CV Mitra Niaga", "active": True, "bank_fingerprint": "verified:sup2:v1"},
]
PURCHASE_ORDERS = [
    {"id": 1, "number": "PO-001", "supplier_id": 1, "product_id": 101,
     "quantity": 100, "unit_price": "150000", "contract_max_unit_price": "155000",
     "historical_median_price": "145000", "target_unit_price": "140000",
     "required_delivery_days": 7, "quoted_delivery_days": 12},
]
INVOICES = [
    {"id": 1, "supplier_id": 1, "invoice_number": "INV-100", "po_number": "PO-001",
     "product_id": 101, "quantity": 100, "unit_price": "150000", "total_amount": "15000000",
     "invoice_date": "2026-10-30", "verified_bank_fingerprint": "verified:sup1:v1",
     "payment_bank_fingerprint": "verified:sup1:v1"},
    {"id": 2, "supplier_id": 1, "invoice_number": "INV-100", "po_number": "PO-001",
     "product_id": 101, "quantity": 100, "unit_price": "150000", "total_amount": "15000000",
     "invoice_date": "2026-10-31", "verified_bank_fingerprint": "verified:sup1:v1",
     "payment_bank_fingerprint": "new-unverified:sup1:v2"},
    {"id": 3, "supplier_id": 2, "invoice_number": "INV-201", "po_number": "PO-002",
     "product_id": 102, "quantity": 10, "unit_price": "400000", "total_amount": "4000000",
     "invoice_date": "2026-10-29", "verified_bank_fingerprint": "verified:sup2:v1",
     "payment_bank_fingerprint": "verified:sup2:v1"},
]
PRICE_HISTORY = [{"supplier_id": 1, "product_id": 101, "median_unit_price": "100000"}]
APPROVALS = [{"id": "APR-001", "entity_type": "negotiation_offer", "entity_id": "OFF-001", "status": "pending"}]

def get_po(number: str):
    return deepcopy(next((x for x in PURCHASE_ORDERS if x["number"] == number), None))

def get_invoices():
    return deepcopy(INVOICES)

def get_suppliers():
    return deepcopy(SUPPLIERS)

def get_approvals():
    return deepcopy(APPROVALS)

def get_price_history():
    return deepcopy(PRICE_HISTORY)
