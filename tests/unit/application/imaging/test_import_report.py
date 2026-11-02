"""Tests for ImportReport and ImportIssue."""

from __future__ import annotations

import pytest

from cranioz.application.imaging.import_report import (
    ImportIssue,
    ImportReport,
    IssueSeverity,
)


def _issue(severity: IssueSeverity, code: str = "test", message: str = "msg") -> ImportIssue:
    return ImportIssue(severity=severity, code=code, message=message)


def test_issue_holds_fields() -> None:
    issue = _issue(IssueSeverity.ERROR, code="x", message="y")
    assert issue.severity is IssueSeverity.ERROR
    assert issue.code == "x"
    assert issue.message == "y"


def test_issue_empty_code_raises() -> None:
    with pytest.raises(ValueError, match="code"):
        _issue(IssueSeverity.ERROR, code="")


def test_issue_empty_message_raises() -> None:
    with pytest.raises(ValueError, match="message"):
        _issue(IssueSeverity.ERROR, message="")


def test_report_has_errors() -> None:
    report = ImportReport(
        success=False,
        files_detected=10,
        instances_loaded=0,
        instances_skipped=10,
        modality="CT",
        transfer_syntax=None,
        dimensions=None,
        spacing=None,
        intensity_scale=None,
        issues=(_issue(IssueSeverity.ERROR),),
    )
    assert report.has_errors is True
    assert report.has_warnings is False


def test_report_has_warnings() -> None:
    report = ImportReport(
        success=True,
        files_detected=10,
        instances_loaded=10,
        instances_skipped=0,
        modality="CT",
        transfer_syntax=None,
        dimensions=(10, 10, 10),
        spacing=(1.0, 1.0, 1.0),
        intensity_scale="hu",
        issues=(_issue(IssueSeverity.WARNING),),
    )
    assert report.has_errors is False
    assert report.has_warnings is True


def test_issues_by_severity() -> None:
    issues = (
        _issue(IssueSeverity.ERROR, code="e1"),
        _issue(IssueSeverity.WARNING, code="w1"),
        _issue(IssueSeverity.WARNING, code="w2"),
        _issue(IssueSeverity.INFO, code="i1"),
    )
    report = ImportReport(
        success=False,
        files_detected=1,
        instances_loaded=1,
        instances_skipped=0,
        modality="CT",
        transfer_syntax=None,
        dimensions=None,
        spacing=None,
        intensity_scale=None,
        issues=issues,
    )
    assert len(report.issues_by_severity(IssueSeverity.ERROR)) == 1
    assert len(report.issues_by_severity(IssueSeverity.WARNING)) == 2
    assert len(report.issues_by_severity(IssueSeverity.INFO)) == 1


def test_summary_contains_key_fields() -> None:
    report = ImportReport(
        success=True,
        files_detected=3,
        instances_loaded=3,
        instances_skipped=0,
        modality="CT",
        transfer_syntax=None,
        dimensions=(10, 10, 10),
        spacing=(1.0, 1.0, 1.0),
        intensity_scale="hu",
        issues=(),
    )
    text = report.summary()
    assert "files=3" in text
    assert "modality=CT" in text
    assert "scale=hu" in text
