import unittest
from dataclasses import replace
from pathlib import Path

from resilience_lab.model import load_architecture
from resilience_lab.validation import has_errors, validate_architecture


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "azure-active-active.json"


class ValidationTests(unittest.TestCase):
    def test_example_is_valid(self):
        architecture = load_architecture(EXAMPLE)
        issues = validate_architecture(architecture)
        self.assertFalse(has_errors(issues), issues)

    def test_unknown_entrypoint_is_rejected(self):
        architecture = replace(load_architecture(EXAMPLE), entrypoints=("missing",))
        issues = validate_architecture(architecture)
        self.assertTrue(has_errors(issues))
        self.assertTrue(any("unknown component" in issue.message for issue in issues))

    def test_self_dependency_is_rejected(self):
        architecture = load_architecture(EXAMPLE)
        component = architecture.components[0]
        bad_dependency = replace(component.dependencies[0], component_id=component.id)
        bad_component = replace(component, dependencies=(bad_dependency,))
        broken = replace(architecture, components=(bad_component, *architecture.components[1:]))
        issues = validate_architecture(broken)
        self.assertTrue(any("cannot depend on itself" in issue.message for issue in issues))

    def test_dependency_cycle_is_rejected(self):
        architecture = load_architecture(EXAMPLE)
        first = architecture.components[0]
        second = architecture.components[1]
        first_to_second = replace(first.dependencies[0], component_id=second.id)
        second_to_first = replace(second.dependencies[0], component_id=first.id)
        broken = replace(
            architecture,
            components=(
                replace(first, dependencies=(first_to_second,)),
                replace(second, dependencies=(second_to_first,)),
                *architecture.components[2:],
            ),
        )
        issues = validate_architecture(broken)
        self.assertTrue(any("dependency cycle detected" in issue.message for issue in issues))


if __name__ == "__main__":
    unittest.main()
