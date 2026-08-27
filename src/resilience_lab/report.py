"""Human- and machine-readable resilience report generation."""

from __future__ import annotations

from pathlib import Path
import json

from .engine import Assessment
from .model import Architecture, ComponentState


def _yes_no(value: bool) -> str:
    return "PASS" if value else "FAIL"


def render_markdown(architecture: Architecture, assessment: Assessment) -> str:
    lines = [
        f"# Resilience Assessment: {architecture.name}",
        "",
        "> Generated deterministically by Resilience Architecture Lab v0.1.0 from the version-controlled model.",
        "",
        "## Executive summary",
        "",
        f"**Resilience score:** {assessment.score.total}/100 ({assessment.rating})",
        "",
        architecture.description,
        "",
        f"**Business impact:** {architecture.business_impact}",
        "",
        f"**Objectives:** {architecture.objectives.availability_target}% availability; "
        f"RTO {architecture.objectives.rto_minutes} minutes; RPO {architecture.objectives.rpo_minutes} minutes.",
        "",
        "## Scorecard",
        "",
        "| Dimension | Score | Maximum |",
        "|---|---:|---:|",
        f"| Objectives and ownership | {assessment.score.objectives} | 15 |",
        f"| Failure-domain redundancy | {assessment.score.redundancy} | 20 |",
        f"| Detection and failover | {assessment.score.failover} | 20 |",
        f"| Data protection | {assessment.score.data_protection} | 20 |",
        f"| Observability | {assessment.score.observability} | 15 |",
        f"| Dependency resilience | {assessment.score.dependency_resilience} | 10 |",
        f"| **Total** | **{assessment.score.total}** | **100** |",
        "",
        "## Failure scenarios",
        "",
        "| Scenario | Result | Restore | Data loss | RTO | RPO |",
        "|---|---|---:|---:|---|---|",
    ]
    for result in assessment.scenarios:
        data_loss = "unknown" if result.estimated_data_loss_minutes is None else f"{result.estimated_data_loss_minutes} min"
        lines.append(
            f"| {result.scenario_name} | {result.system_status} | "
            f"{result.service_restoration_minutes} min | {data_loss} | "
            f"{_yes_no(result.rto_met)} | {_yes_no(result.rpo_met)} |"
        )

    lines.extend(["", "## Findings", ""])
    if assessment.findings:
        for index, finding in enumerate(assessment.findings, start=1):
            lines.extend([
                f"### {index}. [{finding.severity.upper()}] {finding.title}",
                "",
                f"- **Category:** {finding.category}",
                f"- **Component:** `{finding.component_id}`",
                f"- **Evidence:** {finding.evidence}",
                f"- **Recommendation:** {finding.recommendation}",
                "",
            ])
    else:
        lines.extend(["No static design gaps were detected by the current ruleset.", ""])

    lines.extend(["## Scenario evidence", ""])
    for result in assessment.scenarios:
        lines.extend([
            f"### {result.scenario_name}",
            "",
            "| Component | State | Reason |",
            "|---|---|---|",
        ])
        for outcome in result.outcomes:
            if outcome.state != ComponentState.OPERATIONAL:
                lines.append(f"| `{outcome.component_id}` | {outcome.state} | {outcome.reason} |")
        if all(outcome.state == ComponentState.OPERATIONAL for outcome in result.outcomes):
            lines.append("| - | operational | No component-level impact detected. |")
        lines.append("")

    lines.extend([
        "## Assumptions and limits",
        "",
        *[f"- {item}" for item in architecture.assumptions],
        "- Results are deterministic design-review evidence, not a substitute for production telemetry or controlled chaos experiments.",
        "- Recovery estimates are only as credible as the runbooks, automation, capacity tests, and restore exercises behind the input values.",
        "",
    ])
    return "\n".join(lines)


def write_reports(
    architecture: Architecture,
    assessment: Assessment,
    output_dir: str | Path,
) -> tuple[Path, Path]:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    markdown_path = destination / "resilience-assessment.md"
    json_path = destination / "resilience-assessment.json"
    markdown_path.write_text(render_markdown(architecture, assessment), encoding="utf-8")
    json_path.write_text(json.dumps(assessment.to_dict(), indent=2) + "\n", encoding="utf-8")
    return markdown_path, json_path
