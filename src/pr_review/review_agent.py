from __future__ import annotations

from pathlib import Path
from typing import Any

from .llm_client import LLMClient
from .models import ComparisonResult, PRMetadata, ReviewResult


class ReviewAgent:
    def __init__(self, llm_client: LLMClient, prompt_path: Path) -> None:
        self._llm_client = llm_client
        self._prompt = prompt_path.read_text(encoding="utf-8")

    def run(self, pr_metadata: PRMetadata, comparisons: list[ComparisonResult]) -> ReviewResult:
        payload = {
            "pr_metadata": {
                "repository": pr_metadata.repository,
                "pr_number": pr_metadata.pr_number,
                "title": pr_metadata.title,
                "url": pr_metadata.html_url,
                "author": pr_metadata.author,
                "base_branch": pr_metadata.base_branch,
                "head_branch": pr_metadata.head_branch,
                "head_sha": pr_metadata.head_sha,
                "commits": pr_metadata.commits,
                "changed_files": pr_metadata.changed_files,
                "additions": pr_metadata.additions,
                "deletions": pr_metadata.deletions,
            },
            "comparison_results": [
                {
                    "file_path": item.file_path,
                    "change_type": item.change_type,
                    "change_summary": item.change_summary,
                    "behavioral_change": item.behavioral_change,
                    "risk_flags": item.risk_flags,
                    "semantic_impact": item.semantic_impact,
                    "risk_level": item.risk_level,
                }
                for item in comparisons
            ],
        }

        result = self._llm_client.json_chat(self._prompt, payload)

        issues_found = self._normalize_list_of_dicts(result.get("issues_found", []))
        suggested_comments = self._normalize_list_of_dicts(result.get("suggested_comments", []))

        return ReviewResult(
            summary=str(result.get("summary", "")).strip(),
            purpose_of_pr=str(result.get("purpose_of_pr", "")).strip(),
            summary_of_changes=str(result.get("summary_of_changes", "")).strip(),
            problem_being_solved=str(result.get("problem_being_solved", "")).strip(),
            expected_outcome=str(result.get("expected_outcome", "")).strip(),
            issues_found=issues_found,
            suggested_comments=suggested_comments,
            final_recommendation=str(result.get("final_recommendation", "Merge")).strip() or "Merge",
            reasoning=str(result.get("reasoning", "")).strip(),
            risk_level=str(result.get("risk_level", "Low")).strip() or "Low",
        )

    @staticmethod
    def _normalize_list_of_dicts(value: Any) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            return []
        output: list[dict[str, Any]] = []
        for item in value:
            if isinstance(item, dict):
                output.append(item)
        return output
