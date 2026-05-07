from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .framework_detector import FrameworkDetectionResult, FrameworkDetector


@dataclass(frozen=True)
class RulebookDefinition:
    key: str
    display_name: str
    relative_path: Path


@dataclass(frozen=True)
class RulebookContext:
    selected_rulebooks: list[str]
    detected_ecosystems: list[str]
    selection_reason: dict[str, list[str]]
    content: str

    def to_dict(self) -> dict[str, object]:
        return {
            "selected_rulebooks": self.selected_rulebooks,
            "detected_ecosystems": self.detected_ecosystems,
            "selection_reason": self.selection_reason,
        }


class RulebookLoader:
    """Load only the review rulebooks relevant to the files changed in a PR."""

    _RULEBOOKS = {
        "common": RulebookDefinition("common", "Common Review Rules", Path("common/common_rules.md")),
        "python": RulebookDefinition("python", "Python Review Rules", Path("python/python_rules.md")),
        "typescript_angular": RulebookDefinition(
            "typescript_angular",
            "TypeScript / Angular Review Rules",
            Path("typescript/typescript_angular_rules.md"),
        ),
        "dotnet": RulebookDefinition("dotnet", ".NET / C# Review Rules", Path("dotnet/dotnet_rules.md")),
        "java_springboot": RulebookDefinition(
            "java_springboot",
            "Java / Spring Boot Review Rules",
            Path("java/java_springboot_rules.md"),
        ),
    }

    def __init__(
        self,
        rules_root: Path,
        detector: FrameworkDetector | None = None,
        max_rulebook_chars: int = 14000,
    ) -> None:
        self._rules_root = rules_root
        self._detector = detector or FrameworkDetector()
        self._max_rulebook_chars = max_rulebook_chars

    def load_for_files(self, changed_files: Iterable[str]) -> RulebookContext:
        detection = self._detector.detect(changed_files)
        selected_keys = ["common", *detection.ecosystems]

        selected_names: list[str] = []
        content_blocks: list[str] = []
        seen_rules: set[str] = set()

        for key in selected_keys:
            definition = self._RULEBOOKS.get(key)
            if not definition:
                continue

            raw_content = self._read_rulebook(definition)
            if not raw_content:
                continue

            selected_names.append(definition.display_name)
            cleaned_content = self._compact_and_dedupe_markdown(raw_content, seen_rules)
            if cleaned_content:
                content_blocks.append(f"# {definition.display_name}\n{cleaned_content}")

        merged_content = self._trim_to_budget("\n\n".join(content_blocks))
        return RulebookContext(
            selected_rulebooks=selected_names,
            detected_ecosystems=detection.ecosystems,
            selection_reason=self._selection_reason(detection),
            content=merged_content,
        )

    def _read_rulebook(self, definition: RulebookDefinition) -> str:
        path = self._rules_root / definition.relative_path
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8").strip()

    def _compact_and_dedupe_markdown(self, content: str, seen_rules: set[str]) -> str:
        output_lines: list[str] = []
        previous_blank = False

        for raw_line in content.splitlines():
            line = raw_line.rstrip()
            stripped = line.strip()

            if not stripped:
                if output_lines and not previous_blank:
                    output_lines.append("")
                previous_blank = True
                continue

            previous_blank = False
            if stripped.startswith("- "):
                rule_key = self._rule_key(stripped)
                if rule_key in seen_rules:
                    continue
                seen_rules.add(rule_key)

            output_lines.append(line)

        return "\n".join(output_lines).strip()

    def _trim_to_budget(self, content: str) -> str:
        if len(content) <= self._max_rulebook_chars:
            return content

        trimmed = content[: self._max_rulebook_chars]
        last_section = trimmed.rfind("\n# ")
        if last_section > self._max_rulebook_chars * 0.6:
            trimmed = trimmed[:last_section]
        return (
            trimmed.rstrip()
            + "\n\n[Rulebook context trimmed to stay within the configured token budget.]"
        )

    @staticmethod
    def _rule_key(rule_line: str) -> str:
        without_id = re.sub(r"^-\s+\[[^\]]+\]\s*", "", rule_line)
        normalized = re.sub(r"[^a-z0-9]+", " ", without_id.lower()).strip()
        return normalized

    @staticmethod
    def _selection_reason(detection: FrameworkDetectionResult) -> dict[str, list[str]]:
        reasons: dict[str, list[str]] = {"common": ["Loaded for every PR."]}
        reasons.update(detection.signals)
        return reasons
