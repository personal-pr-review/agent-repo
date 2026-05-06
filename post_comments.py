from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from src.pr_review.comment_poster import PRCommentPoster
from src.pr_review.github_client import GitHubClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Post generated PR review comments to GitHub")
    parser.add_argument("--repository", required=True, help="owner/repo")
    parser.add_argument("--pr-number", required=True, type=int, help="Pull request number")
    parser.add_argument("--commit-sha", required=True, help="Head commit SHA")
    parser.add_argument(
        "--review-output",
        default="artifacts/review_output.json",
        help="Path to generated structured review output",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        print("Skipping PR comments: GITHUB_TOKEN is not available.", file=sys.stderr)
        return 0

    review_output_path = Path(args.review_output)
    if not review_output_path.exists():
        print(f"Skipping PR comments: review output not found at {review_output_path}.", file=sys.stderr)
        return 0

    try:
        payload = json.loads(review_output_path.read_text(encoding="utf-8"))
        result = post_comments_from_payload(
            payload=payload,
            token=token,
            repository=args.repository,
            pr_number=args.pr_number,
            commit_sha=args.commit_sha,
        )
        print(f"PR comment posting result: {json.dumps(result, ensure_ascii=False)}")
        return 0
    except Exception as exc:
        print(f"Warning: PR comment posting skipped after error: {exc}", file=sys.stderr)
        return 0


def post_comments_from_payload(
    payload: dict[str, Any],
    token: str,
    repository: str,
    pr_number: int,
    commit_sha: str,
) -> dict[str, Any]:
    review_result = payload.get("review_result", {})
    comments = review_result.get("suggested_comments", [])
    if not isinstance(comments, list):
        comments = []

    valid_lines_by_file: dict[str, set[int]] = {}
    diff_positions_by_file: dict[str, dict[int, int]] = {}
    for item in payload.get("comparison_results", []):
        if not isinstance(item, dict):
            continue
        file_path = str(item.get("file_path", "")).strip()
        if not file_path:
            continue
        valid_lines_by_file[file_path] = {
            int(line)
            for line in item.get("commentable_lines", [])
            if isinstance(line, int) or str(line).isdigit()
        }
        raw_positions = item.get("diff_positions_by_line", {})
        if isinstance(raw_positions, dict):
            positions: dict[int, int] = {}
            for line, position in raw_positions.items():
                try:
                    positions[int(line)] = int(position)
                except (TypeError, ValueError):
                    continue
            diff_positions_by_file[file_path] = positions

    github_client = GitHubClient(token)
    poster = PRCommentPoster(github_client)
    return poster.post_review_comments(
        repository=repository,
        pr_number=pr_number,
        commit_sha=commit_sha,
        comments=comments,
        valid_lines_by_file=valid_lines_by_file,
        diff_positions_by_file=diff_positions_by_file,
    )


if __name__ == "__main__":
    raise SystemExit(main())
