"""Explainable fraud *indicators*, never a conclusion of guilt.

Severity and thresholds are illustrative, not regulatory or statistical facts.
"""
from collections import defaultdict
from datetime import date
from decimal import Decimal

def _number(v) -> Decimal:
    return Decimal(str(v))

def scan_invoices(invoices: list[dict], price_history: list[dict], *,
                  price_spike_ratio: Decimal = Decimal("0.25"),
                  split_threshold: Decimal = Decimal("5000000"),
                  split_window_days: int = 7) -> list[dict]:
    findings = []
    seen = defaultdict(list)
    baseline = {(p["supplier_id"], p["product_id"]): _number(p["median_unit_price"])
                for p in price_history}
    for invoice in invoices:
        key = (invoice["supplier_id"], invoice["invoice_number"].strip().upper())
        for prior in seen[key]:
            findings.append({
                "code": "DUPLICATE_INVOICE_NUMBER", "severity": "high",
                "invoice_ids": [prior["id"], invoice["id"]],
                "reason": "Nomor invoice berulang pada supplier yang sama; perlu verifikasi dokumen",
            })
        seen[key].append(invoice)
        normal = baseline.get((invoice["supplier_id"], invoice["product_id"]))
        current = _number(invoice["unit_price"])
        if normal is not None and normal > 0 and current > normal * (1 + price_spike_ratio):
            findings.append({
                "code": "PRICE_SPIKE", "severity": "medium",
                "invoice_ids": [invoice["id"]],
                "reason": f"Harga {current} melampaui median {normal} lebih dari {price_spike_ratio * 100}%",
            })
        original_bank = invoice.get("verified_bank_fingerprint")
        payment_bank = invoice.get("payment_bank_fingerprint")
        if original_bank and payment_bank and original_bank != payment_bank:
            findings.append({
                "code": "BANK_CHANGE_REVIEW", "severity": "critical",
                "invoice_ids": [invoice["id"]],
                "reason": "Identitas rekening pembayaran berbeda dari rekening terverifikasi",
            })
    # Possible order-splitting needs same supplier and period, not proof of collusion.
    by_supplier = defaultdict(list)
    for inv in invoices:
        try:
            inv_date = date.fromisoformat(inv["invoice_date"])
        except (KeyError, ValueError):
            continue
        if _number(inv["total_amount"]) < split_threshold:
            by_supplier[inv["supplier_id"]].append((inv_date, inv))
    for supplier_id, rows in by_supplier.items():
        rows.sort(key=lambda r: (r[0], r[1]["id"]))
        for start_i, (start_date, _) in enumerate(rows):
            window = [(d, inv) for d, inv in rows[start_i:]
                      if (d - start_date).days <= split_window_days]
            if len(window) >= 2 and sum((_number(inv["total_amount"]) for _, inv in window), Decimal(0)) >= split_threshold:
                ids = [inv["id"] for _, inv in window]
                findings.append({
                    "code": "POSSIBLE_SPLIT_PURCHASE", "severity": "medium",
                    "invoice_ids": ids,
                    "reason": "Beberapa invoice di bawah batas persetujuan, tetapi total periode melampaui batas",
                })
                break
    return findings
