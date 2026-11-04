"""Example RBAC only. Enforce real claims per request in production."""
PERMISSIONS = {
    "buyer": {"po.read", "negotiation.draft", "fraud.read"},
    "finance": {"po.read", "fraud.read", "invoice.review"},
    "auditor": {"po.read", "fraud.read", "audit.read"},
    "approver": {"po.read", "negotiation.draft", "fraud.read", "approval.decide"},
    "admin": {"po.read", "fraud.read", "audit.read", "users.manage"},
}

def may(role: str, permission: str) -> bool:
    return permission in PERMISSIONS.get(role, set())
