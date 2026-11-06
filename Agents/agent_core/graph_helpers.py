"""Pure helpers, independently testable without LangGraph/MCP dependencies."""
from __future__ import annotations
import json
import re

_VALID_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")


def validate_reference(task: str, reference_id: str) -> str | None:
    if task not in {'negotiation', 'fraud'}:
        return 'Task must be negotiation or fraud.'
    if not isinstance(reference_id, str) or not _VALID_ID.fullmatch(reference_id):
        return 'reference_id must contain 1-100 letters, numbers, dots, underscores, or hyphens.'
    return None


def normalize_mcp_result(reply: object) -> dict:
    """Normalize SDK structured content or text-only MCP responses."""
    if getattr(reply, 'is_error', False):
        return {'error': 'The MCP tool reported a failure.'}
    data = getattr(reply, 'structured_content', None)
    if isinstance(data, dict):
        if isinstance(data.get('result'), dict) and len(data) == 1:
            return data['result']
        return data
    for block in getattr(reply, 'content', []) or []:
        string = getattr(block, 'text', None)
        if isinstance(string, str):
            try:
                parsed = json.loads(string)
                if isinstance(parsed, dict):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass
    return {'error': 'The MCP response is not a JSON object.'}


def build_summary(task: str, result: dict, precheck: dict | None = None) -> str:
    """Safe deterministic fallback when LLM configuration is absent."""
    if result.get('error') or result.get('status') in {'not_found', 'invalid_data'}:
        return 'Data is unavailable or invalid. Check the reference ID and data source.'
    if task == 'negotiation':
        opening = result.get('opening_offer_unit')
        currency = result.get('currency', '')
        text = f'Negotiation draft ready: the opening offer is {currency} {opening} per unit.'
        if precheck and precheck.get('flag_count', 0):
            text += ' Supplier risk indicators were found; review them before negotiating.'
        return text + ' All business actions require human approval.'
    count = result.get('flag_count', 0)
    return (
        f'{count} anomaly indicator(s) were found for the supplier. '
        'Indicators are not proof of fraud; human review is required.'
    )
