import json
from agent_core.data_provider import MockProvider
from agent_core.negotiation import recommend_negotiation
from agent_core.po_fraud import analyze_purchase_order

provider = MockProvider()
for label, result in (
    ('NEGOTIATION PO-001', recommend_negotiation(provider, 'PO-001')),
    ('FRAUD BY PO-001', analyze_purchase_order(provider, 'PO-001')),
    ('FRAUD BY PO-999', analyze_purchase_order(provider, 'PO-999')),
):
    print(f'\n=== {label} ===')
    print(json.dumps(result, indent=2, ensure_ascii=False))
