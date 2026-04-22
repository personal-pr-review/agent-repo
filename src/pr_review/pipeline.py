from __future__ import annotations

from pathlib import Path

from .comparison_agent import ComparisonAgent
from .docx_generator import DocxGenerator
from .github_client import GitHubClient
from .llm_client import LLMClient
from .models import PipelineOutput
from .review_agent import ReviewAgent


class PRReviewPipeline:
    def __init__(self, github_client: GitHubClient, llm_client: LLMClient, prompts_dir: Path) -> None:
        self._github_client = github_client
        self._comparison_agent = ComparisonAgent(llm_client, prompts_dir / "comparison_prompt.txt")
        self._review_agent = ReviewAgent(llm_client, prompts_dir / "review_prompt.txt")
        self._docx_generator = DocxGenerator()

    def run(
        self,
        repository: str,
        pr_number: int,
        base_branch: str,
        head_branch: str,
        commit_sha: str,
        output_docx_path: Path,
        output_json_path: Path,
    ) -> PipelineOutput:
        pr_metadata, file_contexts = self._github_client.collect_pr_context(
            repository=repository,
            pr_number=pr_number,
            base_branch=base_branch,
            head_branch=head_branch,
            head_ref=commit_sha,
        )

        comparison_results = [self._comparison_agent.run_for_file(item) for item in file_contexts]
        review_result = self._review_agent.run(pr_metadata, comparison_results)

        output = PipelineOutput(
            pr_metadata=pr_metadata,
            comparison_results=comparison_results,
            review_result=review_result,
        )

        self._docx_generator.generate(output_docx_path, pr_metadata, comparison_results, review_result)

        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        output_json_path.write_text(
            __import__("json").dumps(output.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        return output
