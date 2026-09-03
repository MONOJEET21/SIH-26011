"""
Tests for the Step 9A cadastral query engine.
"""

from __future__ import annotations

import unittest

from ml.gis.query.cadastral_queries import CadastralQueryEngine


class TestCadastralQueryEngine(unittest.TestCase):
    """Test the JSON-backed cadastral query engine."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = CadastralQueryEngine()

    # --------------------------------------------------------------
    # Basic entity queries
    # --------------------------------------------------------------

    def test_get_parcel(self) -> None:
        response = self.engine.get_parcel("P001")

        self.assertTrue(response.success)
        self.assertEqual(response.count, 1)
        self.assertEqual(response.data["parcel_id"], "P001")
        self.assertEqual(response.data["entity_type"], "parcel")

    def test_get_building(self) -> None:
        response = self.engine.get_building("B001")

        self.assertTrue(response.success)
        self.assertEqual(response.count, 1)
        self.assertEqual(response.data["building_id"], "B001")
        self.assertEqual(response.data["parcel_id"], "P001")

    def test_get_floor_by_number(self) -> None:
        response = self.engine.get_floor("B001", 3)

        self.assertTrue(response.success)
        self.assertEqual(response.count, 1)
        self.assertEqual(response.data["floor_id"], "B001_F03")
        self.assertEqual(response.data["floor_number"], 3)

    def test_get_floor_by_floor_code(self) -> None:
        response = self.engine.get_floor("B001", "F03")

        self.assertTrue(response.success)
        self.assertEqual(response.data["floor_id"], "B001_F03")

    def test_get_basement_floor(self) -> None:
        response = self.engine.get_floor("B002", 0)

        self.assertTrue(response.success)
        self.assertEqual(response.data["floor_id"], "B002_B01")
        self.assertEqual(response.data["floor_type"], "BASEMENT")

    def test_get_property_unit(self) -> None:
        response = self.engine.get_property_unit(
            "B001_F03_U0302"
        )

        self.assertTrue(response.success)
        self.assertEqual(response.count, 1)

        self.assertEqual(
            response.data["unit_id"],
            "B001_F03_U0302",
        )

        self.assertEqual(
            response.data["building_id"],
            "B001",
        )

        self.assertEqual(
            response.data["floor_id"],
            "B001_F03",
        )

        self.assertEqual(
            response.data["parcel_id"],
            "P001",
        )

    # --------------------------------------------------------------
    # Collection queries
    # --------------------------------------------------------------

    def test_units_in_parcel(self) -> None:
        response = self.engine.get_units_in_parcel("P001")

        self.assertTrue(response.success)

        # P001 has 15 property units.
        self.assertEqual(response.count, 15)

        self.assertTrue(
            all(
                item["parcel_id"] == "P001"
                for item in response.data
            )
        )

    def test_units_in_building(self) -> None:
        response = self.engine.get_units_in_building("B001")

        self.assertTrue(response.success)

        # B001 has 5 floors x 3 units.
        self.assertEqual(response.count, 15)

        self.assertTrue(
            all(
                item["building_id"] == "B001"
                for item in response.data
            )
        )

    def test_units_on_floor(self) -> None:
        response = self.engine.get_units_on_floor(
            "B001",
            3,
        )

        self.assertTrue(response.success)

        # Every normal floor has 3 units.
        self.assertEqual(response.count, 3)

        self.assertTrue(
            all(
                item["floor_id"] == "B001_F03"
                for item in response.data
            )
        )

    def test_underground_assets(self) -> None:
        response = self.engine.get_underground_assets("P001")

        self.assertTrue(response.success)
        self.assertEqual(response.count, 1)

        self.assertEqual(
            response.data[0]["asset_id"],
            "UA001",
        )

    # --------------------------------------------------------------
    # Hierarchical queries
    # --------------------------------------------------------------

    def test_find_entities_in_parcel(self) -> None:
        response = self.engine.find_entities_in_parcel("P001")

        self.assertTrue(response.success)

        # P001:
        #
        # 1 parcel
        # 1 building
        # 5 floors
        # 15 property units
        # 1 underground asset
        #
        # Total = 23
        self.assertEqual(response.count, 23)

        entity_types = [
            item["entity_type"]
            for item in response.data
        ]

        self.assertIn("parcel", entity_types)
        self.assertIn("building", entity_types)
        self.assertIn("floor", entity_types)
        self.assertIn("property_unit", entity_types)
        self.assertIn("underground_asset", entity_types)

    def test_find_entities_above_parcel(self) -> None:
        response = self.engine.find_entities_above_parcel("P002")

        self.assertTrue(response.success)

        # P002:
        #
        # 1 building
        # 5 above-ground floors
        # 15 property units
        #
        # Basement is excluded.
        #
        # Total = 21
        self.assertEqual(response.count, 21)

        floor_entities = [
            item
            for item in response.data
            if item["entity_type"] == "floor"
        ]

        self.assertEqual(len(floor_entities), 5)

        self.assertTrue(
            all(
                item["floor_type"] != "BASEMENT"
                for item in floor_entities
            )
        )

    def test_find_underground_assets_below(self) -> None:
        response = self.engine.find_underground_assets_below("P003")

        self.assertTrue(response.success)
        self.assertEqual(response.count, 1)

        self.assertEqual(
            response.data[0]["asset_id"],
            "UA002",
        )

    # --------------------------------------------------------------
    # Error handling
    # --------------------------------------------------------------

    def test_missing_parcel(self) -> None:
        response = self.engine.get_parcel("DOES_NOT_EXIST")

        self.assertFalse(response.success)
        self.assertEqual(response.count, 0)
        self.assertIsNotNone(response.error)

    def test_missing_building(self) -> None:
        response = self.engine.get_building("DOES_NOT_EXIST")

        self.assertFalse(response.success)
        self.assertEqual(response.count, 0)

    def test_missing_floor(self) -> None:
        response = self.engine.get_floor(
            "B001",
            99,
        )

        self.assertFalse(response.success)
        self.assertEqual(response.count, 0)

    def test_missing_property_unit(self) -> None:
        response = self.engine.get_property_unit(
            "DOES_NOT_EXIST"
        )

        self.assertFalse(response.success)
        self.assertEqual(response.count, 0)

    # --------------------------------------------------------------
    # Metadata / serialization
    # --------------------------------------------------------------

    def test_response_serialization(self) -> None:
        response = self.engine.get_property_unit(
            "B001_F03_U0302"
        )

        result = response.to_dict()

        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        self.assertIn("query_type", result)
        self.assertIn("count", result)
        self.assertIn("data", result)
        self.assertIn("entity_ids", result)
        self.assertIn("error", result)
        self.assertIn("metadata", result)

    def test_statistics(self) -> None:
        response = self.engine.get_statistics()

        self.assertTrue(response.success)

        self.assertEqual(
            response.data["parcels"],
            3,
        )

        self.assertEqual(
            response.data["buildings"],
            3,
        )

        self.assertEqual(
            response.data["property_units"],
            45,
        )


if __name__ == "__main__":
    unittest.main()