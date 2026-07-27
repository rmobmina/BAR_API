"""
Tests for the /umap_expression/<database>/<gene_id> endpoint.

Covers gene ID validation and unknown-database handling for the per-cell UMAP
coordinate/expression endpoint. Actual coordinate/expression retrieval is
exercised in CI where the real MySQL dumps (config/databases/*_umap.sql) are
loaded; locally we only verify the validation/error-mapping layer.
"""
from unittest import TestCase

from api import app
from api.resources.umap_expression import UMAP_DATABASE_SPECIES


class TestUMAPExpressionValidation(TestCase):
    """Validate that the endpoint accepts and rejects the right gene ID formats."""

    def setUp(self):
        self.client = app.test_client()

    def test_arabidopsis_agi_accepted(self):
        """A real Arabidopsis AGI is accepted for an arabidopsis UMAP database."""
        # AT3G55980 is the gene seeded in arabidopsis_NIE_umap.sql
        response = self.client.get("/umap_expression/arabidopsis_NIE_umap/AT3G55980")
        self.assertNotEqual(response.status_code, 400)

    def test_arabidopsis_agi_case_insensitive(self):
        """AGI IDs are accepted regardless of case."""
        response = self.client.get("/umap_expression/arabidopsis_NIE_umap/at3g55980")
        self.assertNotEqual(response.status_code, 400)

    def test_invalid_arabidopsis_gene_rejected(self):
        """A clearly invalid gene ID is rejected with 400."""
        response = self.client.get("/umap_expression/arabidopsis_NIE_umap/NOTAGENEID")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json["wasSuccessful"])

    def test_rice_gene_id_accepted(self):
        """A real rice gene ID is accepted for the rice UMAP database."""
        # Os10g0168500 is the gene seeded in rice_OW_umap.sql
        response = self.client.get("/umap_expression/rice_OW_umap/Os10g0168500")
        self.assertNotEqual(response.status_code, 400)

    def test_invalid_rice_gene_rejected(self):
        """An invalid rice gene ID is rejected with 400."""
        response = self.client.get("/umap_expression/rice_OW_umap/NOTAGENE")
        self.assertEqual(response.status_code, 400)

    def test_all_umap_databases_registered(self):
        """Every SUPeR Viewer UMAP database is known to the endpoint (not a 400)."""
        databases_and_gene_ids = {
            "arabidopsis_NIE_umap": "AT3G55980",
            "arabidopsis_flower_lee_umap": "AT3G15510",
            "arabidopsis_root_shahan_umap": "AT1G79580",
            "arabidopsis_seed_martin_umap": "AT2G42840",
            "arabidopsis_silique_lee_umap": "AT3G24140",
            "arabidopsis_stem_lee_umap": "AT5G26000",
            "rice_OW_umap": "Os10g0168500",
        }
        self.assertEqual(set(databases_and_gene_ids), set(UMAP_DATABASE_SPECIES))
        for database, gene_id in databases_and_gene_ids.items():
            with self.subTest(database=database):
                response = self.client.get(f"/umap_expression/{database}/{gene_id}")
                self.assertNotEqual(
                    response.status_code, 400, f"{database} unexpectedly rejected a valid-shaped gene ID"
                )

    def test_unknown_database_rejected(self):
        """An unknown UMAP database name returns a 400 error response."""
        response = self.client.get("/umap_expression/totally_unknown_database/AT1G01010")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json["wasSuccessful"])
