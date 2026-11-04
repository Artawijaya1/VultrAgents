FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY agent_requirements.txt graph_requirements.txt ./
RUN pip install --no-cache-dir -r agent_requirements.txt -r graph_requirements.txt
COPY agent_core ./agent_core
EXPOSE 8001
CMD ["uvicorn", "agent_core.graph_api:app", "--host", "127.0.0.1", "--port", "8001"]
