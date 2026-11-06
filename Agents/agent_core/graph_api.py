"""Independent REST API for the teammate's backend to consume.

Runs as a separate service. Not an unauthenticated public endpoint.
"""
from __future__ import annotations
import asyncio
import os
import secrets
from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from dotenv import load_dotenv

# Keep the Agent API key and data mode aligned with the repository's local
# service configuration, even when the process was launched from a shell that
# already has stale environment variables.
load_dotenv(Path(__file__).resolve().parents[1] / '.env', override=True)

from .graph_workflow import run_workflow
from .intelligent_graph import run_chat

app = FastAPI(title='ProcureGuard LangGraph Agent API', version='0.2.0', docs_url='/docs')


class AgentRequest(BaseModel):
    task: Literal['negotiation', 'fraud']
    reference_id: str = Field(min_length=1, max_length=100, pattern=r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$')
    instruction: str = Field(default='', max_length=1000)
    request_id: str | None = Field(default=None, min_length=1, max_length=100)
    reference_type: Literal['po', 'supplier'] = 'supplier'


class AgentResponse(BaseModel):
    request_id: str
    task: str
    reference_id: str
    status: str
    summary: str
    result: dict | None
    precheck: dict | None
    tool_trace: list[dict]
    requires_approval: bool
    error: str | None


def authorized(authorization: str | None = Header(default=None)) -> None:
    expected = os.getenv('AGENT_API_KEY', '')
    if not expected:
        raise HTTPException(status_code=503, detail='AGENT_API_KEY is not configured.')
    prefix = 'Bearer '
    if not authorization or not authorization.startswith(prefix):
        raise HTTPException(status_code=401, detail='Unauthorized')
    provided = authorization[len(prefix):]
    if not secrets.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail='Unauthorized')


@app.get('/health')
def health():
    return {'status': 'ok', 'version': '0.2.0', 'workflow': 'langgraph',
            'mode': os.getenv('AGENT_DATA_MODE', 'mock')}


@app.post('/api/v1/agents/run', response_model=AgentResponse, dependencies=[Depends(authorized)])
async def run_agent(request: AgentRequest):
    request_id = request.request_id or str(uuid4())
    try:
        return await asyncio.wait_for(run_workflow(
            task=request.task, reference_id=request.reference_id,
            instruction=request.instruction, request_id=request_id,
            reference_type=request.reference_type), timeout=30)
    except TimeoutError:
        raise HTTPException(status_code=504, detail='Agent timeout')
    except Exception:
        # Never leak backend URLs, credentials, or internal stack traces to API callers.
        raise HTTPException(status_code=502, detail='The Agent could not call the data source or MCP tool.')


# PROCUREGUARD_STAGE6_CHAT_API
class AgentChatRequest(BaseModel):
    task: Literal['negotiation', 'fraud']
    reference_id: str = Field(min_length=1, max_length=100, pattern=r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$')
    session_id: str | None = Field(default=None, min_length=1, max_length=80,
                                    pattern=r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$')
    question: str = Field(min_length=1, max_length=1000)


class AgentChatResponse(BaseModel):
    session_id: str
    task: str
    reference_id: str
    status: str
    summary: str
    answer: str
    verified_result: dict | None
    precheck: dict | None
    tool_trace: list[dict]
    turn_index: int
    requires_approval: bool
    error: str | None
    notice: str


@app.post('/api/v1/agents/chat', response_model=AgentChatResponse,
          dependencies=[Depends(authorized)])
async def chat_agent(request: AgentChatRequest):
    try:
        return await asyncio.wait_for(run_chat(
            task=request.task, reference_id=request.reference_id,
            question=request.question, session_id=request.session_id,
        ), timeout=float(os.getenv('AGENT_CHAT_TIMEOUT_SECONDS', '145')))

    except TimeoutError:
        raise HTTPException(status_code=504, detail='Agent conversation timeout')
    except Exception:
        raise HTTPException(status_code=502, detail='The Agent could not process the conversation.')
