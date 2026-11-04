"""Optional HTTP API contract for frontend teammate."""
from fastapi import FastAPI
from pydantic import BaseModel, Field
from .orchestrator import execute_agent
from .llm_agent import chat_with_agent

app = FastAPI(title='ProcureGuard Agent API', version='0.1.0')

class TaskRequest(BaseModel):
    task: str
    reference_id: str = Field(min_length=1, max_length=100)

class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)

@app.get('/health')
def health():
    return {'status': 'ok', 'mode': 'mock', 'version': '0.1.0'}

@app.post('/api/agents/execute')
def execute(req: TaskRequest):
    return execute_agent(req.task, req.reference_id)

@app.post('/api/agents/chat')
async def chat(req: ChatRequest):
    return await chat_with_agent(req.question)
