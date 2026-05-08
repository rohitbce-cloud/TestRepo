import argparse
import json
import os
import sys
from pathlib import Path

from .config import Settings
from .orchestrator import AgentOrchestrator
from .services.github_service import GitHubService
from .services.openai_service import OpenAIService
from .utils.logging import get_logger

logger = get_logger("agent.runner")


def forward_event_to_http(endpoint: str, payload: dict, event_name: str) -> dict:
    import requests

    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": event_name,
    }
    response = requests.post(endpoint, json=payload, headers=headers, timeout=20)
    response.raise_for_status()
    return response.json()


def load_event_payload(path: str) -> dict:
    if not path or not os.path.exists(path):
        raise FileNotFoundError(f"GitHub event payload path not found: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Engineering Agent runner.")
    parser.add_argument(
        "--forward-to-http",
        action="store_true",
        help="Forward GitHub event payload to a running FastAPI agent service.",
    )
    parser.add_argument(
        "--event-file",
        type=str,
        help="Path to a GitHub event JSON payload for local execution.",
    )
    parser.add_argument(
        "--event-name",
        type=str,
        help="GitHub event name override for local execution.",
    )
    args = parser.parse_args()

    settings = Settings()
    event_path = args.event_file or settings.github_event_path or os.getenv("GITHUB_EVENT_PATH")
    event_name = args.event_name or settings.github_event_name or os.getenv("GITHUB_EVENT_NAME", "push")

    if args.forward_to_http:
        endpoint = settings.agent_http_endpoint
        if not endpoint:
            logger.error("AGENT_HTTP_ENDPOINT is required when forwarding to HTTP.")
            return 1
        payload = load_event_payload(event_path)
        result = forward_event_to_http(endpoint, payload, event_name)
        logger.info("Forwarded event to HTTP service: %s", result)
        return 0

    if not event_path:
        logger.error("GITHUB_EVENT_PATH is not set.")
        return 1

    payload = load_event_payload(event_path)
    orchestrator = AgentOrchestrator(settings)
    result = orchestrator.process_event(payload, event_name)
    logger.info("Analysis complete.")
    logger.info(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
