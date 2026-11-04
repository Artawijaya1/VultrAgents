# MCP Contracts (rancangan tahap awal)

## Aktif di prototipe
| MCP tool | Input | Output | Mode |
|---|---|---|---|
| `get_purchase_order` | `po_number: str` | Data PO / error | Demo read-only |
| `list_suppliers` | - | Supplier sintetis | Demo read-only |
| `draft_negotiation` | `po_number: str` | Counteroffer + alasan + draf | Demo read-only |
| `scan_procurement_anomalies` | - | Findings + severity + ringkasan | Demo read-only |
| `get_approval_status` | `approval_id: str` | Status persetujuan | Demo read-only |

MCP resource: `procurement://policies/default`.
MCP prompt: `prepare_negotiation(po_number)`.

## Tahap produksi / belum diimplementasikan
- `get_contract_terms(contract_id)`
- `get_supplier_price_history(supplier_id, product_id)`
- `compare_supplier_offers(offer_ids)`
- `create_negotiation_session(po_id)` (memerlukan autentikasi)
- `record_supplier_counteroffer(session_id, offer)` (memerlukan autentikasi)
- `validate_invoice_against_po(invoice_id)`
- `review_bank_change(change_id)` (human, verifikasi independen)
- `open_fraud_case(alert_id)` (human triage)
- `request_approval(entity_type, entity_id)` (human authenticated)
- `approve_negotiation(approval_id)` (approver yang berbeda)
- `send_approved_email(approval_id)` (hanya setelah persetujuan sah)

Semua tool produksi wajib: schema input ketat, tenant scoping, otorisasi per tindakan, idempotency key untuk writes, audit log, error terstruktur dan pembatasan data sensitif.
