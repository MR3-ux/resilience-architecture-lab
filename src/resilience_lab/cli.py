"""Command-line interface for Resilience Architecture Lab."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .engine import assess, simulate
from .model import load_architecture
from .report import write_reports
from .validation import has_errors, validate_architecture


def _load_validated(path: str):
    architecture = load_architecture(path)
    issues = validate_architecture(architecture)
    for issue in issues:
        stream = sys.stderr if issue.level == "error" else sys.stdout
        print(f"{issue.level.upper():7} {issue.path}: {issue.message}", file=stream)
    if has_errors(issues):
        raise ValueError("architecture validation failed")
    return architecture


def _validate(args: argparse.Namespace) -> int:
    architecture = load_architecture(args.architecture)
    issues = validate_architecture(architecture)
    for issue in issues:
        print(f"{issue.level.upper():7} {issue.path}: {issue.message}")
    if has_errors(issues):
        print(f"Validation failed with {sum(item.level == 'error' for item in issues)} error(s).")
        return 2
    print(f"VALID: {architecture.name} ({len(architecture.components)} components, {len(architecture.scenarios)} scenarios)")
    return 0


def _assess(args: argparse.Namespace) -> int:
    architecture = _load_validated(args.architecture)
    assessment = assess(architecture)
    markdown, machine = write_reports(architecture, assessment, args.output_dir)
    print(f"Score: {assessment.score.total}/100 ({assessment.rating})")
    print(f"Markdown: {markdown}")
    print(f"JSON: {machine}")
    return 0


def _simulate(args: argparse.Namespace) -> int:
    architecture = _load_validated(args.architecture)
    try:
        scenario = architecture.scenario_map[args.scenario]
    except KeyError:
        available = ", ".join(sorted(architecture.scenario_map))
        print(f"Unknown scenario '{args.scenario}'. Available: {available}", file=sys.stderr)
        return 2
    result = simulate(architecture, scenario)
    print(f"{result.scenario_name}: {result.system_status}")
    restore_unit = "minute" if result.service_restoration_minutes == 1 else "minutes"
    print(f"Estimated service restoration: {result.service_restoration_minutes} {restore_unit}")
    if result.estimated_data_loss_minutes is None:
        print("Estimated data loss: unknown")
    else:
        data_unit = "minute" if result.estimated_data_loss_minutes == 1 else "minutes"
        print(f"Estimated data loss: {result.estimated_data_loss_minutes} {data_unit}")
    print(f"RTO: {'PASS' if result.rto_met else 'FAIL'} | RPO: {'PASS' if result.rpo_met else 'FAIL'}")
    print("\nImpacted components:")
    for outcome in result.outcomes:
        if outcome.state != "operational":
            print(f"- {outcome.component_id}: {outcome.state} - {outcome.reason}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="resilience-lab",
        description="Assess architecture resilience and simulate failure propagation.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate an architecture specification")
    validate_parser.add_argument("architecture")
    validate_parser.set_defaults(handler=_validate)

    assess_parser = subparsers.add_parser("assess", help="Run all rules and failure scenarios")
    assess_parser.add_argument("architecture")
    assess_parser.add_argument("--output-dir", default="reports/latest")
    assess_parser.set_defaults(handler=_assess)

    simulate_parser = subparsers.add_parser("simulate", help="Run one failure scenario")
    simulate_parser.add_argument("architecture")
    simulate_parser.add_argument("--scenario", required=True)
    simulate_parser.set_defaults(handler=_simulate)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
