"""Email is intentionally disabled until consent, approval and sender configuration."""

def send_supplier_email(*args, **kwargs):
    raise PermissionError("Outbound email is disabled in this starter project")
