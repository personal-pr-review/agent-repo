from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class PRFileContext:
    path: str
    status: str
    additions: int
    deletions: int
    changes: int
    patch: str
    annotated_patch: str
    base_content: str
    head_content: str
    commentable_lines: list[int] = field(default_factory=list)
    added_lines: list[int] = field(default_factory=list)
    diff_positions_by_line: dict[int, int] = field(default_factory=dict)


@dataclass
class PRMetadata:
    repository: str
    pr_number: int
    title: str
    html_url: str
    author: str
    base_branch: str
    head_branch: str
    head_sha: str
    commits: int
    changed_files: int
    additions: int
    deletions: int
    linked_ticket: str = ""
    release_sprint: str = ""


@dataclass
class ComparisonResult:
    file_path: str
    change_type: str
    change_summary: str
    behavioral_change: str
    annotated_patch: str = ""
    commentable_lines: list[int] = field(default_factory=list)
    added_lines: list[int] = field(default_factory=list)
    diff_positions_by_line: dict[int, int] = field(default_factory=dict)
    risk_flags: list[str] = field(default_factory=list)
    semantic_impact: str = ""
    risk_level: str = "Low"


@dataclass
class ReviewResult:
    summary: str
    purpose_of_pr: str = ""
    summary_of_changes: str = ""
    problem_being_solved: str = ""
    expected_outcome: str = ""
    issues_found: list[dict[str, Any]] = field(default_factory=list)
    suggested_comments: list[dict[str, Any]] = field(default_factory=list)
    final_recommendation: str = "Merge"
    reasoning: str = ""
    risk_level: str = "Low"


@dataclass
class PipelineOutput:
    pr_metadata: PRMetadata
    comparison_results: list[ComparisonResult]
    review_result: ReviewResult
    comment_posting_result: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
