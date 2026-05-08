import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .agents.documentation_agent import DocumentationAgent
from .agents.reuse_agent import ReuseAgent
from .config import Settings
from .services.github_service import GitHubService
from .services.openai_service import OpenAIService
from .services.vector_store import VectorStore
from .utils.logging import get_logger

logger = get_logger("agent.orchestrator")


class AgentOrchestrator:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.settings.ensure_data_root()
        self.openai = OpenAIService(self.settings)
        self.github = GitHubService(self.settings)
        self.vector_store = VectorStore(self.settings)
        self.documentation_agent = DocumentationAgent(self.openai, self.settings)
        self.reuse_agent = ReuseAgent(self.openai, self.vector_store, self.settings)

    def process_event(self, payload: dict[str, Any], event_name: str) -> dict[str, Any]:
        logger.info("Processing event %s", event_name)
        repo_full_name = self.github.extract_repository_full_name(payload)
        diff_text = self.github.extract_diff(payload, event_name)

        report = self.documentation_agent.generate_report(diff_text, payload)
        reuse = self.reuse_agent.find_similar_code(diff_text, payload)

        response = {
            "repository": repo_full_name,
            "event": event_name,
            "report": report,
            "reuse": reuse,
        }

        self._persist_response(response, repo_full_name, event_name)

        if event_name in {"pull_request", "pull_request_target"}:
            pr_number = self.github.extract_pull_request_number(payload)
            if pr_number:
                body = self._build_pr_comment(response)
                self.github.post_pr_comment(repo_full_name, pr_number, body)
                response["comment_posted"] = True

        return response

    def _persist_response(self, response: dict[str, Any], repo_full_name: str, event_name: str) -> None:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_{repo_full_name.replace('/', '_')}_{event_name}_{timestamp}.json"
        output_path = Path(self.settings.data_root) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as fh:
            json.dump(response, fh, indent=2)
        logger.info("Saved analysis output to %s", output_path)

    def _build_pr_comment(self, response: dict[str, Any]) -> str:
        report = response["report"]
        reuse = response["reuse"]
        similar_code = reuse.get("similar_code") or []
        similar_section = "None found." if not similar_code else "\n".join(
            [f"- {item['path']} (score: {item['score']:.2f})" for item in similar_code]
        )

        return (
            "### AI Engineering Agent Report\n"
            "### Change Summary\n"
            f"{report.get('change_summary', 'N/A')}\n\n"
            "### What Changed\n"
            f"{report.get('what_changed', 'N/A')}\n\n"
            "### Why Change Was Made\n"
            f"{report.get('why_changed', 'N/A')}\n\n"
            "### Impact Analysis\n"
            f"{report.get('impact_analysis', 'N/A')}\n\n"
            "### Risk / Considerations\n"
            f"{report.get('risk_assessment', 'N/A')}\n\n"
            "### Similar Existing Code (if any)\n"
            f"{similar_section}\n\n"
            "### Recommendation (Reuse / Modify / Build New)\n"
            f"{report.get('recommendation', 'N/A')}\n\n"
            "### Developer Summary\n"
            f"{report.get('developer_summary', 'N/A')}"
        )
