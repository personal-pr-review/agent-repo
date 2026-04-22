from __future__ import annotations

from pathlib import Path

from docx import Document

from .models import ComparisonResult, PRMetadata, ReviewResult


class DocxGenerator:
    def generate(
        self,
        output_path: Path,
        pr_metadata: PRMetadata,
        comparisons: list[ComparisonResult],
        review_result: ReviewResult,
    ) -> None:
        document = Document()

        document.add_paragraph("PR Review & Change Summary Document")
        document.add_paragraph(
            "This document captures the detailed review of a pull request including changes, impact, and risks."
        )

        document.add_paragraph("1. Document Header")
        self._add_document_header_table(document, pr_metadata)

        document.add_paragraph("2. Executive Summary")
        document.add_paragraph("Purpose of this PR:")
        document.add_paragraph("[Explain why this PR was created]")
        document.add_paragraph("")
        document.add_paragraph("Summary of Changes:")
        document.add_paragraph("[Brief summary of key changes]")
        document.add_paragraph("")
        document.add_paragraph("Risk Level: [Low / Medium / High]")

        document.add_paragraph("3. PR Metadata")
        self._add_pr_metadata_table(document, pr_metadata)

        document.add_paragraph("4. Business / Functional Context")
        document.add_paragraph("Problem Being Solved:")
        document.add_paragraph("")
        document.add_paragraph("Expected Outcome:")
        document.add_paragraph("")

        document.add_paragraph("5. Scope of Review")
        document.add_paragraph("Reviewed Areas:")
        document.add_paragraph("- Code Logic")
        document.add_paragraph("- Security")
        document.add_paragraph("- Performance")
        document.add_paragraph("- Testing")
        document.add_paragraph("- Documentation")

        document.add_paragraph("6. Files Changed Summary")
        self._add_files_changed_table(document, comparisons)

        document.add_paragraph("7. What Changed From Existing Behavior")
        self._add_behavior_change_table(document, comparisons)

        document.add_paragraph("8. Final Recommendation")
        document.add_paragraph("Decision: [Merge / Do Not Merge]")
        document.add_paragraph("Reasoning:")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        document.save(str(output_path))

    @staticmethod
    def _add_document_header_table(document: Document, pr_metadata: PRMetadata) -> None:
        table = document.add_table(rows=10, cols=2)
        table.rows[0].cells[0].text = "Field"
        table.rows[0].cells[1].text = "Details"

        data = [
            ("Project / Repository", pr_metadata.repository),
            ("Module / Service", ""),
            ("PR Title", pr_metadata.title),
            ("PR Number / Link", f"{pr_metadata.pr_number} / {pr_metadata.html_url}"),
            ("Branch (Source \u2192 Target)", f"{pr_metadata.head_branch} \u2192 {pr_metadata.base_branch}"),
            ("Author", pr_metadata.author),
            ("Reviewer(s)", ""),
            ("Review Date", ""),
            ("Status", ""),
        ]

        for idx, (field, value) in enumerate(data, start=1):
            table.rows[idx].cells[0].text = field
            table.rows[idx].cells[1].text = value or ""

    @staticmethod
    def _add_pr_metadata_table(document: Document, pr_metadata: PRMetadata) -> None:
        table = document.add_table(rows=7, cols=2)
        table.rows[0].cells[0].text = "Metric"
        table.rows[0].cells[1].text = "Value"

        data = [
            ("Files Changed", str(pr_metadata.changed_files)),
            ("Lines Added", str(pr_metadata.additions)),
            ("Lines Removed", str(pr_metadata.deletions)),
            ("Commits", str(pr_metadata.commits)),
            ("Linked Ticket", pr_metadata.linked_ticket),
            ("Release/Sprint", pr_metadata.release_sprint),
        ]

        for idx, (metric, value) in enumerate(data, start=1):
            table.rows[idx].cells[0].text = metric
            table.rows[idx].cells[1].text = value or ""

    @staticmethod
    def _add_files_changed_table(document: Document, comparisons: list[ComparisonResult]) -> None:
        table = document.add_table(rows=1, cols=4)
        table.rows[0].cells[0].text = "File"
        table.rows[0].cells[1].text = "Change Type"
        table.rows[0].cells[2].text = "Summary"
        table.rows[0].cells[3].text = "Risk"

        for item in comparisons:
            row = table.add_row().cells
            row[0].text = item.file_path
            row[1].text = item.change_type
            row[2].text = item.change_summary
            row[3].text = item.risk_level

        blank_row = table.add_row().cells
        blank_row[0].text = ""
        blank_row[1].text = ""
        blank_row[2].text = ""
        blank_row[3].text = ""

    @staticmethod
    def _add_behavior_change_table(document: Document, comparisons: list[ComparisonResult]) -> None:
        table = document.add_table(rows=1, cols=5)
        table.rows[0].cells[0].text = "Area"
        table.rows[0].cells[1].text = "Existing Behavior"
        table.rows[0].cells[2].text = "New Behavior"
        table.rows[0].cells[3].text = "Reason"
        table.rows[0].cells[4].text = "Impact"

        for item in comparisons:
            row = table.add_row().cells
            row[0].text = item.file_path
            row[1].text = ""
            row[2].text = item.behavioral_change
            row[3].text = item.change_summary
            row[4].text = item.semantic_impact

        blank_row = table.add_row().cells
        blank_row[0].text = ""
        blank_row[1].text = ""
        blank_row[2].text = ""
        blank_row[3].text = ""
        blank_row[4].text = ""
