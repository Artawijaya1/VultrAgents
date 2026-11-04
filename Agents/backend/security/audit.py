"""Audit design placeholder: actor, action, entity ID, UTC timestamp, trace ID.
Do not log secrets, full bank numbers, or raw private emails.
"""
AUDIT_FIELDS = ("actor_id", "action", "entity_type", "entity_id", "timestamp_utc", "trace_id")
