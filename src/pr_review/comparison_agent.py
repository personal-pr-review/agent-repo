from __future__ import annotations

from pathlib import Path

from .llm_client import LLMClient
from .models import ComparisonResult, PRFileContext


class ComparisonAgent:
    def __init__(self, llm_client: LLMClient, prompt_path: Path) -> None:
        self._llm_client = llm_client
        self._prompt = prompt_path.read_text(encoding="utf-8")

    def run_for_file(self, file_context: PRFileContext) -> ComparisonResult:
        payload = {
            "file_path": file_context.path,
            "file_status": file_context.status,
            "base_file_content": file_context.base_content,
            "head_file_content": file_context.head_content,
            "patch_diff": file_context.patch,
            "line_stats": {
                "additions": file_context.additions,
                "deletions": file_context.deletions,
                "changes": file_context.changes,
            },
        }

        result = self._llm_client.json_chat(self._prompt, payload)

        risk_flags = result.get("risk_flags", [])
        if not isinstance(risk_flags, list):
            risk_flags = []

        return ComparisonResult(
            file_path=file_context.path,
            change_type=file_context.status,
            change_summary=str(result.get("change_summary", "")).strip(),
            behavioral_change=str(result.get("behavioral_change", "")).strip(),
            risk_flags=[str(flag) for flag in risk_flags],
            semantic_impact=str(result.get("semantic_impact", "")).strip(),
            risk_level=str(result.get("risk_level", "Low")).strip() or "Low",
        )
