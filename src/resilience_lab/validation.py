"""Semantic validation for architecture specifications."""

from __future__ import annotations

from dataclasses import dataclass

from .model import Architecture


@dataclass(frozen=True)
class ValidationIssue:
    level: str
    path: str
    message: str


def validate_architecture(architecture: Architecture) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    component_ids = [component.id for component in architecture.components]
    component_set = set(component_ids)

    if len(component_ids) != len(component_set):
        duplicates = sorted({item for item in component_ids if component_ids.count(item) > 1})
        issues.append(ValidationIssue("error", "system.components", f"duplicate component IDs: {duplicates}"))

    if not 0 < architecture.objectives.availability_target <= 100:
        issues.append(ValidationIssue("error", "system.objectives.availability_target", "must be > 0 and <= 100"))
    if architecture.objectives.rto_minutes <= 0:
        issues.append(ValidationIssue("error", "system.objectives.rto_minutes", "must be greater than zero"))
    if architecture.objectives.rpo_minutes < 0:
        issues.append(ValidationIssue("error", "system.objectives.rpo_minutes", "cannot be negative"))
    if not architecture.entrypoints:
        issues.append(ValidationIssue("error", "system.entrypoints", "at least one entrypoint is required"))

    for entrypoint in architecture.entrypoints:
        if entrypoint not in component_set:
            issues.append(ValidationIssue("error", "system.entrypoints", f"unknown component '{entrypoint}'"))

    for component in architecture.components:
        path = f"system.components.{component.id}"
        if not component.regions:
            issues.append(ValidationIssue("error", f"{path}.regions", "at least one region is required"))
        if component.replicas < 1:
            issues.append(ValidationIssue("error", f"{path}.replicas", "must be at least one"))
        if component.dependency_policy not in {"all", "any"}:
            issues.append(ValidationIssue("error", f"{path}.dependency_policy", "must be 'all' or 'any'"))
        if component.failover_minutes < 0 or component.recovery_minutes < 0:
            issues.append(ValidationIssue("error", path, "recovery and failover times cannot be negative"))
        for dependency in component.dependencies:
            if dependency.component_id not in component_set:
                issues.append(
                    ValidationIssue("error", f"{path}.dependencies", f"unknown component '{dependency.component_id}'")
                )
            if dependency.component_id == component.id:
                issues.append(ValidationIssue("error", f"{path}.dependencies", "a component cannot depend on itself"))
        if component.stateful and component.replication_rpo_minutes is None and component.backup_rpo_minutes is None:
            issues.append(
                ValidationIssue("warning", path, "stateful component has no replication or backup RPO evidence")
            )
        if component.critical and not component.telemetry:
            issues.append(ValidationIssue("warning", path, "critical component has no telemetry signals"))

    graph = {
        component.id: [dependency.component_id for dependency in component.dependencies if dependency.component_id in component_set]
        for component in architecture.components
    }
    visiting: list[str] = []
    visited: set[str] = set()
    reported_cycles: set[tuple[str, ...]] = set()

    def visit(component_id: str) -> None:
        if component_id in visiting:
            start = visiting.index(component_id)
            cycle = tuple(visiting[start:] + [component_id])
            if cycle not in reported_cycles:
                reported_cycles.add(cycle)
                issues.append(
                    ValidationIssue("error", "system.components", f"dependency cycle detected: {' -> '.join(cycle)}")
                )
            return
        if component_id in visited:
            return
        visiting.append(component_id)
        for dependency_id in graph.get(component_id, []):
            visit(dependency_id)
        visiting.pop()
        visited.add(component_id)

    for component_id in component_ids:
        visit(component_id)

    scenario_ids: set[str] = set()
    for scenario in architecture.scenarios:
        path = f"system.scenarios.{scenario.id}"
        if scenario.id in scenario_ids:
            issues.append(ValidationIssue("error", path, "duplicate scenario ID"))
        scenario_ids.add(scenario.id)
        if scenario.kind not in {"region_outage", "component_outage"}:
            issues.append(ValidationIssue("error", f"{path}.kind", "must be region_outage or component_outage"))
        if scenario.kind == "component_outage" and scenario.target not in component_set:
            issues.append(ValidationIssue("error", f"{path}.target", f"unknown component '{scenario.target}'"))
        if scenario.kind == "region_outage" and not any(
            scenario.target in component.regions for component in architecture.components
        ):
            issues.append(
                ValidationIssue("warning", f"{path}.target", f"region '{scenario.target}' does not contain any component")
            )
        if scenario.duration_minutes <= 0:
            issues.append(ValidationIssue("error", f"{path}.duration_minutes", "must be greater than zero"))

    return issues


def has_errors(issues: list[ValidationIssue]) -> bool:
    return any(issue.level == "error" for issue in issues)
