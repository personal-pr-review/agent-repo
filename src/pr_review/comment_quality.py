from __future__ import annotations

import re
from typing import Any


class ReviewCommentQualityGate:
    """Keep inline PR comments high-signal and practical."""

    MAX_INLINE_COMMENTS = 6
    MIN_BODY_CHARS = 45
    MAX_BODY_CHARS = 650

    _GENERIC_PATTERNS = (
        r"\bthis code can be improved\b",
        r"\bconsider improving\b",
        r"\bplease review\b",
        r"\blooks good\b",
        r"\bnit\b",
        r"\bnitpick\b",
        r"\bminor\b",
        r"\bstyle\b",
        r"\bformatting\b",
        r"\badd comments?\b",
        r"\badd documentation\b",
        r"\blogging the criteria\b",
        r"\bensure transparency\b",
        r"\btransparency in the review process\b",
    )

    _WEAK_SPECULATION_PATTERNS = (
        r"\bmaybe\b",
        r"\bpossibly\b",
        r"\bmight maybe\b",
        r"\bmight be beneficial\b",
        r"\bcould potentially\b",
        r"\bmay want to consider\b",
        r"\bit would be nice\b",
        r"\bnice to have\b",
    )

    _ACTION_TERMS = {
        "add",
        "avoid",
        "check",
        "ensure",
        "guard",
        "handle",
        "prevent",
        "return",
        "validate",
        "verify",
    }

    _RISK_TERMS = {
        "authorization",
        "bypass",
        "concurrent",
        "corrupt",
        "csrf",
        "data loss",
        "deadlock",
        "exception",
        "failure",
        "incorrect",
        "injection",
        "invalid",
        "leak",
        "malformed",
        "n+1",
        "null",
        "race",
        "regression",
        "risk",
        "security",
        "sql",
        "timeout",
        "transaction",
        "unbounded",
        "validation",
        "xss",
    }

    _REASON_PHRASES = (
        " because ",
        " otherwise ",
        " so that ",
        " without ",
        " to avoid ",
        " to ensure ",
        " to prevent ",
        " can cause ",
        " can lead ",
        " may allow ",
        " may cause ",
    )

    _SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}

    def filter(
        self,
        comments: list[dict[str, Any]],
        issues_found: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        deduped = self._dedupe(comments)
        issue_rank_by_file = self._issue_rank_by_file(issues_found)

        accepted: list[tuple[int, int, dict[str, Any]]] = []
        for index, comment in enumerate(deduped):
            if not self._is_high_signal_comment(comment):
                continue
            accepted.append((self._priority(comment, issue_rank_by_file), index, comment))

        accepted.sort(key=lambda item: (item[0], item[1]))
        return [item[2] for item in accepted[: self.MAX_INLINE_COMMENTS]]

    def _is_high_signal_comment(self, comment: dict[str, Any]) -> bool:
        body = str(comment.get("body", "")).strip()
        normalized = self._normalize_text(body)

        if len(body) < self.MIN_BODY_CHARS or len(body) > self.MAX_BODY_CHARS:
            return False
        if self._matches_any(normalized, self._GENERIC_PATTERNS):
            return False
        if self._matches_any(normalized, self._WEAK_SPECULATION_PATTERNS):
            return False

        return self._has_action(normalized) and self._has_risk_or_reason(normalized)

    def _priority(self, comment: dict[str, Any], issue_rank_by_file: dict[str, int]) -> int:
        body = self._normalize_text(str(comment.get("body", "")))
        file_path = str(comment.get("file_path", "")).strip()
        issue_rank = issue_rank_by_file.get(file_path, 3)

        if any(term in body for term in ("security", "authorization", "injection", "xss", "csrf", "secret")):
            return min(issue_rank, 0)
        if any(term in body for term in ("incorrect", "failure", "exception", "data loss", "corrupt")):
            return min(issue_rank, 1)
        if any(term in body for term in ("race", "concurrent", "deadlock", "transaction")):
            return min(issue_rank, 1)
        return issue_rank

    def _has_action(self, normalized: str) -> bool:
        words = set(re.findall(r"[a-z0-9]+", normalized))
        return bool(words.intersection(self._ACTION_TERMS))

    def _has_risk_or_reason(self, normalized: str) -> bool:
        if any(term in normalized for term in self._RISK_TERMS):
            return True
        return any(phrase in f" {normalized} " for phrase in self._REASON_PHRASES)

    def _issue_rank_by_file(self, issues_found: list[dict[str, Any]]) -> dict[str, int]:
        ranks: dict[str, int] = {}
        for issue in issues_found:
            file_path = str(issue.get("file_path", "")).strip()
            severity = str(issue.get("severity", "")).strip().lower()
            rank = self._SEVERITY_RANK.get(severity, 3)
            if file_path and rank < ranks.get(file_path, 3):
                ranks[file_path] = rank
        return ranks

    def _dedupe(self, comments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[tuple[str, int, str]] = set()
        output: list[dict[str, Any]] = []
        for comment in comments:
            key = (
                str(comment.get("file_path", "")).strip(),
                int(comment.get("line", 0) or 0),
                self._normalize_text(str(comment.get("body", ""))),
            )
            if key in seen:
                continue
            seen.add(key)
            output.append(comment)
        return output

    @staticmethod
    def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
        return any(re.search(pattern, text) for pattern in patterns)

    @staticmethod
    def _normalize_text(text: str) -> str:
        return re.sub(r"\s+", " ", text.lower()).strip()


class ReviewIssueQualityGate:
    """Keep issue summaries useful enough for the final report."""

    MAX_ISSUES = 10
    MIN_TEXT_CHARS = 25
    _SEVERITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}

    _LOW_VALUE_PATTERNS = (
        r"\bconsider logging the criteria\b",
        r"\bensure transparency\b",
        r"\bthis could be improved\b",
        r"\bcode quality\b",
        r"\bgeneral maintainability\b",
        r"\badd documentation\b",
        r"\bminor\b",
        r"\bnit\b",
        r"\bstyle\b",
    )

    _WEAK_SPECULATION_PATTERNS = (
        r"\bmaybe\b",
        r"\bpossibly\b",
        r"\bcould potentially\b",
        r"\bmight be beneficial\b",
        r"\bmay want to consider\b",
        r"\bnice to have\b",
    )

    _MATERIAL_RISK_TERMS = {
        "authorization",
        "backward compatibility",
        "bypass",
        "concurrency",
        "contract",
        "corrupt",
        "data integrity",
        "data loss",
        "deadlock",
        "exception",
        "failure",
        "idempotency",
        "incorrect",
        "injection",
        "invalid",
        "leak",
        "malformed",
        "migration",
        "n+1",
        "null",
        "permission",
        "race",
        "regression",
        "security",
        "timeout",
        "transaction",
        "validation",
        "xss",
    }

    def filter(self, issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized = [item for item in (self._normalize_issue(issue) for issue in issues) if item]
        deduped = self._dedupe(normalized)
        filtered = [issue for issue in deduped if self._is_high_signal_issue(issue)]
        filtered.sort(key=lambda item: self._SEVERITY_ORDER[item["severity"]])
        return filtered[: self.MAX_ISSUES]

    def _normalize_issue(self, issue: dict[str, Any]) -> dict[str, Any] | None:
        if not isinstance(issue, dict):
            return None

        severity = str(issue.get("severity", "Low")).strip().capitalize()
        if severity not in self._SEVERITY_ORDER:
            severity = "Low"

        normalized = {
            "severity": severity,
            "file_path": str(issue.get("file_path", "")).strip(),
            "issue": str(issue.get("issue", "")).strip(),
            "recommendation": str(issue.get("recommendation", "")).strip(),
        }
        if not normalized["issue"] or not normalized["recommendation"]:
            return None
        return normalized

    def _is_high_signal_issue(self, issue: dict[str, Any]) -> bool:
        combined = self._normalize_text(f"{issue['issue']} {issue['recommendation']}")
        if len(combined) < self.MIN_TEXT_CHARS:
            return False
        if self._matches_any(combined, self._LOW_VALUE_PATTERNS):
            return False
        if self._matches_any(combined, self._WEAK_SPECULATION_PATTERNS):
            return False
        if issue["severity"] in {"High", "Medium"}:
            return True
        return any(term in combined for term in self._MATERIAL_RISK_TERMS)

    def _dedupe(self, issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[tuple[str, str]] = set()
        output: list[dict[str, Any]] = []
        for issue in issues:
            key = (
                issue["file_path"],
                self._normalize_text(issue["issue"]),
            )
            if key in seen:
                continue
            seen.add(key)
            output.append(issue)
        return output

    @staticmethod
    def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
        return any(re.search(pattern, text) for pattern in patterns)

    @staticmethod
    def _normalize_text(text: str) -> str:
        return re.sub(r"\s+", " ", text.lower()).strip()
