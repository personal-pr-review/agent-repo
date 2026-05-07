from __future__ import annotations

from collections import Counter
from pathlib import PurePosixPath
from typing import Any

from .models import ComparisonResult, PRMetadata


class ReviewFocusBuilder:
    """Build compact deterministic signals that help the LLM review like a senior engineer."""

    _RISK_ORDER = {"High": 3, "Medium": 2, "Low": 1}

    _CATEGORY_PATTERNS = {
        "security_or_auth": ("auth", "oauth", "jwt", "permission", "policy", "security", "secret"),
        "data_or_persistence": ("migration", "schema", "repository", "dao", "model", "entity", "database", "sql"),
        "api_or_contract": ("api", "controller", "route", "endpoint", "dto", "schema", "contract"),
        "config_or_ci": (".github/", "workflow", "dockerfile", "helm", "k8s", "config", "settings", ".yml", ".yaml"),
        "tests": ("test", "tests", "spec", "__tests__"),
        "docs": ("readme", "docs/", ".md"),
        "dependencies": (
            "requirements.txt",
            "pyproject.toml",
            "package.json",
            "pom.xml",
            ".csproj",
            "build.gradle",
        ),
    }

    def build(self, pr_metadata: PRMetadata, comparisons: list[ComparisonResult]) -> dict[str, Any]:
        categories = self._categories(comparisons)
        max_file_risk = self._max_file_risk(comparisons)
        risk_flags = [flag for item in comparisons for flag in item.risk_flags if str(flag).strip()]
        runtime_files = [
            item.file_path
            for item in comparisons
            if not self._has_category(item.file_path, "tests") and not self._has_category(item.file_path, "docs")
        ]

        priorities = self._priorities(
            categories=categories,
            risk_flags=risk_flags,
            max_file_risk=max_file_risk,
            pr_metadata=pr_metadata,
            runtime_file_count=len(runtime_files),
        )

        return {
            "change_size": {
                "files_changed": pr_metadata.changed_files,
                "additions": pr_metadata.additions,
                "deletions": pr_metadata.deletions,
                "is_large_change": pr_metadata.changed_files >= 12
                or pr_metadata.additions + pr_metadata.deletions >= 500,
            },
            "max_file_risk": max_file_risk,
            "risk_flag_count": len(risk_flags),
            "file_categories": dict(categories),
            "runtime_file_count": len(runtime_files),
            "tests_changed": categories.get("tests", 0) > 0,
            "docs_only": bool(comparisons) and len(runtime_files) == 0,
            "review_priorities": priorities,
            "review_guidance": self._guidance(priorities),
        }

    def _priorities(
        self,
        categories: Counter[str],
        risk_flags: list[str],
        max_file_risk: str,
        pr_metadata: PRMetadata,
        runtime_file_count: int,
    ) -> list[str]:
        priorities: list[str] = []

        if categories.get("security_or_auth"):
            priorities.append("Prioritize authorization, authentication, secret handling, and privilege boundaries.")
        if categories.get("data_or_persistence"):
            priorities.append("Prioritize data integrity, migrations, transaction boundaries, and backward compatibility.")
        if categories.get("api_or_contract"):
            priorities.append("Prioritize request validation, response contracts, compatibility, and error behavior.")
        if categories.get("config_or_ci"):
            priorities.append("Prioritize safe defaults, deployment impact, permissions, and environment-specific behavior.")
        if categories.get("dependencies"):
            priorities.append("Prioritize dependency security, version compatibility, and lockfile consistency.")
        if max_file_risk == "High" or risk_flags:
            priorities.append("Inspect comparison-agent risk flags closely and only escalate supported high-confidence risks.")
        if runtime_file_count > 0 and not categories.get("tests") and pr_metadata.additions + pr_metadata.deletions > 30:
            priorities.append("Check whether changed runtime behavior has meaningful test coverage.")
        if not priorities:
            priorities.append("Focus on correctness and only comment when the diff introduces a practical risk.")

        return priorities[:6]

    def _categories(self, comparisons: list[ComparisonResult]) -> Counter[str]:
        categories: Counter[str] = Counter()
        for item in comparisons:
            for category in self._CATEGORY_PATTERNS:
                if self._has_category(item.file_path, category):
                    categories[category] += 1
        return categories

    def _max_file_risk(self, comparisons: list[ComparisonResult]) -> str:
        max_level = "Low"
        for item in comparisons:
            normalized = self._normalize_risk_level(item.risk_level)
            if self._RISK_ORDER[normalized] > self._RISK_ORDER[max_level]:
                max_level = normalized
        return max_level

    def _has_category(self, file_path: str, category: str) -> bool:
        normalized = file_path.replace("\\", "/").lower()
        name = PurePosixPath(normalized).name
        return any(pattern in normalized or pattern in name for pattern in self._CATEGORY_PATTERNS[category])

    @classmethod
    def _normalize_risk_level(cls, value: str) -> str:
        normalized = str(value or "").strip().capitalize()
        return normalized if normalized in cls._RISK_ORDER else "Low"

    @staticmethod
    def _guidance(priorities: list[str]) -> str:
        return (
            "Use these deterministic signals to focus the review. They are not findings by themselves; "
            "only raise issues when the changed diff provides concrete evidence."
        )
