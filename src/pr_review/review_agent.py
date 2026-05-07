from __future__ import annotations

from pathlib import Path
from typing import Any

from .comment_quality import ReviewCommentQualityGate, ReviewIssueQualityGate
from .llm_client import LLMClient
from .models import ComparisonResult, PRMetadata, ReviewResult
from .prompt_builder import PromptBuilder
from .review_focus import ReviewFocusBuilder
from .rulebook_loader import RulebookContext


class ReviewAgent:
    def __init__(
        self,
        llm_client: LLMClient,
        prompt_path: Path,
        prompt_builder: PromptBuilder | None = None,
        comment_quality_gate: ReviewCommentQualityGate | None = None,
        issue_quality_gate: ReviewIssueQualityGate | None = None,
        review_focus_builder: ReviewFocusBuilder | None = None,
    ) -> None:
        self._llm_client = llm_client
        self._prompt = prompt_path.read_text(encoding="utf-8")
        self._prompt_builder = prompt_builder or PromptBuilder()
        self._comment_quality_gate = comment_quality_gate or ReviewCommentQualityGate()
        self._issue_quality_gate = issue_quality_gate or ReviewIssueQualityGate()
        self._review_focus_builder = review_focus_builder or ReviewFocusBuilder()

    def run(
        self,
        pr_metadata: PRMetadata,
        comparisons: list[ComparisonResult],
        rulebook_context: RulebookContext | None = None,
    ) -> ReviewResult:
        review_focus = self._review_focus_builder.build(pr_metadata, comparisons)
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
                    "annotated_patch_diff": item.annotated_patch,
                    "valid_comment_lines": item.added_lines or item.commentable_lines,
                    "added_lines": item.added_lines,
                    "diff_positions_by_line": item.diff_positions_by_line,
                }
                for item in comparisons
            ],
            "rulebooks_loaded": rulebook_context.to_dict() if rulebook_context else {},
            "review_focus": review_focus,
        }

        system_prompt = self._prompt_builder.build_review_prompt(self._prompt, rulebook_context)
        result = self._llm_client.json_chat(system_prompt, payload)

        raw_issues_found = self._normalize_list_of_dicts(result.get("issues_found", []))
        issues_found = self._issue_quality_gate.filter(raw_issues_found)
        removed_issues = len(raw_issues_found) - len(issues_found)
        if removed_issues > 0:
            print(f"Review issue quality gate removed {removed_issues} low-signal issue(s).")

        suggested_comments = self._normalize_suggested_comments(result.get("suggested_comments", []))
        filtered_comments = self._comment_quality_gate.filter(suggested_comments, issues_found)
        removed_comments = len(suggested_comments) - len(filtered_comments)
        if removed_comments > 0:
            print(f"Review comment quality gate removed {removed_comments} low-signal comment(s).")

        risk_level = self._normalize_risk_level(str(result.get("risk_level", "Low")).strip(), issues_found)
        final_recommendation = self._normalize_final_recommendation(
            str(result.get("final_recommendation", "Merge")).strip(),
            issues_found,
            filtered_comments,
        )

        return ReviewResult(
            summary=str(result.get("summary", "")).strip(),
            purpose_of_pr=str(result.get("purpose_of_pr", "")).strip(),
            summary_of_changes=str(result.get("summary_of_changes", "")).strip(),
            problem_being_solved=str(result.get("problem_being_solved", "")).strip(),
            expected_outcome=str(result.get("expected_outcome", "")).strip(),
            issues_found=issues_found,
            suggested_comments=filtered_comments,
            final_recommendation=final_recommendation,
            reasoning=str(result.get("reasoning", "")).strip(),
            risk_level=risk_level,
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

    @staticmethod
    def _normalize_suggested_comments(value: Any) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            return []

        comments: list[dict[str, Any]] = []
        for item in value:
            if not isinstance(item, dict):
                continue

            raw_line = item.get("line")
            try:
                line = int(raw_line)
            except (TypeError, ValueError):
                line = 0

            body = str(item.get("body") or item.get("comment") or "").strip()
            comments.append(
                {
                    "file_path": str(item.get("file_path", "")).strip(),
                    "line": line,
                    "side": str(item.get("side", "RIGHT")).strip().upper() or "RIGHT",
                    "body": body,
                }
            )
        return comments

    @staticmethod
    def _normalize_risk_level(raw_risk: str, issues_found: list[dict[str, Any]]) -> str:
        valid = {"Low", "Medium", "High"}
        risk_level = raw_risk.capitalize() if raw_risk.capitalize() in valid else "Low"

        severities = {str(issue.get("severity", "")).capitalize() for issue in issues_found}
        if "High" in severities:
            return "High"
        if "Medium" in severities and risk_level == "Low":
            return "Medium"
        if not issues_found:
            return "Low" if risk_level == "High" else risk_level
        return risk_level

    @staticmethod
    def _normalize_final_recommendation(
        raw_recommendation: str,
        issues_found: list[dict[str, Any]],
        suggested_comments: list[dict[str, Any]],
    ) -> str:
        high_severity_exists = any(str(issue.get("severity", "")).capitalize() == "High" for issue in issues_found)
        if high_severity_exists:
            return "Do Not Merge"
        if not issues_found and not suggested_comments:
            return "Merge"
        return "Do Not Merge" if raw_recommendation == "Do Not Merge" else "Merge"
