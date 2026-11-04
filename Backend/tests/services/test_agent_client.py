import asyncio
import json
import unittest
from unittest.mock import patch

import httpx
from pydantic import SecretStr

from app.core.config import Settings
from app.services.agent_client import AgentServiceError, call_agent


class AgentClientTests(unittest.TestCase):
    def setUp(self):
        self.settings = Settings(
            agent_api_url="http://127.0.0.1:8001",
            agent_api_key=SecretStr("agent-service-key"),
        )
        self.client_class = httpx.AsyncClient

    def _client_factory(self, handler):
        def factory(*args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(handler)
            return self.client_class(*args, **kwargs)

        return factory

    def test_call_agent_uses_service_bearer_and_validates_response(self):
        observed = {}
        response_body = {
            "request_id": "run-1",
            "task": "fraud",
            "reference_id": "PO-1",
            "status": "review_required",
            "summary": "Human review requested.",
            "result": {},
            "precheck": None,
            "tool_trace": [],
            "requires_approval": True,
            "error": None,
        }

        def handler(request):
            observed["url"] = str(request.url)
            observed["authorization"] = request.headers.get("Authorization")
            observed["payload"] = json.loads(request.read())
            return httpx.Response(200, json=response_body)

        with patch("app.services.agent_client.get_settings", return_value=self.settings), patch(
            "app.services.agent_client.httpx.AsyncClient",
            self._client_factory(handler),
        ):
            response = asyncio.run(
                call_agent("run", {"reference_id": "PO-1"}, timeout=2)
            )

        self.assertEqual(response, response_body)
        self.assertEqual(observed["url"], "http://127.0.0.1:8001/api/v1/agents/run")
        self.assertEqual(observed["authorization"], "Bearer agent-service-key")
        self.assertEqual(observed["payload"], {"reference_id": "PO-1"})

    def test_call_agent_rejects_malformed_response(self):
        handler = lambda _: httpx.Response(200, json={"requires_approval": "yes"})
        with patch("app.services.agent_client.get_settings", return_value=self.settings), patch(
            "app.services.agent_client.httpx.AsyncClient",
            self._client_factory(handler),
        ):
            with self.assertRaisesRegex(AgentServiceError, "API contract"):
                asyncio.run(call_agent("run", {}, timeout=2))
