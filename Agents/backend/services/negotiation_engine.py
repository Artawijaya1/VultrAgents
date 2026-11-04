"""Deterministic, non-LLM negotiation suggestions for the demonstration.

Never treat a draft as a legal commitment or approval.
"""
from decimal import Decimal

def plan_negotiation(po: dict) -> dict:
    if not po:
        raise ValueError("Purchase order not found")
    qty = int(po["quantity"])
    if qty <= 0:
        raise ValueError("Quantity must be positive")
    current = Decimal(str(po["unit_price"]))
    target = Decimal(str(po["target_unit_price"]))
    ceiling = Decimal(str(po["contract_max_unit_price"]))
    median = Decimal(str(po["historical_median_price"]))
    if min(current, target, ceiling, median) <= 0:
        raise ValueError("Prices must be positive")
    required_days = int(po["required_delivery_days"])
    offered_days = int(po["quoted_delivery_days"])
    over_contract = current > ceiling
    late = offered_days > required_days
    reasons = []
    if over_contract:
        reasons.append("Harga penawaran di atas batas kontrak; eskalasi wajib")
    if current > median:
        reasons.append("Harga penawaran melebihi median historis")
    if late:
        reasons.append("Lead time melebihi kebutuhan")
    counter = min(target, ceiling)
    proposal = (
        f"Mohon pertimbangkan harga Rp{counter:,.0f}/unit untuk {qty} unit dan "
        f"pengiriman maksimal {required_days} hari. "
        "Mohon konfirmasi kesediaan atau alternatif penawaran."
    )
    return {
        "purchase_order": po["number"],
        "current_unit_price": str(current),
        "target_unit_price": str(target),
        "contract_max_unit_price": str(ceiling),
        "estimated_savings_if_accepted": str(max(Decimal("0"), (current - counter) * qty)),
        "flags": reasons,
        "proposed_strategy": "minta revisi harga dan tanggal" if reasons else "konfirmasi kondisi penawaran",
        "draft_message": proposal,
        "approval_required": True,
        "status": "DRAFT_ONLY",
    }
