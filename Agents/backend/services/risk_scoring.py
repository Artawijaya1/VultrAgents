"""Presentation labels for rule alerts. Do not equate severity to fraud probability."""

SEVERITY_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}

def summarize_findings(findings: list[dict]) -> dict:
    counts = {s: 0 for s in SEVERITY_ORDER}
    for item in findings:
        if item.get("severity") in counts:
            counts[item["severity"]] += 1
    return {"total": len(findings), "by_severity": counts,
            "human_review_required": bool(findings),
            "disclaimer": "Indikator risiko; bukan bukti atau putusan fraud."}
