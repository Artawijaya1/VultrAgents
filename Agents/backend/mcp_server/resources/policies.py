import json

def procurement_policy() -> str:
    return json.dumps({
        "version": "demo-1",
        "approval_rule": "Semua penawaran, komitmen, dan perubahan PO memerlukan persetujuan manusia",
        "fraud_rule": "Bendera risiko adalah indikator, bukan vonis pelanggaran",
        "invoice_review_threshold_idr": 5000000,
        "no_automatic_external_actions": True,
    }, ensure_ascii=False)
