"""
Tests for unified_analyzer.UnifiedCodeAnalyzer._extract_issues.

These tests pin the function's CURRENT behavior — quirks included — so
the Tier A refactor (structured issue contract via AutoGen function-
calling) has a regression net. Where current behavior surprises, the
test still asserts what the code does today; Tier A will revisit.

The xfail in test 9 documents a real format-drift failure mode.
"""

import pytest

from unified_analyzer import UnifiedCodeAnalyzer


def make_review(messages):
    """Build a review dict from a list of (speaker, content) tuples."""
    return {
        "conversation": [
            {"speaker": speaker, "content": content}
            for speaker, content in messages
        ]
    }


def issue_block(issue_type, line, description, severity):
    """Render an issue in the canonical dash-prefix format the agents are told to emit."""
    return "\n".join(
        [
            f"- Issue type: {issue_type}",
            f"- Line number: {line}",
            f"- Description: {description}",
            f"- Severity: {severity}",
        ]
    )


@pytest.fixture
def analyzer():
    return UnifiedCodeAnalyzer()


def test_happy_path_three_agents(analyzer):
    review = make_review(
        [
            ("CodeAnalyzer", issue_block("smell", 10, "Function is too long", "Medium")),
            ("SecurityReviewer", issue_block("vuln", 20, "SQL injection in user lookup", "CRITICAL")),
            ("PerformanceOptimizer", issue_block("perf", 30, "Nested O(n^2) loop", "High")),
        ]
    )

    issues = analyzer._extract_issues(review)

    assert len(issues) == 3
    severities = [i["severity"] for i in issues]
    assert severities == ["Critical", "High", "Medium"]
    agents = [i["agent"] for i in issues]
    assert agents == ["SecurityReviewer", "PerformanceOptimizer", "CodeAnalyzer"]
    for i in issues:
        assert i["line"] in (10, 20, 30)
        assert i["description"]


def test_missing_conversation_key_returns_empty(analyzer):
    assert analyzer._extract_issues({}) == []
    assert analyzer._extract_issues({"messages": [{"speaker": "CodeAnalyzer", "content": "x"}]}) == []


def test_filters_non_review_speakers(analyzer):
    block = issue_block("smell", 1, "Should not appear", "Critical")
    review = make_review(
        [
            ("User", block),
            ("TestGenerator", block),
            ("CodeExecutor", block),
            ("ReviewOrchestrator", block),
        ]
    )

    assert analyzer._extract_issues(review) == []


def test_rejects_issue_missing_severity(analyzer):
    content = "\n".join(
        [
            "- Issue type: smell",
            "- Line number: 5",
            "- Description: This issue has no severity",
        ]
    )
    review = make_review([("CodeAnalyzer", content)])

    assert analyzer._extract_issues(review) == []


def test_rejects_issue_missing_description(analyzer):
    content = "\n".join(
        [
            "- Issue type: smell",
            "- Line number: 5",
            "- Severity: Critical",
        ]
    )
    review = make_review([("CodeAnalyzer", content)])

    assert analyzer._extract_issues(review) == []


def test_severity_normalization_case_insensitive(analyzer):
    content = "\n\n".join(
        [
            issue_block("a", 1, "first issue", "CRITICAL"),
            issue_block("b", 2, "second issue", "High"),
            issue_block("c", 3, "third issue", "medium"),
            issue_block("d", 4, "fourth issue", "LOW"),
        ]
    )
    review = make_review([("CodeAnalyzer", content)])

    issues = analyzer._extract_issues(review)

    assert len(issues) == 4
    assert [i["severity"] for i in issues] == ["Critical", "High", "Medium", "Low"]


def test_dedups_by_line_and_description_prefix(analyzer):
    block = issue_block("vuln", 7, "SQL injection via f-string in query", "Critical")
    review = make_review(
        [
            ("CodeAnalyzer", block),
            ("SecurityReviewer", block),
        ]
    )

    issues = analyzer._extract_issues(review)

    assert len(issues) == 1
    assert issues[0]["agent"] == "CodeAnalyzer"


def test_sorts_by_severity_critical_first(analyzer):
    content = "\n\n".join(
        [
            issue_block("a", 1, "low priority issue", "Low"),
            issue_block("b", 2, "high priority issue", "High"),
            issue_block("c", 3, "critical issue", "Critical"),
            issue_block("d", 4, "medium issue", "Medium"),
        ]
    )
    review = make_review([("CodeAnalyzer", content)])

    issues = analyzer._extract_issues(review)

    assert [i["severity"] for i in issues] == ["Critical", "High", "Medium", "Low"]


@pytest.mark.xfail(
    reason="Non-canonical severity wording (e.g., 'Significant security risk', "
    "'Important', 'Concerning') is silently dropped: the parser's elif chain "
    "only matches the four substrings CRITICAL/HIGH/MEDIUM/LOW after .upper(), "
    "so any descriptive severity phrasing leaves severity unset and the issue "
    "is filtered out at the require-severity-and-description gate. Tier A's "
    "structured-issue contract (enum severity via function-calling) will fix.",
    strict=True,
)
def test_non_canonical_severity_word_is_extracted(analyzer):
    content = "\n".join(
        [
            "- Issue type: vuln",
            "- Line number: 42",
            "- Description: SQL injection via f-string",
            "- Severity: Significant security risk",
        ]
    )
    review = make_review([("SecurityReviewer", content)])

    issues = analyzer._extract_issues(review)

    assert len(issues) == 1
