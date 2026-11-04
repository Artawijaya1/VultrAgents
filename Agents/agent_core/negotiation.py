"""Rule-grounded negotiation recommendation: never sends or changes a PO."""
from decimal import Decimal, ROUND_DOWN
from .data_provider import ProcurementProvider


def recommend_negotiation(provider: ProcurementProvider, po_id: str) -> dict:
    po = provider.get_po(po_id)
    if po is None:
        return {'status': 'not_found', 'po_id': po_id, 'error': 'PO tidak ditemukan'}
    price = Decimal(str(po['offered_unit_price']))
    ceiling = Decimal(str(po['budget_ceiling_unit']))
    previous = Decimal(str(po['previous_unit_price']))
    # Backend serializes PostgreSQL NUMERIC(18,4) as a decimal string,
    # e.g. "10.0000"; int("10.0000") raises ValueError.
    # Current business rules require whole units. Never silently truncate fractions.
    try:
        quantity_value = Decimal(str(po['quantity']))
        if (not quantity_value.is_finite() or quantity_value <= 0
                or quantity_value != quantity_value.to_integral_value()
                or quantity_value > Decimal('99999999999999')):
            return {'status': 'invalid_data', 'po_id': po_id,
                    'error': 'Quantity harus bilangan bulat positif yang valid'}
        quantity = int(quantity_value)
    except (ValueError, TypeError, ArithmeticError):
        return {'status': 'invalid_data', 'po_id': po_id,
                'error': 'Quantity harus bilangan bulat positif yang valid'}
    if min(price, ceiling, previous) <= 0 or quantity <= 0:
        return {'status': 'invalid_data', 'po_id': po_id, 'error': 'Harga/jumlah tidak valid'}
    opening = (min(ceiling * Decimal('0.97'), previous * Decimal('0.95')) / 1000).to_integral_value(rounding=ROUND_DOWN) * 1000
    opening = min(opening, ceiling)
    options = [
        {'option': 'discount', 'proposal_unit_price': int(opening), 'reason': 'Penawaran awal di bawah batas anggaran'},
        {'option': 'volume_or_terms', 'proposal_unit_price': int(ceiling), 'reason': 'Minta diskon/layanan tambahan tanpa melewati batas unit'},
        {'option': 'escalate', 'proposal_unit_price': None, 'reason': 'Bila supplier menolak, minta keputusan manusia atau evaluasi pemasok alternatif'},
    ]
    return {
        'status': 'draft', 'agent': 'negotiation', 'po_id': po_id,
        'currency': po['currency'], 'offered_unit_price': int(price),
        'budget_ceiling_unit': int(ceiling), 'previous_unit_price': int(previous),
        'quantity': quantity, 'opening_offer_unit': int(opening),
        'potential_savings_vs_offer': int((price - opening) * quantity),
        'options': options, 'requires_approval': True,
        'draft_message': f"Mohon pertimbangan penawaran Rp{int(opening):,} per unit untuk PO {po_id}. Apakah terdapat opsi diskon atau termin yang dapat membantu?".replace(',', '.'),
        'evidence': {'po_id': po_id, 'supplier_id': po['supplier_id']},
        'disclaimer': 'Saran awal berbasis aturan dan data simulasi; belum dikirim ke supplier.'
    }
