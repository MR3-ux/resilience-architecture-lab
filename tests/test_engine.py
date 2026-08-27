import unittest
from pathlib import Path

from resilience_lab.engine import assess, simulate
from resilience_lab.model import ComponentState, load_architecture


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "azure-active-active.json"
FRAGILE = ROOT / "examples" / "fragile-single-region.json"


class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.architecture = load_architecture(EXAMPLE)

    def test_reference_architecture_scores_high(self):
        result = assess(self.architecture)
        self.assertGreaterEqual(result.score.total, 90)
        self.assertEqual(result.rating, "production-minded")

    def test_region_outage_degrades_but_does_not_drop_entrypoint(self):
        result = simulate(self.architecture, self.architecture.scenario_map["east-region-loss"])
        states = {item.component_id: item.state for item in result.outcomes}
        self.assertEqual(result.system_status, "DEGRADED")
        self.assertEqual(states["app-east"], ComponentState.UNAVAILABLE)
        self.assertEqual(states["app-west"], ComponentState.DEGRADED)
        self.assertEqual(states["front-door"], ComponentState.DEGRADED)
        self.assertTrue(result.rto_met)
        self.assertTrue(result.rpo_met)

    def test_database_outage_propagates_to_customer_entrypoint(self):
        result = simulate(self.architecture, self.architecture.scenario_map["database-loss"])
        states = {item.component_id: item.state for item in result.outcomes}
        self.assertEqual(result.system_status, "OUTAGE")
        self.assertEqual(states["app-east"], ComponentState.UNAVAILABLE)
        self.assertEqual(states["app-west"], ComponentState.UNAVAILABLE)
        self.assertEqual(states["front-door"], ComponentState.UNAVAILABLE)
        self.assertTrue(result.rto_met)
        self.assertFalse(result.rpo_met)

    def test_identity_outage_has_zero_data_loss(self):
        result = simulate(self.architecture, self.architecture.scenario_map["identity-loss"])
        self.assertEqual(result.estimated_data_loss_minutes, 0)
        self.assertTrue(result.rpo_met)

    def test_fragile_architecture_exposes_material_risk(self):
        architecture = load_architecture(FRAGILE)
        result = assess(architecture)
        self.assertLess(result.score.total, 50)
        self.assertEqual(result.rating, "fragile")
        self.assertTrue(any(item.category == "redundancy" for item in result.findings))
        self.assertTrue(any(item.category == "data-protection" for item in result.findings))
        self.assertFalse(result.scenarios[0].rto_met)
        self.assertFalse(result.scenarios[0].rpo_met)


if __name__ == "__main__":
    unittest.main()
