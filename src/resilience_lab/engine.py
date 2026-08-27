"""Deterministic resilience assessment and failure propagation engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

from .model import Architecture, Component, ComponentState, Scenario, Severity


@dataclass(frozen=True)
class Finding:
    severity: Severity
    category: str
    component_id: str
    title: str
    evidence: str
    recommendation: str


@dataclass(frozen=True)
class ComponentOutcome:
    component_id: str
    state: ComponentState
    reason: str


@dataclass(frozen=True)
class ScenarioResult:
    scenario_id: str
    scenario_name: str
    system_status: str
    service_restoration_minutes: int
    estimated_data_loss_minutes: int | None
    rto_met: bool
    rpo_met: bool
    outcomes: tuple[ComponentOutcome, ...]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ScoreBreakdown:
    objectives: int
    redundancy: int
    failover: int
    data_protection: int
    observability: int
    dependency_resilience: int

    @property
    def total(self) -> int:
        return sum(asdict(self).values())


@dataclass(frozen=True)
class Assessment:
    architecture_name: str
    score: ScoreBreakdown
    findings: tuple[Finding, ...]
    scenarios: tuple[ScenarioResult, ...]

    @property
    def rating(self) -> str:
        if self.score.total >= 90:
            return "production-minded"
        if self.score.total >= 75:
            return "resilient with gaps"
        if self.score.total >= 50:
            return "material resilience risk"
        return "fragile"

    def to_dict(self) -> dict:
        return {
            "architecture_name": self.architecture_name,
            "score": {**asdict(self.score), "total": self.score.total},
            "rating": self.rating,
            "findings": [asdict(item) for item in self.findings],
            "scenarios": [item.to_dict() for item in self.scenarios],
        }


def _direct_impact(
    architecture: Architecture, scenario: Scenario
) -> tuple[dict[str, ComponentState], dict[str, str], set[str]]:
    states = {component.id: ComponentState.OPERATIONAL for component in architecture.components}
    reasons = {component.id: "No failure impact detected." for component in architecture.components}
    impacted: set[str] = set()

    if scenario.kind == "component_outage":
        states[scenario.target] = ComponentState.UNAVAILABLE
        reasons[scenario.target] = f"Direct outage of component '{scenario.target}'."
        impacted.add(scenario.target)
        return states, reasons, impacted

    for component in architecture.components:
        real_regions = {region for region in component.regions if region != "global"}
        if scenario.target not in real_regions:
            continue
        impacted.add(component.id)
        remaining = real_regions - {scenario.target}
        if remaining and component.automated_failover:
            states[component.id] = ComponentState.DEGRADED
            reasons[component.id] = (
                f"Region '{scenario.target}' is unavailable; automated failover to "
                f"{', '.join(sorted(remaining))} is expected in {component.failover_minutes} minutes."
            )
        else:
            states[component.id] = ComponentState.UNAVAILABLE
            reasons[component.id] = (
                f"Region '{scenario.target}' contains all available instances and no viable automated failover remains."
            )
    return states, reasons, impacted


def _propagate(
    architecture: Architecture,
    states: dict[str, ComponentState],
    reasons: dict[str, str],
) -> None:
    """Propagate dependency failures until the graph reaches a fixed point."""
    changed = True
    while changed:
        changed = False
        for component in architecture.components:
            if states[component.id] == ComponentState.UNAVAILABLE or not component.dependencies:
                continue
            required = [item for item in component.dependencies if item.required]
            optional = [item for item in component.dependencies if not item.required]
            required_states = [states[item.component_id] for item in required]
            optional_states = [states[item.component_id] for item in optional]
            next_state = states[component.id]
            reason = reasons[component.id]

            if required_states:
                if component.dependency_policy == "all" and ComponentState.UNAVAILABLE in required_states:
                    failed = [item.component_id for item in required if states[item.component_id] == ComponentState.UNAVAILABLE]
                    next_state = ComponentState.UNAVAILABLE
                    reason = f"Required dependency unavailable: {', '.join(failed)}."
                elif component.dependency_policy == "any" and all(
                    state == ComponentState.UNAVAILABLE for state in required_states
                ):
                    next_state = ComponentState.UNAVAILABLE
                    reason = "All alternative required dependencies are unavailable."
                elif any(state != ComponentState.OPERATIONAL for state in required_states):
                    next_state = ComponentState.DEGRADED
                    reason = "One or more required dependencies are degraded or unavailable, but service can continue."

            if next_state == ComponentState.OPERATIONAL and any(
                state != ComponentState.OPERATIONAL for state in optional_states
            ):
                next_state = ComponentState.DEGRADED
                reason = "An optional dependency is unavailable; noncritical capability is reduced."

            if next_state != states[component.id]:
                states[component.id] = next_state
                reasons[component.id] = reason
                changed = True


def _estimated_restoration(
    architecture: Architecture,
    scenario: Scenario,
    states: dict[str, ComponentState],
    directly_impacted: set[str],
) -> int:
    components = architecture.component_map
    entrypoint_states = [states[item] for item in architecture.entrypoints]
    if all(state == ComponentState.OPERATIONAL for state in entrypoint_states):
        critical_degraded = [
            component for component in architecture.components
            if component.critical and states[component.id] == ComponentState.DEGRADED
        ]
        return max((component.failover_minutes for component in critical_degraded), default=0)

    direct_components = [components[item] for item in directly_impacted]
    if scenario.kind == "region_outage":
        if any(
            component.automated_failover and states[component.id] != ComponentState.UNAVAILABLE
            for component in direct_components
        ):
            return max(
                (component.failover_minutes for component in direct_components if component.automated_failover),
                default=scenario.duration_minutes,
            )
        return scenario.duration_minutes
    return max((component.recovery_minutes for component in direct_components), default=scenario.duration_minutes)


def _estimated_data_loss(
    architecture: Architecture,
    directly_impacted: set[str],
    states: dict[str, ComponentState],
) -> int | None:
    values: list[int] = []
    unknown = False
    for component in architecture.components:
        if component.id not in directly_impacted or not component.stateful:
            continue
        if states[component.id] != ComponentState.UNAVAILABLE and component.replication_rpo_minutes is not None:
            values.append(component.replication_rpo_minutes)
        elif component.backup_rpo_minutes is not None:
            values.append(component.backup_rpo_minutes)
        else:
            unknown = True
    if unknown:
        return None
    return max(values, default=0)


def simulate(architecture: Architecture, scenario: Scenario) -> ScenarioResult:
    states, reasons, impacted = _direct_impact(architecture, scenario)
    _propagate(architecture, states, reasons)
    entrypoint_states = [states[item] for item in architecture.entrypoints]
    if all(state == ComponentState.UNAVAILABLE for state in entrypoint_states):
        status = "OUTAGE"
    elif any(state != ComponentState.OPERATIONAL for state in entrypoint_states):
        status = "DEGRADED"
    elif any(
        states[component.id] != ComponentState.OPERATIONAL
        for component in architecture.components
        if component.critical
    ):
        status = "DEGRADED"
    else:
        status = "HEALTHY"

    restoration = _estimated_restoration(architecture, scenario, states, impacted)
    data_loss = _estimated_data_loss(architecture, impacted, states)
    outcomes = tuple(
        ComponentOutcome(component.id, states[component.id], reasons[component.id])
        for component in architecture.components
    )
    return ScenarioResult(
        scenario_id=scenario.id,
        scenario_name=scenario.name,
        system_status=status,
        service_restoration_minutes=restoration,
        estimated_data_loss_minutes=data_loss,
        rto_met=restoration <= architecture.objectives.rto_minutes,
        rpo_met=(data_loss is not None and data_loss <= architecture.objectives.rpo_minutes),
        outcomes=outcomes,
    )


def _ratio_score(items: Iterable[bool], maximum: int) -> int:
    values = list(items)
    if not values:
        return maximum
    return round(maximum * sum(values) / len(values))


def _findings(architecture: Architecture) -> list[Finding]:
    findings: list[Finding] = []
    components = architecture.component_map
    for component in architecture.components:
        if component.critical and not component.is_multi_region and component.replicas == 1:
            findings.append(Finding(
                Severity.CRITICAL if component.id in architecture.entrypoints else Severity.HIGH,
                "redundancy",
                component.id,
                "Critical component is a single point of failure",
                f"{component.name} has one replica in {', '.join(component.regions)}.",
                "Add failure-domain redundancy and document the traffic or workload failover path.",
            ))
        if component.critical and not component.health_check:
            findings.append(Finding(
                Severity.HIGH,
                "failover",
                component.id,
                "No health signal drives failover",
                "The component is critical but health_check is false.",
                "Define an end-to-end health probe that validates dependencies and customer-serving behavior.",
            ))
        if component.critical and component.is_multi_region and not component.automated_failover:
            findings.append(Finding(
                Severity.HIGH,
                "failover",
                component.id,
                "Multi-region capacity lacks automated failover",
                "Multiple regions are declared, but automated_failover is false.",
                "Automate failover or document a rehearsed manual decision path with an owner and time budget.",
            ))
        if component.stateful:
            best_rpo = component.replication_rpo_minutes
            if best_rpo is None:
                best_rpo = component.backup_rpo_minutes
            if best_rpo is None:
                findings.append(Finding(
                    Severity.CRITICAL,
                    "data-protection",
                    component.id,
                    "No recoverable data copy is documented",
                    "Neither replication_rpo_minutes nor backup_rpo_minutes is defined.",
                    "Define tested replication and backup controls, including restore evidence and retention.",
                ))
            elif best_rpo > architecture.objectives.rpo_minutes:
                findings.append(Finding(
                    Severity.HIGH,
                    "data-protection",
                    component.id,
                    "Data protection does not meet the system RPO",
                    f"Best documented RPO is {best_rpo} minutes; target is {architecture.objectives.rpo_minutes}.",
                    "Improve replication or backup frequency and prove recovery with a restore test.",
                ))
        if component.critical and not {"metrics", "logs", "alerts"}.issubset(set(component.telemetry)):
            missing = sorted({"metrics", "logs", "alerts"} - set(component.telemetry))
            findings.append(Finding(
                Severity.MEDIUM,
                "observability",
                component.id,
                "Critical telemetry coverage is incomplete",
                f"Missing signals: {', '.join(missing)}.",
                "Instrument golden signals, structured logs, and actionable alerts tied to the service objectives.",
            ))

        for dependency in component.dependencies:
            target = components[dependency.component_id]
            if (
                component.critical
                and dependency.required
                and component.dependency_policy == "all"
                and not target.is_multi_region
                and target.replicas == 1
            ):
                findings.append(Finding(
                    Severity.HIGH,
                    "dependency",
                    component.id,
                    "Critical path depends on a single-instance service",
                    f"{component.name} requires {target.name}, which has no failure-domain redundancy.",
                    "Remove the dependency SPOF, add a degraded mode, or make the dependency redundant.",
                ))
    return findings


def assess(architecture: Architecture) -> Assessment:
    critical = [component for component in architecture.components if component.critical]
    stateful = [component for component in architecture.components if component.stateful]
    objectives_score = 15 if (
        architecture.owners and architecture.business_impact != "Not documented"
        and architecture.objectives.rto_minutes > 0
        and architecture.objectives.rpo_minutes >= 0
    ) else 8
    redundancy_score = _ratio_score(
        (component.is_multi_region or component.replicas > 1 for component in critical), 20
    )
    failover_score = _ratio_score(
        (
            component.health_check
            and (not component.is_multi_region or component.automated_failover)
            and component.failover_minutes <= architecture.objectives.rto_minutes
            for component in critical
        ),
        20,
    )
    data_score = _ratio_score(
        (
            (
                component.replication_rpo_minutes
                if component.replication_rpo_minutes is not None
                else component.backup_rpo_minutes
            ) is not None
            and (
                component.replication_rpo_minutes
                if component.replication_rpo_minutes is not None
                else component.backup_rpo_minutes
            ) <= architecture.objectives.rpo_minutes
            for component in stateful
        ),
        20,
    )
    observability_score = _ratio_score(
        ({"metrics", "logs", "alerts"}.issubset(set(component.telemetry)) for component in critical), 15
    )
    findings = _findings(architecture)
    dependency_score = 10 if not any(item.category == "dependency" for item in findings) else 4
    score = ScoreBreakdown(
        objectives=objectives_score,
        redundancy=redundancy_score,
        failover=failover_score,
        data_protection=data_score,
        observability=observability_score,
        dependency_resilience=dependency_score,
    )
    results = tuple(simulate(architecture, scenario) for scenario in architecture.scenarios)
    return Assessment(architecture.name, score, tuple(findings), results)
