from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.pr_review.config import AppConfig
from src.pr_review.github_client import GitHubClient
from src.pr_review.llm_client import LLMClient
from src.pr_review.pipeline import PRReviewPipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Centralized PR review pipeline")
    parser.add_argument("--repository", required=True, help="owner/repo")
    parser.add_argument("--pr-number", required=True, type=int, help="Pull request number")
    parser.add_argument("--base-branch", required=True, help="Base branch")
    parser.add_argument("--head-branch", required=True, help="Head branch")
    parser.add_argument("--commit-sha", required=True, help="Head commit SHA")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        config = AppConfig.from_env()
        github_client = GitHubClient(config.github_token)
        llm_client = LLMClient(
            api_key=config.llm_api_key,
            base_url=config.llm_api_url,
            model=config.llm_model,
        )

        pipeline = PRReviewPipeline(
            github_client=github_client,
            llm_client=llm_client,
            prompts_dir=Path("src/pr_review/prompt_templates"),
            template_path=Path("templates/Detailed_PR_Review_Template.docx"),
        )

        output_docx_path = Path("artifacts/pr_review_report.docx")
        output_json_path = Path("artifacts/review_output.json")

        pipeline.run(
            repository=args.repository,
            pr_number=args.pr_number,
            base_branch=args.base_branch,
            head_branch=args.head_branch,
            commit_sha=args.commit_sha,
            output_docx_path=output_docx_path,
            output_json_path=output_json_path,
        )

        print(f"Review complete. DOCX: {output_docx_path}; JSON: {output_json_path}")
        return 0
    except Exception as exc:
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
