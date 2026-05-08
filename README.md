# AI Engineering Agent

Enterprise-grade AI Engineering Agent scaffold for Git/GitHub-level automation.

## Architecture

- Trigger Layer: GitHub Actions triggers on `push` and `pull_request`.
- Agent Orchestrator: Python service (`FastAPI`) receives events and routes work.
- Multi-Agent Pattern: Documentation Agent + Reuse Agent.
- AI Layer: OpenAI completion and embeddings.
- Code Processing: GitHub diff extraction and change analysis.
- Vector Search: FAISS-backed reuse search with embedding metadata.
- Action Layer: PR comment automation.
- Storage: Local debug storage and vector metadata.

## Files

- `.github/workflows/ai-agent.yml` - GitHub Action trigger.
- `agent/main.py` - FastAPI webhook endpoint.
- `agent/runner.py` - CLI event handler for GitHub Actions.
- `agent/orchestrator.py` - Central orchestration logic.
- `agent/services/openai_service.py` - OpenAI API integration.
- `agent/services/github_service.py` - GitHub diff and comment helpers.
- `agent/services/vector_store.py` - Vector embedding storage and search.
- `agent/agents/documentation_agent.py` - Change analysis + report generation.
- `agent/agents/reuse_agent.py` - Similar code search and reuse recommendations.
- `agent/config.py` - Environment-based configuration.
- `agent/utils/logging.py` - Structured logging.

## Setup

1. Create a `.env` file or configure environment variables:
   - `OPENAI_API_KEY`
   - `GITHUB_TOKEN`
   - optional `AGENT_HTTP_ENDPOINT` when forwarding events to a remote service
   - optional `GITHUB_EVENT_PATH` and `GITHUB_EVENT_NAME` for local testing
2. Install dependencies:
   - `python -m pip install --upgrade pip`
   - `python -m pip install -r requirements.txt`
3. Run locally:
   - `uvicorn agent.main:app --host 0.0.0.0 --port 8000`
   - or `python -m agent.runner --event-file ./sample-event.json --event-name pull_request`

## GitHub Actions

The workflow at `.github/workflows/ai-agent.yml` runs on `push` and `pull_request` events. It checks out the repository, installs dependencies, and executes `agent.runner` with the event payload.

## Output Format

The agent produces structured results in the following form:

### Change Summary
### What Changed
### Why Change Was Made
### Impact Analysis
### Risk / Considerations
### Similar Existing Code (if any)
### Recommendation (Reuse / Modify / Build New)
### Developer Summary
