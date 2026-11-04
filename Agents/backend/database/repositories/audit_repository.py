"""Production TODO: append-only audit storage with actor and correlation ID."""

def append_audit_event(*, actor_id: int, action: str, payload: dict):
    raise NotImplementedError("Audit persistence must be configured before production writes")
