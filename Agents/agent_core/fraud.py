"""Transparent anomaly flags, not a fraud verdict."""
from collections import defaultdict
from datetime import date
from decimal import Decimal
from .data_provider import ProcurementProvider


def analyze_supplier(provider: ProcurementProvider, supplier_id: str) -> dict:
    supplier = provider.get_supplier(supplier_id)
    if supplier is None:
        return {'status': 'not_found', 'supplier_id': supplier_id, 'error': 'Supplier tidak ditemukan'}
    invoices = provider.get_invoices(supplier_id)
    findings: list[dict] = []
    seen = defaultdict(list)
    for inv in invoices:
        seen[(inv['supplier_id'], inv['invoice_number'])].append(inv)
    for (supplier_key, number), matches in seen.items():
        if len({x['record_id'] for x in matches}) > 1:
            findings.append({
                'rule_id': 'DUPLICATE_INVOICE', 'severity': 'high',
                'description': f'Nomor invoice {number} tercatat lebih dari sekali',
                'evidence_record_ids': [x['record_id'] for x in matches],
                'next_action': 'Verifikasi dokumen dan status pembayaran secara manual'
            })
    for inv in invoices:
        po = provider.get_po(inv['po_id'])
        if po and inv.get('unit_price') is not None:
            baseline = Decimal(str(po['previous_unit_price']))
            current = Decimal(str(inv['unit_price']))
            if baseline > 0 and current > baseline * Decimal('1.25'):
                findings.append({
                    'rule_id': 'PRICE_ANOMALY', 'severity': 'medium',
                    'description': 'Harga invoice melampaui 125% harga historis',
                    'evidence_record_ids': [inv['record_id']],
                    'next_action': 'Periksa alasan kenaikan harga dan kontrak'
                })
        changed = supplier.get('bank_last_changed_at')
        if changed:
            try:
                delta = (date.fromisoformat(inv['invoice_date']) - date.fromisoformat(changed)).days
                if 0 <= delta <= 7:
                    findings.append({
                        'rule_id': 'RECENT_BANK_CHANGE', 'severity': 'high',
                        'description': 'Ada perubahan rekening dalam 7 hari sebelum tanggal invoice',
                        'evidence_record_ids': [inv['record_id']],
                        'next_action': 'Konfirmasi perubahan rekening melalui kanal independen'
                    })
            except ValueError:
                findings.append({'rule_id':'INVALID_DATE','severity':'low',
                    'description':'Tanggal transaksi tidak dapat dibaca',
                    'evidence_record_ids':[inv['record_id']],
                    'next_action':'Periksa kualitas data'})
    # A finding is a lead for review, never proof of fraud.
    return {
        'status': 'review_required' if findings else 'no_flags',
        'agent': 'fraud', 'supplier_id': supplier_id,
        'invoice_count': len(invoices), 'findings': findings,
        'flag_count': len(findings), 'is_fraud_confirmed': False,
        'requires_human_review': bool(findings),
        'disclaimer': 'Indikator anomali, bukan bukti atau vonis penipuan.'
    }
