"""Read-only PO-scoped procurement anomaly analysis.

Reuses supplier-level fraud rules while returning only findings involving
invoice records tied to the requested PO. A duplicate involving a second PO
may still include that related evidence record ID for human review.
"""
from .data_provider import ProcurementProvider
from .fraud import analyze_supplier


def analyze_purchase_order(provider: ProcurementProvider, po_id: str) -> dict:
    po = provider.get_po(po_id)
    if po is None:
        return {
            'status': 'not_found', 'agent': 'fraud', 'scope': 'purchase_order',
            'po_id': po_id, 'error': 'Purchase order not found.',
            'is_fraud_confirmed': False,
        }

    supplier_id = po['supplier_id']
    all_supplier_invoices = provider.get_invoices(supplier_id)
    target_invoices = [i for i in all_supplier_invoices if i.get('po_id') == po_id]
    target_ids = {i['record_id'] for i in target_invoices}

    if not target_invoices:
        return {
            'status': 'no_invoices', 'agent': 'fraud', 'scope': 'purchase_order',
            'po_id': po_id, 'supplier_id': supplier_id, 'invoice_count': 0,
            'findings': [], 'flag_count': 0, 'is_fraud_confirmed': False,
            'requires_human_review': False,
            'disclaimer': 'There are no invoices to review; this does not prove that there is no risk.',
        }

    supplier_scan = analyze_supplier(provider, supplier_id)
    if supplier_scan['status'] == 'not_found':
        return {
            'status': 'invalid_reference', 'agent': 'fraud', 'scope': 'purchase_order',
            'po_id': po_id, 'supplier_id': supplier_id,
            'error': 'The supplier associated with the purchase order was not found.',
            'is_fraud_confirmed': False,
        }

    # Include a finding only if at least one evidence record belongs to this PO.
    # A cross-PO duplicate remains visible if it concerns a target invoice.
    findings = [
        finding for finding in supplier_scan['findings']
        if target_ids.intersection(finding.get('evidence_record_ids', []))
    ]
    return {
        'status': 'review_required' if findings else 'no_flags',
        'agent': 'fraud', 'scope': 'purchase_order',
        'po_id': po_id, 'supplier_id': supplier_id,
        'invoice_count': len(target_invoices),
        'findings': findings, 'flag_count': len(findings),
        'is_fraud_confirmed': False,
        'requires_human_review': bool(findings),
        'disclaimer': 'Anomaly indicators are not proof or a determination of fraud.',
    }
