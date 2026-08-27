"""Typed domain model for resilience architecture specifications."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any
import json


class ComponentState(StrEnum):
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class Objectives:
    availability_target: float
    rto_minutes: int
    rpo_minutes: int


@dataclass(frozen=True)
class Dependency:
    component_id: str
    required: bool = True


@dataclass(frozen=True)
class Component:
    id: str
    name: str
    kind: str
    critical: bool
    regions: tuple[str, ...]
    replicas: int
    dependency_policy: str
    dependencies: tuple[Dependency, ...]
    health_check: bool
    automated_failover: bool
    failover_minutes: int
    recovery_minutes: int
    stateful: bool
    replication_rpo_minutes: int | None
    backup_rpo_minutes: int | None
    telemetry: tuple[str, ...]

    @property
    def is_multi_region(self) -> bool:
        real_regions = {region for region in self.regions if region != "global"}
        return len(real_regions) > 1 or "global" in self.regions


@dataclass(frozen=True)
class Scenario:
    id: str
    name: str
    kind: str
    target: str
    duration_minutes: int
    description: str = ""


@dataclass(frozen=True)
class Architecture:
    name: str
    description: str
    business_impact: str
    owners: tuple[str, ...]
    objectives: Objectives
    entrypoints: tuple[str, ...]
    components: tuple[Component, ...]
    scenarios: tuple[Scenario, ...]
    assumptions: tuple[str, ...] = field(default_factory=tuple)

    @property
    def component_map(self) -> dict[str, Component]:
        return {component.id: component for component in self.components}

    @property
    def scenario_map(self) -> dict[str, Scenario]:
        return {scenario.id: scenario for scenario in self.scenarios}


def _require(data: dict[str, Any], key: str, context: str) -> Any:
    if key not in data:
        raise ValueError(f"{context}: missing required field '{key}'")
    return data[key]


def _component(data: dict[str, Any], index: int) -> Component:
    context = f"components[{index}]"
    dependencies = tuple(
        Dependency(
            component_id=_require(item, "component_id", f"{context}.dependencies[{dep_index}]"),
            required=bool(item.get("required", True)),
        )
        for dep_index, item in enumerate(data.get("dependencies", []))
    )
    return Component(
        id=str(_require(data, "id", context)),
        name=str(_require(data, "name", context)),
        kind=str(_require(data, "kind", context)),
        critical=bool(data.get("critical", False)),
        regions=tuple(str(value) for value in data.get("regions", [])),
        replicas=int(data.get("replicas", 1)),
        dependency_policy=str(data.get("dependency_policy", "all")),
        dependencies=dependencies,
        health_check=bool(data.get("health_check", False)),
        automated_failover=bool(data.get("automated_failover", False)),
        failover_minutes=int(data.get("failover_minutes", 0)),
        recovery_minutes=int(data.get("recovery_minutes", 60)),
        stateful=bool(data.get("stateful", False)),
        replication_rpo_minutes=(
            int(data["replication_rpo_minutes"])
            if data.get("replication_rpo_minutes") is not None
            else None
        ),
        backup_rpo_minutes=(
            int(data["backup_rpo_minutes"])
            if data.get("backup_rpo_minutes") is not None
            else None
        ),
        telemetry=tuple(str(value) for value in data.get("telemetry", [])),
    )


def _scenario(data: dict[str, Any], index: int) -> Scenario:
    context = f"scenarios[{index}]"
    return Scenario(
        id=str(_require(data, "id", context)),
        name=str(_require(data, "name", context)),
        kind=str(_require(data, "kind", context)),
        target=str(_require(data, "target", context)),
        duration_minutes=int(data.get("duration_minutes", 60)),
        description=str(data.get("description", "")),
    )


def load_architecture(path: str | Path) -> Architecture:
    """Load an architecture from JSON with actionable parse errors."""
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"architecture file not found: {source}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"invalid JSON in {source} at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc

    system = _require(data, "system", "root")
    objective_data = _require(system, "objectives", "system")
    objectives = Objectives(
        availability_target=float(_require(objective_data, "availability_target", "system.objectives")),
        rto_minutes=int(_require(objective_data, "rto_minutes", "system.objectives")),
        rpo_minutes=int(_require(objective_data, "rpo_minutes", "system.objectives")),
    )
    return Architecture(
        name=str(_require(system, "name", "system")),
        description=str(system.get("description", "")),
        business_impact=str(system.get("business_impact", "Not documented")),
        owners=tuple(str(value) for value in system.get("owners", [])),
        objectives=objectives,
        entrypoints=tuple(str(value) for value in _require(system, "entrypoints", "system")),
        components=tuple(
            _component(item, index)
            for index, item in enumerate(_require(system, "components", "system"))
        ),
        scenarios=tuple(
            _scenario(item, index)
            for index, item in enumerate(_require(system, "scenarios", "system"))
        ),
        assumptions=tuple(str(value) for value in system.get("assumptions", [])),
    )
