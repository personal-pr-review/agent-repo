from __future__ import annotations

import re
from dataclasses import dataclass, field


HUNK_HEADER_RE = re.compile(
    r"^@@ -(?P<old_start>\d+)(?:,(?P<old_count>\d+))? "
    r"\+(?P<new_start>\d+)(?:,(?P<new_count>\d+))? @@"
)


@dataclass(frozen=True)
class AnnotatedDiff:
    text: str
    commentable_lines: list[int] = field(default_factory=list)
    added_lines: list[int] = field(default_factory=list)
    diff_positions_by_line: dict[int, int] = field(default_factory=dict)


def annotate_patch_with_target_lines(patch: str) -> AnnotatedDiff:
    if not patch:
        return AnnotatedDiff(text="", commentable_lines=[], added_lines=[])

    old_line: int | None = None
    new_line: int | None = None
    annotated_lines: list[str] = []
    commentable_lines: set[int] = set()
    added_lines: set[int] = set()
    diff_positions_by_line: dict[int, int] = {}
    diff_position = 0

    for raw_line in patch.splitlines():
        hunk_match = HUNK_HEADER_RE.match(raw_line)
        if hunk_match:
            old_line = int(hunk_match.group("old_start"))
            new_line = int(hunk_match.group("new_start"))
            annotated_lines.append(raw_line)
            continue

        if old_line is None or new_line is None:
            annotated_lines.append(raw_line)
            continue

        if raw_line.startswith("\\ No newline"):
            annotated_lines.append(raw_line)
            continue

        prefix = raw_line[:1] if raw_line else " "
        if prefix == "+":
            diff_position += 1
            annotated_lines.append(f"[LINE:{new_line}] {raw_line}")
            commentable_lines.add(new_line)
            added_lines.add(new_line)
            diff_positions_by_line[new_line] = diff_position
            new_line += 1
        elif prefix == "-":
            diff_position += 1
            annotated_lines.append(f"[OLD_LINE:{old_line}] {raw_line}")
            old_line += 1
        elif prefix == " ":
            diff_position += 1
            annotated_lines.append(f"[LINE:{new_line}] {raw_line}")
            commentable_lines.add(new_line)
            diff_positions_by_line[new_line] = diff_position
            old_line += 1
            new_line += 1
        else:
            annotated_lines.append(raw_line)

    return AnnotatedDiff(
        text="\n".join(annotated_lines),
        commentable_lines=sorted(commentable_lines),
        added_lines=sorted(added_lines),
        diff_positions_by_line=diff_positions_by_line,
    )
