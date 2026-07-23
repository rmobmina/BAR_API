from api import app
from unittest import TestCase
import json


class TestIntegrations(TestCase):
    def setUp(self):
        self.app_client = app.test_client()

    def test_get_loc(self):
        """
        This function test retrieving subcellular localizations for various species' genes via GET.
        """

        # Rice isoform-suffixed IDs (LOC_Os01g52560.1) are no longer accepted:
        # is_rice_gene_valid now delegates to Vincent's tested efp_rice registry
        # pattern, which -- unlike the old hand-written regex -- has no isoform
        # suffix variant for the LOC_Os form. This is an accepted, deliberate
        # trade-off for a single source of truth on gene ID validation.
        response = self.app_client.get("/loc/rice/LOC_Os01g52560.1")
        expected = {"wasSuccessful": False, "error": "Invalid species or gene ID"}
        self.assertEqual(response.json, expected)

        # Invalid species
        response = self.app_client.get("/loc/poplar/LOC_Os01g52560.1")
        expected = {"wasSuccessful": False, "error": "Invalid species or gene ID"}
        self.assertEqual(response.json, expected)

        # Invalid gene id
        response = self.app_client.get("/loc/rice/abc")
        expected = {"wasSuccessful": False, "error": "Invalid species or gene ID"}
        self.assertEqual(response.json, expected)

        # Also rejected at validation now, for the same reason as above
        response = self.app_client.get("/loc/rice/LOC_Os01g52561.1")
        expected = {"wasSuccessful": False, "error": "Invalid species or gene ID"}
        self.assertEqual(response.json, expected)

    def test_post_loc(self):
        """
        This function test retrieving subcellular localizations for various species' genes via POST.
        """

        # Rice isoform-suffixed IDs are no longer accepted -- see test_get_loc
        # for why (is_rice_gene_valid now delegates to Vincent's efp_rice
        # registry pattern, which has no LOC_Os isoform-suffix variant).
        response = self.app_client.post(
            "/loc/",
            json={"species": "rice", "genes": ["LOC_Os01g01080.1", "LOC_Os01g52560.1"]},
        )
        data = json.loads(response.get_data(as_text=True))
        expected = {"wasSuccessful": False, "error": "Invalid gene id"}
        self.assertEqual(data, expected)

        # Invalid species
        response = self.app_client.post(
            "/loc/",
            json={
                "species": "poplar",
                "genes": ["LOC_Os01g01080.1", "LOC_Os01g52560.1"],
            },
        )
        data = json.loads(response.get_data(as_text=True))
        expected = {"wasSuccessful": False, "error": "Invalid species"}
        self.assertEqual(data, expected)

        # Invalid gene ID
        response = self.app_client.post("/loc/", json={"species": "rice", "genes": ["abc", "xyz"]})
        data = json.loads(response.get_data(as_text=True))
        expected = {"wasSuccessful": False, "error": "Invalid gene id"}
        self.assertEqual(data, expected)

        # Also rejected at validation now, for the same reason as above
        response = self.app_client.post(
            "/loc/",
            json={"species": "rice", "genes": ["LOC_Os01g01085.1", "LOC_Os01g52565.1"]},
        )
        data = json.loads(response.get_data(as_text=True))
        expected = {"wasSuccessful": False, "error": "Invalid gene id"}
        self.assertEqual(data, expected)
