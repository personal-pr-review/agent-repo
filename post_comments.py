from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from src.pr_review.comment_poster import PRCommentPoster
from src.pr_review.diff_utils import annotate_patch_with_target_lines
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
    github_client = GitHubClient(token)
    pr = github_client.get_pull_request(repository, pr_number)
    pr_head_sha = ((pr.get("head") or {}).get("sha") or "").strip()
    review_commit_sha = pr_head_sha or commit_sha

    review_result = payload.get("review_result", {})
    comments = review_result.get("suggested_comments", [])
    if not isinstance(comments, list):
        comments = []

    valid_lines_by_file, diff_positions_by_file = build_live_diff_maps(github_client, repository, pr_number)

    poster = PRCommentPoster(github_client)
    return poster.post_review_comments(
        repository=repository,
        pr_number=pr_number,
        commit_sha=review_commit_sha,
        comments=comments,
        valid_lines_by_file=valid_lines_by_file,
        diff_positions_by_file=diff_positions_by_file,
    )


def build_live_diff_maps(
    github_client: GitHubClient,
    repository: str,
    pr_number: int,
) -> tuple[dict[str, set[int]], dict[str, dict[int, int]]]:
    valid_lines_by_file: dict[str, set[int]] = {}
    diff_positions_by_file: dict[str, dict[int, int]] = {}

    for file_data in github_client.get_pull_request_files(repository, pr_number):
        path = str(file_data.get("filename", "")).strip()
        if not path:
            continue

        status = str(file_data.get("status", "")).strip()
        if status == "removed":
            continue

        annotated_diff = annotate_patch_with_target_lines(file_data.get("patch", "") or "")
        valid_lines_by_file[path] = set(annotated_diff.added_lines or annotated_diff.commentable_lines)
        diff_positions_by_file[path] = annotated_diff.diff_positions_by_line

    print(
        "Live PR comment map: "
        f"files={len(valid_lines_by_file)}, "
        f"commentable_lines={sum(len(lines) for lines in valid_lines_by_file.values())}"
    )
    return valid_lines_by_file, diff_positions_by_file


if __name__ == "__main__":
    raise SystemExit(main())
