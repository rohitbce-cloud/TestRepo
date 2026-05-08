import json
import logging
from typing import Any

import requests

from ..config import Settings

logger = logging.getLogger("agent.github")


class GitHubService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.github_token = settings.github_token
        self.base_url = "https://api.github.com"

    def _request(self, method: str, path: str, json_data: dict | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github+json",
        }
        response = requests.request(method, url, json=json_data, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def extract_repository_full_name(self, payload: dict[str, Any]) -> str:
        repo = payload.get("repository") or payload.get("repo")
        if isinstance(repo, dict):
            return repo.get("full_name") or f"{repo.get('owner', {}).get('login', 'unknown')}/{repo.get('name', 'unknown')}"
        return "unknown/unknown"

    def extract_pull_request_number(self, payload: dict[str, Any]) -> int | None:
        pr = payload.get("pull_request")
        if isinstance(pr, dict):
            return pr.get("number")
        return None

    def extract_diff(self, payload: dict[str, Any], event_name: str) -> str:
        if event_name in {"pull_request", "pull_request_target"}:
            pr = payload.get("pull_request") or {}
            if pr.get("diff_url"):
                return self._get_url_text(pr["diff_url"])
            if pr.get("patch_url"):
                return self._get_url_text(pr["patch_url"])
            repo_full_name = self.extract_repository_full_name(payload)
            pr_number = self.extract_pull_request_number(payload)
            if repo_full_name != "unknown/unknown" and pr_number:
                return self.get_pull_request_diff(repo_full_name, pr_number)
        if event_name == "push":
            repo_full_name = self.extract_repository_full_name(payload)
            before = payload.get("before")
            after = payload.get("after")
            if repo_full_name != "unknown/unknown" and before and after:
                return self.get_push_diff(repo_full_name, before, after)
        return payload.get("diff", "") or payload.get("patch", "") or ""

    def _get_url_text(self, url: str) -> str:
        response = requests.get(url, headers={"Authorization": f"Bearer {self.github_token}"}, timeout=30)
        response.raise_for_status()
        return response.text

    def get_pull_request_diff(self, repo_full_name: str, pull_number: int) -> str:
        owner, repo = repo_full_name.split("/")
        path = f"/repos/{owner}/{repo}/pulls/{pull_number}"
        pr = self._request("GET", path)
        diff_url = pr.get("diff_url")
        if diff_url:
            return self._get_url_text(diff_url)
        return ""

    def get_push_diff(self, repo_full_name: str, before: str, after: str) -> str:
        owner, repo = repo_full_name.split("/")
        path = f"/repos/{owner}/{repo}/compare/{before}...{after}"
        result = self._request("GET", path)
        files = result.get("files", [])
        patches = []
        for file in files:
            filename = file.get("filename")
            patch = file.get("patch")
            if filename and patch:
                patches.append(f"diff --git a/{filename} b/{filename}\n{patch}")
        if patches:
            return "\n\n".join(patches)
        return json.dumps(result, indent=2)

    def post_pr_comment(self, repo_full_name: str, pull_number: int, body: str) -> dict[str, Any]:
        owner, repo = repo_full_name.split("/")
        path = f"/repos/{owner}/{repo}/issues/{pull_number}/comments"
        return self._request("POST", path, json_data={"body": body})
