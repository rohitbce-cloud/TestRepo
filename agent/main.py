from fastapi import FastAPI, Header, HTTPException, Request
from pathlib import Path

from .config import Settings
from .orchestrator import AgentOrchestrator
from .utils.logging import get_logger

app = FastAPI(
    title="AI Engineering Agent",
    description="Backend AI orchestration service for GitHub events.",
)
logger = get_logger("agent.main")
settings = Settings()
orchestrator = AgentOrchestrator(settings)


@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-engine-agent"}


@app.post("/webhook")
async def webhook(request: Request, x_github_event: str | None = Header(None)):
    payload = await request.json()
    if payload is None:
        raise HTTPException(status_code=400, detail="Unable to parse JSON payload.")

    event_name = x_github_event or "push"
    logger.info("Received GitHub event %s", event_name)
    result = orchestrator.process_event(payload, event_name)
    return {"status": "processed", "event": event_name, "result": result}
