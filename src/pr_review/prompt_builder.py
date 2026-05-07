from __future__ import annotations

from .rulebook_loader import RulebookContext


class PromptBuilder:
    """Compose LLM prompts with dynamic rulebook context."""

    def build_review_prompt(self, base_prompt: str, rulebook_context: RulebookContext | None) -> str:
        base = base_prompt.strip()
        if not rulebook_context or not rulebook_context.content.strip():
            return base

        selected = ", ".join(rulebook_context.selected_rulebooks)
        return "\n\n".join(
            [
                base,
                "Dynamic Review Rulebooks",
                (
                    "The following rulebooks were selected from the PR changed files. "
                    "Apply these rules when they are relevant to the actual diff. "
                    "Do not penalize code for unrelated ecosystems or unchanged legacy code. "
                    "Prefer high-signal correctness, security, reliability, and maintainability feedback."
                ),
                f"Selected rulebooks: {selected}",
                rulebook_context.content.strip(),
                (
                    "Rulebook application guidance:\n"
                    "- Use rulebooks to judge risk and generate issues_found.\n"
                    "- Cross-check rulebook concerns against review_focus and comparison_results before raising them.\n"
                    "- Generate suggested_comments only for concrete violations anchored to valid [LINE:nnn] markers.\n"
                    "- Avoid noisy style-only comments unless they create a real correctness, security, or maintenance risk.\n"
                    "- Do not force comments for clean, low-risk PRs; returning an empty suggested_comments array is acceptable.\n"
                    "- Favor security, correctness, data integrity, concurrency, architecture, and non-trivial performance risks over minor improvements.\n"
                    "- If framework evidence is weak, treat framework-specific rules as advisory rather than mandatory."
                ),
            ]
        )
