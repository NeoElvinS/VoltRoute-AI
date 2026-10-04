"""Focused checks for the data-backed Chennai Folium map."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import folium
import pandas as pd

from ai.agent import ChargingAgent
from ai.problem_formulation import Params
from visualization.maps import CHENNAI_CENTER, CHENNAI_ZOOM, build_map


class MapInteractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sites = pd.read_csv("data/ev_locations.csv")
        cls.zones = pd.read_csv("data/demand_zones.csv")
        cls.existing = pd.read_csv("data/existing_stations.csv")
        cls.result = ChargingAgent(cls.sites, cls.zones, Params()).run()
        cls.problem = cls.result["problem"]

    def setUp(self):
        self.map = build_map(self.problem, self.existing, self.result["state"], self.result)
        self.groups = {
            layer.layer_name: layer
            for layer in self.map._children.values()
            if isinstance(layer, folium.FeatureGroup)
        }

    def test_chennai_center_and_named_layers(self):
        self.assertEqual(self.map.location, CHENNAI_CENTER)
        self.assertEqual(self.map.options["zoom"], CHENNAI_ZOOM)
        self.assertTrue({
            "Demand Zones",
            "Candidate Charging Locations",
            "Existing Charging Stations",
            "AI Recommended Stations",
            "Demand-to-Station Connections",
        }.issubset(self.groups))

    def test_markers_use_source_rows_and_actual_ai_state(self):
        self.assertEqual(len(self.groups["Demand Zones"]._children), len(self.zones))
        self.assertEqual(len(self.groups["Candidate Charging Locations"]._children), len(self.sites))
        self.assertEqual(len(self.groups["Existing Charging Stations"]._children), len(self.existing))
        self.assertEqual(len(self.groups["AI Recommended Stations"]._children), len(self.result["state"]))

        recommended_locations = {
            tuple(marker.location)
            for marker in self.groups["AI Recommended Stations"]._children.values()
        }
        expected_locations = {
            (self.sites.loc[index, "latitude"], self.sites.loc[index, "longitude"])
            for index in self.result["state"]
        }
        self.assertEqual(recommended_locations, expected_locations)

        assignments = self.problem.assign(self.result["state"])
        self.assertEqual(
            len(self.groups["Demand-to-Station Connections"]._children),
            sum(station_index is not None for station_index in assignments),
        )

    def test_click_popups_contain_dataset_and_ai_details(self):
        for group_name in (
            "Demand Zones",
            "Candidate Charging Locations",
            "Existing Charging Stations",
            "AI Recommended Stations",
        ):
            self.assertTrue(all(
                any(isinstance(child, folium.Popup) for child in marker._children.values())
                for marker in self.groups[group_name]._children.values()
            ))

        marker_groups = (
            "Demand Zones",
            "Candidate Charging Locations",
            "Existing Charging Stations",
            "AI Recommended Stations",
        )
        for group_name in marker_groups:
            for marker in self.groups[group_name]._children.values():
                latitude, longitude = marker.location
                self.assertTrue(12.8 <= latitude <= 13.3)
                self.assertTrue(80.0 <= longitude <= 80.4)

        html = self.map.get_root().render()
        for detail in (
            "Demand intensity",
            "Nearest candidate",
            "Coverage status",
            "Installation cost",
            "Charging capacity",
            "Grid capacity / usage",
            "Demand served",
            "AI selection",
            "AI Recommendation",
            "AI score",
            "Reason for selection",
            "Reset view to Chennai",
            "L.control.layers",
        ):
            self.assertIn(detail, html)

        for station_index in self.result["state"]:
            station_name = self.sites.loc[station_index, "location_name"]
            self.assertIn(station_name, html)
        for name in self.sites["location_name"]:
            self.assertIn(name, html)
        for name in self.zones["zone_name"]:
            self.assertIn(name, html)
        for name in self.existing["station_name"]:
            self.assertIn(name, html)

    def test_preallocation_map_has_no_recommendation_layers(self):
        preview = build_map(self.problem, self.existing, frozenset())
        names = {
            layer.layer_name
            for layer in preview._children.values()
            if isinstance(layer, folium.FeatureGroup)
        }
        self.assertNotIn("AI Recommended Stations", names)
        self.assertNotIn("Demand-to-Station Connections", names)
        self.assertIn("Demand Zones", names)
        self.assertIn("Candidate Charging Locations", names)
        self.assertIn("Existing Charging Stations", names)


if __name__ == "__main__":
    unittest.main()