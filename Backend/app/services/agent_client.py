from urllib.parse import urlsplit
from typing import Any

import httpx

from app.core.config import get_settings


class AgentServiceError(RuntimeError):
    pass


class AgentServiceNotConfigured(AgentServiceError):
    pass


class AgentServiceTimeout(AgentServiceError):
    pass


async def call_agent(endpoint: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    settings = get_settings()
    if not settings.agent_api_url or settings.agent_api_key is None:
        raise AgentServiceNotConfigured("Agent API is not configured.")
    if endpoint not in {"run", "chat"}:
        raise AgentServiceError("Unsupported Agent endpoint.")

    parsed = urlsplit(settings.agent_api_url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or (parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"})
    ):
        raise AgentServiceError("Agent API URL must use HTTPS except on localhost.")

    url = f"{settings.agent_api_url.rstrip('/')}/api/v1/agents/{endpoint}"
    headers = {
        "Authorization": f"Bearer {settings.agent_api_key.get_secret_value()}",
        "Accept": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
            response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
    except httpx.TimeoutException as exc:
        raise AgentServiceTimeout("Agent request timed out.") from exc
    except httpx.HTTPError as exc:
        raise AgentServiceError("Agent service is unavailable or rejected the request.") from exc
    except ValueError as exc:
        raise AgentServiceError("Agent returned an invalid response.") from exc

    if not isinstance(data, dict):
        raise AgentServiceError("Agent response must be a JSON object.")
    required_fields = (
        {
            "request_id",
            "task",
            "reference_id",
            "status",
            "summary",
            "result",
            "precheck",
            "tool_trace",
            "requires_approval",
            "error",
        }
        if endpoint == "run"
        else {
            "session_id",
            "task",
            "reference_id",
            "status",
            "summary",
            "answer",
            "verified_result",
            "precheck",
            "tool_trace",
            "turn_index",
            "requires_approval",
            "error",
            "notice",
        }
    )
    if not required_fields.issubset(data):
        raise AgentServiceError("Agent response does not match its API contract.")
    if not isinstance(data["requires_approval"], bool) or not isinstance(
        data["tool_trace"], list
    ):
        raise AgentServiceError("Agent response does not match its API contract.")
    return data
