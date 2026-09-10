FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/app

COPY api /app/app/api
COPY agents /app/app/agents
COPY auth /app/app/auth
COPY tools /app/app/tools
COPY scripts /app/app/scripts
COPY agent.py /app/app/agent.py
COPY __init__.py /app/app/__init__.py

EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT}"]
