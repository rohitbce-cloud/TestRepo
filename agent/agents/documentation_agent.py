from ..services.openai_service import OpenAIService
from ..config import Settings
from ..utils.logging import get_logger

logger = get_logger("agent.documentation")


class DocumentationAgent:
    def __init__(self, openai_service: OpenAIService, settings: Settings):
        self.openai = openai_service
        self.settings = settings

    def generate_report(self, diff_text: str, payload: dict) -> dict:
        if not diff_text:
            logger.warning("Empty diff received for report generation.")
            return {
                "change_summary": "No diff available.",
                "what_changed": "Unable to compute change details.",
                "why_changed": "No change context available.",
                "impact_analysis": "No impact analysis available.",
                "risk_assessment": "No risk assessment available.",
                "recommendation": "No recommendation available.",
                "developer_summary": "No developer summary available.",
            }

        context = self._build_context(payload)
        analysis = self.openai.summarize_diff(diff_text, context)
        return self._parse_analysis(analysis)

    def _build_context(self, payload: dict) -> str:
        repo_name = payload.get("repository", {}).get("full_name", "unknown")
        event_type = payload.get("action", payload.get("event", "unknown"))
        return f"Repository: {repo_name}. Event type: {event_type}."

    def _parse_analysis(self, content: str) -> dict:
        sections = {
            "Change Summary": "change_summary",
            "What Changed": "what_changed",
            "Why Change Was Made": "why_changed",
            "Impact Analysis": "impact_analysis",
            "Risk Assessment": "risk_assessment",
            "Recommendation": "recommendation",
            "Developer Summary": "developer_summary",
        }
        parsed = {value: "" for value in sections.values()}
        current_section = None
        buffer = []
        for line in content.splitlines():
            if line.strip().rstrip(":") in sections:
                if current_section and buffer:
                    parsed[sections[current_section]] = "\n".join(buffer).strip()
                    buffer = []
                current_section = line.strip().rstrip(":")
                continue
            if current_section:
                buffer.append(line)
        if current_section and buffer:
            parsed[sections[current_section]] = "\n".join(buffer).strip()
        return parsed
