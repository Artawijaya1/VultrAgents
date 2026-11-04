"""Types shared across API and tools (no implicit float currency calculations)."""
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class Offer:
    supplier_id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    lead_time_days: int

@dataclass(frozen=True)
class FraudFinding:
    code: str
    severity: str
    rationale: str
    evidence: dict
