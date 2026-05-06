from __future__ import annotations

from typing import Any

from .github_client import GitHubApiError, GitHubClient


class PRCommentPoster:
    def __init__(self, github_client: GitHubClient) -> None:
        self._github_client = github_client

    def post_review_comments(
        self,
        repository: str,
        pr_number: int,
        commit_sha: str,
        comments: list[dict[str, Any]],
        valid_lines_by_file: dict[str, set[int]],
    ) -> dict[str, Any]:
        posted: list[dict[str, Any]] = []
        fallback_comments: list[dict[str, Any]] = []

        for comment in comments:
            normalized = self._normalize_comment(comment)
            validation_error = self._validate_comment(normalized, valid_lines_by_file)
            if validation_error:
                fallback_comments.append({**normalized, "reason": validation_error})
                continue

            try:
                self._github_client.create_pull_request_review_comment(
                    repository=repository,
                    pr_number=pr_number,
                    commit_sha=commit_sha,
                    path=normalized["file_path"],
                    line=normalized["line"],
                    side=normalized["side"],
                    body=normalized["body"],
                )
                posted.append(normalized)
            except GitHubApiError as exc:
                fallback_comments.append({**normalized, "reason": str(exc)})
            except Exception as exc:
                fallback_comments.append({**normalized, "reason": f"Unexpected error: {exc}"})

        fallback_posted = False
        if fallback_comments:
            fallback_posted = self._post_fallback_comment(repository, pr_number, fallback_comments)

        return {
            "line_comments_requested": len(comments),
            "line_comments_posted": len(posted),
            "fallback_comments": len(fallback_comments),
            "fallback_posted": fallback_posted,
        }

    @staticmethod
    def _normalize_comment(comment: dict[str, Any]) -> dict[str, Any]:
        try:
            line = int(comment.get("line", 0))
        except (TypeError, ValueError):
            line = 0

        return {
            "file_path": str(comment.get("file_path", "")).strip(),
            "line": line,
            "side": str(comment.get("side", "RIGHT")).strip().upper() or "RIGHT",
            "body": str(comment.get("body") or comment.get("comment") or "").strip(),
        }

    @staticmethod
    def _validate_comment(comment: dict[str, Any], valid_lines_by_file: dict[str, set[int]]) -> str:
        file_path = comment["file_path"]
        if not file_path:
            return "Missing file_path."
        if not comment["body"]:
            return "Missing comment body."
        if comment["side"] != "RIGHT":
            return "Only RIGHT-side PR review comments are supported."
        if comment["line"] <= 0:
            return "Missing or invalid target line."
        if file_path not in valid_lines_by_file:
            return "File is not part of the PR diff."
        if comment["line"] not in valid_lines_by_file[file_path]:
            return "Line is not present in the annotated PR diff."
        return ""

    def _post_fallback_comment(
        self,
        repository: str,
        pr_number: int,
        fallback_comments: list[dict[str, Any]],
    ) -> bool:
        body_lines = [
            "Automated PR review comments could not be anchored to exact diff lines safely.",
            "",
            "Please review these manually:",
            "",
        ]

        for item in fallback_comments[:20]:
            location = item["file_path"] or "unknown file"
            line = item["line"] or "unknown line"
            body_lines.append(f"- `{location}:{line}`: {item['body']}")
            body_lines.append(f"  Reason: {item['reason']}")

        if len(fallback_comments) > 20:
            body_lines.append(f"- {len(fallback_comments) - 20} additional comments omitted.")

        try:
            self._github_client.create_issue_comment(
                repository=repository,
                issue_number=pr_number,
                body="\n".join(body_lines),
            )
            return True
        except Exception as exc:
            print(f"Warning: failed to post fallback PR comment: {exc}")
            return False
