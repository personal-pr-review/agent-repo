from __future__ import annotations

import base64
from typing import Any

import requests

from .diff_utils import annotate_patch_with_target_lines
from .models import PRFileContext, PRMetadata


class GitHubApiError(RuntimeError):
    pass


class GitHubClient:
    def __init__(self, token: str, timeout_seconds: int = 30) -> None:
        self._timeout = timeout_seconds
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "centralized-pr-review-agent",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )

    def _request(self, method: str, url: str, **kwargs: Any) -> Any:
        response = self._session.request(method, url, timeout=self._timeout, **kwargs)
        if response.status_code >= 400:
            raise GitHubApiError(
                f"GitHub API error {response.status_code} for {url}: {response.text[:500]}"
            )
        if response.status_code == 204:
            return None
        return response.json()

    def get_pull_request(self, repository: str, pr_number: int) -> dict[str, Any]:
        url = f"https://api.github.com/repos/{repository}/pulls/{pr_number}"
        return self._request("GET", url)

    def create_pull_request_review_comment(
        self,
        repository: str,
        pr_number: int,
        commit_sha: str,
        path: str,
        line: int,
        side: str,
        body: str,
    ) -> dict[str, Any]:
        url = f"https://api.github.com/repos/{repository}/pulls/{pr_number}/comments"
        payload = {
            "body": body,
            "commit_id": commit_sha,
            "path": path,
            "line": line,
            "side": side,
        }
        return self._request("POST", url, json=payload)

    def create_pull_request_review_comment_by_position(
        self,
        repository: str,
        pr_number: int,
        commit_sha: str,
        path: str,
        position: int,
        body: str,
    ) -> dict[str, Any]:
        url = f"https://api.github.com/repos/{repository}/pulls/{pr_number}/comments"
        payload = {
            "body": body,
            "commit_id": commit_sha,
            "path": path,
            "position": position,
        }
        return self._request("POST", url, json=payload)

    def create_pull_request_review(
        self,
        repository: str,
        pr_number: int,
        commit_sha: str,
        comments: list[dict[str, Any]],
        body: str = "Automated PR review comments",
    ) -> dict[str, Any]:
        url = f"https://api.github.com/repos/{repository}/pulls/{pr_number}/reviews"
        payload = {
            "commit_id": commit_sha,
            "event": "COMMENT",
            "body": body,
            "comments": comments,
        }
        return self._request("POST", url, json=payload)

    def create_issue_comment(self, repository: str, issue_number: int, body: str) -> dict[str, Any]:
        url = f"https://api.github.com/repos/{repository}/issues/{issue_number}/comments"
        return self._request("POST", url, json={"body": body})

    def get_pull_request_files(self, repository: str, pr_number: int) -> list[dict[str, Any]]:
        files: list[dict[str, Any]] = []
        page = 1
        while True:
            url = f"https://api.github.com/repos/{repository}/pulls/{pr_number}/files"
            data = self._request("GET", url, params={"per_page": 100, "page": page})
            if not data:
                break
            files.extend(data)
            page += 1
        return files

    def get_file_content(self, repository: str, file_path: str, ref: str) -> str:
        url = f"https://api.github.com/repos/{repository}/contents/{file_path}"
        try:
            payload = self._request("GET", url, params={"ref": ref})
        except GitHubApiError as exc:
            # For removed files, renamed edge cases, or binary content not available.
            if "404" in str(exc):
                return ""
            raise

        if isinstance(payload, list):
            return ""

        encoded = payload.get("content", "")
        if not encoded:
            return ""

        try:
            decoded = base64.b64decode(encoded).decode("utf-8", errors="replace")
        except Exception:
            return ""
        return decoded

    def collect_pr_context(
        self,
        repository: str,
        pr_number: int,
        base_branch: str,
        head_branch: str,
        head_ref: str,
    ) -> tuple[PRMetadata, list[PRFileContext]]:
        pr = self.get_pull_request(repository, pr_number)
        files = self.get_pull_request_files(repository, pr_number)

        metadata = PRMetadata(
            repository=repository,
            pr_number=pr_number,
            title=pr.get("title", ""),
            html_url=pr.get("html_url", ""),
            author=(pr.get("user") or {}).get("login", ""),
            base_branch=base_branch,
            head_branch=head_branch,
            head_sha=head_ref or ((pr.get("head") or {}).get("sha", "")),
            commits=int(pr.get("commits", 0) or 0),
            changed_files=int(pr.get("changed_files", 0) or 0),
            additions=int(pr.get("additions", 0) or 0),
            deletions=int(pr.get("deletions", 0) or 0),
        )

        contexts: list[PRFileContext] = []
        for file_data in files:
            path = file_data.get("filename", "")
            status = file_data.get("status", "modified")
            patch = file_data.get("patch", "") or ""
            annotated_diff = annotate_patch_with_target_lines(patch)

            base_content = ""
            head_content = ""
            if status != "added":
                base_content = self.get_file_content(repository, path, base_branch)
            if status != "removed":
                head_content = self.get_file_content(repository, path, head_ref or head_branch)

            contexts.append(
                PRFileContext(
                    path=path,
                    status=status,
                    additions=int(file_data.get("additions", 0) or 0),
                    deletions=int(file_data.get("deletions", 0) or 0),
                    changes=int(file_data.get("changes", 0) or 0),
                    patch=patch,
                    annotated_patch=annotated_diff.text,
                    commentable_lines=annotated_diff.commentable_lines,
                    added_lines=annotated_diff.added_lines,
                    diff_positions_by_line=annotated_diff.diff_positions_by_line,
                    base_content=base_content,
                    head_content=head_content,
                )
            )

        return metadata, contexts
