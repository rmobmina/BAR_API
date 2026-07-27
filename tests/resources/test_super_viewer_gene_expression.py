"""
Tests for the /super_viewer_gene_expression/expression/<database>/<gene_id> endpoint.

Covers gene ID validation for the SUPeR Viewer pseudobulk databases -- these
are gene-model-keyed (AGI/rice gene IDs directly, no probeset conversion),
unlike the older microarray sample_data databases. Actual data retrieval is
exercised in CI where the real MySQL dumps (config/databases/*_pseudobulk_dump.sql)
are loaded; locally we only verify the validation/error-mapping layer.
"""
from unittest import TestCase

from api import app


class TestSUPeRViewerGeneExpressionValidation(TestCase):
    """Validate that the endpoint accepts and rejects the right gene ID formats."""

    def setUp(self):
        self.client = app.test_client()

    def test_arabidopsis_agi_accepted(self):
        """A real Arabidopsis AGI is accepted for an arabidopsis pseudobulk database."""
        # AT1G01010 is the gene seeded in arabidopsis_NIE_pseudobulk_dump.sql
        response = self.client.get(
            "/super_viewer_gene_expression/expression/arabidopsis_NIE_pseudobulk/AT1G01010"
        )
        self.assertNotEqual(response.status_code, 400)

    def test_arabidopsis_agi_case_insensitive(self):
        """AGI IDs are accepted regardless of case."""
        response = self.client.get(
            "/super_viewer_gene_expression/expression/arabidopsis_NIE_pseudobulk/at1g01010"
        )
        self.assertNotEqual(response.status_code, 400)

    def test_invalid_arabidopsis_gene_rejected(self):
        """A clearly invalid gene ID is rejected with 400."""
        response = self.client.get(
            "/super_viewer_gene_expression/expression/arabidopsis_NIE_pseudobulk/NOTAGENEID"
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json["wasSuccessful"])

    def test_rice_gene_id_accepted(self):
        """A real rice gene ID is accepted for the rice pseudobulk database."""
        # Os01g0100100 is the gene seeded in rice_OW_pseudobulk_dump.sql
        response = self.client.get(
            "/super_viewer_gene_expression/expression/rice_OW_pseudobulk/Os01g0100100"
        )
        self.assertNotEqual(response.status_code, 400)

    def test_invalid_rice_gene_rejected(self):
        """An invalid rice gene ID is rejected with 400."""
        response = self.client.get(
            "/super_viewer_gene_expression/expression/rice_OW_pseudobulk/NOTAGENE"
        )
        self.assertEqual(response.status_code, 400)

    def test_all_pseudobulk_databases_registered(self):
        """Every SUPeR Viewer pseudobulk database is known to the endpoint (not a 400)."""
        databases_and_gene_ids = [
            ("arabidopsis_NIE_pseudobulk", "AT1G01010"),
            ("arabidopsis_flower_lee_pseudobulk", "AT1G01010"),
            ("arabidopsis_root_rs_pseudobulk", "AT1G01010"),
            ("arabidopsis_seed_martin_pseudobulk", "AT1G01010"),
            ("arabidopsis_silique_lee_pseudobulk", "AT1G01010"),
            ("arabidopsis_stem_lee_pseudobulk", "AT1G01010"),
            ("rice_OW_pseudobulk", "Os01g0100100"),
        ]
        for database, gene_id in databases_and_gene_ids:
            with self.subTest(database=database):
                response = self.client.get(
                    f"/super_viewer_gene_expression/expression/{database}/{gene_id}"
                )
                self.assertNotEqual(
                    response.status_code, 400, f"{database} unexpectedly rejected a valid-shaped gene ID"
                )

    def test_unknown_database_rejected(self):
        """An unknown database name returns a 400 error response."""
        response = self.client.get(
            "/super_viewer_gene_expression/expression/totally_unknown_database/AT1G01010"
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json["wasSuccessful"])
