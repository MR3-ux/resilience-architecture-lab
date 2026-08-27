#!/usr/bin/env python3
"""Dependency-free repository quality checks used locally and in CI."""

from __future__ import annotations

from pathlib import Path
import json
import py_compile
import sys


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".py", ".md", ".json", ".yml", ".toml"}
REQUIRED = {
    "README.md",
    "LICENSE",
    "SECURITY.md",
    "pyproject.toml",
    "examples/azure-active-active.json",
    "reports/demo/resilience-assessment.md",
}


def main() -> int:
    failures: list[str] = []

    for required in sorted(REQUIRED):
        if not (ROOT / required).is_file():
            failures.append(f"missing required file: {required}")

    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(ROOT)
        if path.suffix in TEXT_SUFFIXES:
            text = path.read_text(encoding="utf-8")
            if not text.endswith("\n"):
                failures.append(f"{relative}: missing final newline")
            if text.endswith("\n\n"):
                failures.append(f"{relative}: extra blank line at end of file")
            for line_number, line in enumerate(text.splitlines(), start=1):
                if line.rstrip() != line:
                    failures.append(f"{relative}:{line_number}: trailing whitespace")
        if path.suffix == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                failures.append(f"{relative}:{exc.lineno}:{exc.colno}: invalid JSON: {exc.msg}")
        if path.suffix == ".py":
            try:
                py_compile.compile(str(path), doraise=True)
            except py_compile.PyCompileError as exc:
                failures.append(f"{relative}: {exc.msg}")

    if failures:
        print("QUALITY CHECK FAILED", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("QUALITY CHECK PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
