"""Compliance scoring — combines rule check results and RAG findings into 0-100 score."""

SEVERITY_PENALTIES = {
    "critical": 30,
    "high": 15,
    "medium": 5,
    "low": 2,
}

RAG_SEVERITY_PENALTIES = {
    "high": 10,
    "medium": 5,
    "low": 2,
}


def calculate_compliance_score(
    check_results: list[dict],
    rag_findings: list[dict] | None = None,
) -> int:
    """Calculate a 0-100 compliance score from check results and RAG findings.

    Scoring:
        Start at 100, deduct per failed check and per RAG finding.
        CRITICAL fail: -30
        HIGH fail:     -15
        MEDIUM fail:   -5
        LOW fail:      -2
        RAG HIGH:      -10
        RAG MEDIUM:    -5
        RAG LOW:       -2
        Minimum: 0
    """
    score = 100

    for check in check_results:
        if not check.get("passed", True):
            severity = check.get("severity", "medium")
            score -= SEVERITY_PENALTIES.get(severity, 5)

    if rag_findings:
        for finding in rag_findings:
            severity = finding.get("severity", "medium")
            score -= RAG_SEVERITY_PENALTIES.get(severity, 5)

    return max(0, score)
