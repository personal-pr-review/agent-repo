from __future__ import annotations

import time
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
        pull_request_node_id: str,
        comments: list[dict[str, Any]],
        valid_lines_by_file: dict[str, set[int]],
        diff_positions_by_file: dict[str, dict[int, int]],
    ) -> dict[str, Any]:
        ready_comments: list[dict[str, Any]] = []
        fallback_comments: list[dict[str, Any]] = []

        for comment in comments:
            normalized = self._normalize_comment(comment)
            validation_error = self._validate_comment(normalized, valid_lines_by_file)
            if validation_error:
                fallback_comments.append({**normalized, "reason": validation_error})
                continue

            position = diff_positions_by_file.get(normalized["file_path"], {}).get(normalized["line"])
            if not position:
                fallback_comments.append({**normalized, "reason": "No diff position found for line."})
                continue

            ready_comments.append({**normalized, "position": position})

        posted = self._post_ready_comments(
            repository=repository,
            pr_number=pr_number,
            commit_sha=commit_sha,
            pull_request_node_id=pull_request_node_id,
            ready_comments=ready_comments,
            fallback_comments=fallback_comments,
        )
        verified_posted = self._verify_posted_comments(repository, pr_number, posted)
        unverified = [
            item
            for item in posted
            if not self._posted_comment_key(item) in {self._posted_comment_key(v) for v in verified_posted}
        ]
        for item in unverified:
            fallback_comments.append(
                {
                    **item,
                    "reason": "GitHub API accepted the comment request, but the comment was not visible via the PR review comments API after verification.",
                }
            )

        success_summary_posted = False
        if verified_posted:
            success_summary_posted = self._post_success_summary(repository, pr_number, verified_posted)

        fallback_posted = False
        if fallback_comments:
            fallback_posted = self._post_fallback_comment(repository, pr_number, fallback_comments)

        return {
            "line_comments_requested": len(comments),
            "line_comments_posted": len(verified_posted),
            "fallback_comments": len(fallback_comments),
            "fallback_posted": fallback_posted,
            "success_summary_posted": success_summary_posted,
        }

    def _post_ready_comments(
        self,
        repository: str,
        pr_number: int,
        commit_sha: str,
        pull_request_node_id: str,
        ready_comments: list[dict[str, Any]],
        fallback_comments: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not ready_comments:
            return []

        posted: list[dict[str, Any]] = []
        rest_ready_comments: list[dict[str, Any]] = []
        for item in ready_comments:
            if not pull_request_node_id:
                rest_ready_comments.append(item)
                continue

            try:
                result = self._github_client.create_pull_request_review_thread(
                    pull_request_node_id=pull_request_node_id,
                    path=item["file_path"],
                    line=item["line"],
                    side=item["side"],
                    body=item["body"],
                )
                thread_id = self._extract_graphql_thread_id(result)
                print(
                    "GraphQL PR review thread accepted: "
                    f"path={item['file_path']}, line={item['line']}, "
                    f"thread_id_present={bool(thread_id)}"
                )
                posted.append(
                    {
                        **item,
                        "posted_via": "graphql_review_thread",
                        "graphql_thread_id": thread_id,
                    }
                )
            except Exception as exc:
                rest_ready_comments.append({**item, "graphql_error": str(exc)})

        if not rest_ready_comments:
            return posted

        review_comments = [
            {
                "path": item["file_path"],
                "line": item["line"],
                "side": item["side"],
                "body": item["body"],
            }
            for item in rest_ready_comments
        ]

        try:
            self._github_client.create_pull_request_review(
                repository=repository,
                pr_number=pr_number,
                commit_sha=commit_sha,
                comments=review_comments,
            )
            posted.extend(rest_ready_comments)
            return posted
        except GitHubApiError as exc:
            print(f"Warning: batch PR review comment creation with line/side failed: {exc}")

        position_review_comments = [
            {
                "path": item["file_path"],
                "position": item["position"],
                "body": item["body"],
            }
            for item in rest_ready_comments
        ]
        try:
            self._github_client.create_pull_request_review(
                repository=repository,
                pr_number=pr_number,
                commit_sha=commit_sha,
                comments=position_review_comments,
            )
            posted.extend(rest_ready_comments)
            return posted
        except GitHubApiError as exc:
            print(f"Warning: batch PR review comment creation with position failed: {exc}")

        for item in rest_ready_comments:
            try:
                self._github_client.create_pull_request_review_comment_by_position(
                    repository=repository,
                    pr_number=pr_number,
                    commit_sha=commit_sha,
                    path=item["file_path"],
                    position=item["position"],
                    body=item["body"],
                )
                posted.append(item)
            except GitHubApiError as exc:
                try:
                    self._github_client.create_pull_request_review_comment(
                        repository=repository,
                        pr_number=pr_number,
                        commit_sha=commit_sha,
                        path=item["file_path"],
                        line=item["line"],
                        side=item["side"],
                        body=item["body"],
                    )
                    posted.append({**item, "line_side_fallback": True})
                except Exception as fallback_exc:
                    fallback_comments.append(
                        {
                            **item,
                            "reason": (
                                f"GraphQL failed: {item.get('graphql_error', 'not attempted')}; "
                                f"review batch failed; position failed: {exc}; "
                                f"line/side failed: {fallback_exc}"
                            ),
                        }
                    )
            except Exception as exc:
                fallback_comments.append({**item, "reason": f"Unexpected error: {exc}"})

        return posted

    def _verify_posted_comments(
        self,
        repository: str,
        pr_number: int,
        posted_comments: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not posted_comments:
            return []

        graph_verified = [
            item
            for item in posted_comments
            if item.get("posted_via") == "graphql_review_thread"
        ]
        rest_candidates = [item for item in posted_comments if item not in graph_verified]
        if not rest_candidates:
            print(
                "PR comment verification: "
                f"posted_attempts={len(posted_comments)}, verified_visible={len(graph_verified)}"
            )
            return graph_verified

        time.sleep(2)
        try:
            github_comments = self._github_client.list_pull_request_review_comments(repository, pr_number)
        except Exception as exc:
            print(f"Warning: unable to verify PR review comments: {exc}")
            return graph_verified

        verified: list[dict[str, Any]] = list(graph_verified)
        for item in rest_candidates:
            if self._matching_github_comment_exists(item, github_comments):
                verified.append(item)

        print(
            "PR comment verification: "
            f"posted_attempts={len(posted_comments)}, verified_visible={len(verified)}"
        )
        return verified

    @staticmethod
    def _matching_github_comment_exists(
        posted_comment: dict[str, Any],
        github_comments: list[dict[str, Any]],
    ) -> bool:
        expected_path = posted_comment.get("file_path")
        expected_line = posted_comment.get("line")
        expected_body = str(posted_comment.get("body", "")).strip()

        for comment in github_comments:
            if comment.get("path") != expected_path:
                continue
            actual_body = str(comment.get("body", "")).strip()
            if actual_body != expected_body:
                continue

            possible_lines = {
                comment.get("line"),
                comment.get("original_line"),
            }
            normalized_lines = set()
            for line in possible_lines:
                try:
                    normalized_lines.add(int(line))
                except (TypeError, ValueError):
                    continue
            if expected_line in normalized_lines:
                return True

        return False

    @staticmethod
    def _posted_comment_key(comment: dict[str, Any]) -> tuple[str, int, str]:
        return (
            str(comment.get("file_path", "")),
            int(comment.get("line", 0) or 0),
            str(comment.get("body", "")).strip(),
        )

    @staticmethod
    def _extract_graphql_thread_id(result: dict[str, Any]) -> str:
        try:
            return str(result["data"]["addPullRequestReviewThread"]["thread"]["id"])
        except (KeyError, TypeError):
            pass

        try:
            return str(result["data"]["addPullRequestReviewThread"]["pullRequestReviewThread"]["id"])
        except (KeyError, TypeError):
            return ""

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
            position = item.get("position", "unknown position")
            body_lines.append(f"- `{location}:{line}`: {item['body']}")
            body_lines.append(f"  Diff position: {position}")
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

    def _post_success_summary(
        self,
        repository: str,
        pr_number: int,
        posted_comments: list[dict[str, Any]],
    ) -> bool:
        body_lines = [
            f"Automated PR review posted {len(posted_comments)} inline comment(s).",
            "",
            "Inline review comments are available in the PR Files changed tab.",
            "",
        ]
        for item in posted_comments[:20]:
            body_lines.append(f"- `{item['file_path']}:{item['line']}`")
        if len(posted_comments) > 20:
            body_lines.append(f"- {len(posted_comments) - 20} additional inline comments posted.")

        try:
            self._github_client.create_issue_comment(
                repository=repository,
                issue_number=pr_number,
                body="\n".join(body_lines),
            )
            return True
        except Exception as exc:
            print(f"Warning: failed to post PR review success summary: {exc}")
            return False
