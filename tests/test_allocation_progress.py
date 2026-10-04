"""Progress events must match real ChargingAgent pipeline stages."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from ai.agent import ChargingAgent
from ai.problem_formulation import Params


class AllocationProgressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sites = pd.read_csv("data/ev_locations.csv")
        cls.zones = pd.read_csv("data/demand_zones.csv")

    def test_success_reports_stages_in_execution_order(self):
        events = []
        result = ChargingAgent(self.sites, self.zones, Params()).run(
            lambda stage, event: events.append((stage, event))
        )
        self.assertTrue(result["feasible"])

        expected = [
            "Validating demand inputs",
            "Formulating allocation problem",
            "Applying CSP constraints",
            "Propagating constraints",
            "Checking allocation feasibility",
            "Running heuristic search (A*)",
            "Evaluating alternatives with backtracking",
            "Running local search",
            "Optimizing final network",
            "Allocation complete",
        ]
        complete = [stage for stage, event in events if event == "complete"]
        self.assertEqual(complete, expected)
        for stage in expected[:-1]:
            self.assertIn((stage, "start"), events)

    def test_invalid_inputs_stop_before_search(self):
        events = []
        result = ChargingAgent(self.sites, self.zones, Params(budget=-1)).run(
            lambda stage, event: events.append((stage, event))
        )
        self.assertFalse(result["feasible"])
        self.assertIn(("Validating demand inputs", "failed"), events)
        self.assertNotIn(("Running heuristic search (A*)", "start"), events)
        self.assertNotIn(("Running local search", "start"), events)

    def test_infeasible_constraints_stop_before_search(self):
        events = []
        result = ChargingAgent(self.sites, self.zones, Params(budget=5)).run(
            lambda stage, event: events.append((stage, event))
        )
        self.assertFalse(result["feasible"])
        self.assertIn(("Propagating constraints", "complete"), events)
        self.assertIn(("Checking allocation feasibility", "failed"), events)
        self.assertIn(("Allocation could not be completed", "failed"), events)
        self.assertNotIn(("Running heuristic search (A*)", "start"), events)
        self.assertNotIn(("Evaluating alternatives with backtracking", "start"), events)


if __name__ == "__main__":
    unittest.main()