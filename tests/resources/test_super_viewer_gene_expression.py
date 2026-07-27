"""
Tests for the /super_viewer_gene_expression/expression/<database>/<gene_id> endpoint.

Covers gene ID validation for the SUPeR Viewer pseudobulk databases -- these
are gene-model-keyed (AGI/rice gene IDs directly, no probeset conversion),
unlike the older microarray sample_data databases. Actual data retrieval against
a live MySQL bind is exercised in CI where the real dumps are loaded; here the
query_efp_database_dynamic() boundary is mocked so the endpoint's own
validation/response-mapping/mean-split logic gets exercised deterministically
without needing a live database.
"""
from unittest import TestCase
from unittest.mock import patch

from api import app
from api.resources.super_viewer_gene_expression import _split_rows


class TestSplitRows(TestCase):
    """Unit tests for _split_rows() -- separates the Mean_CTRL row from per-tissue rows."""

    def test_splits_mean_ctrl_from_tissue_rows(self):
        rows = [
            {"name": "D0_Mesophyll", "value": "0.03"},
            {"name": "Mean_CTRL", "value": "0.05"},
            {"name": "W0_Vascular", "value": "0.02"},
        ]
        tissue_rows, mean_row = _split_rows(rows)
        self.assertEqual(
            tissue_rows, [{"name": "D0_Mesophyll", "value": "0.03"}, {"name": "W0_Vascular", "value": "0.02"}]
        )
        self.assertEqual(mean_row, {"name": "Mean_CTRL", "value": "0.05"})

    def test_no_mean_ctrl_row_present(self):
        """Datasets that predate the Mean_CTRL rollout have no such row -- mean_row is None."""
        rows = [{"name": "D0_Mesophyll", "value": "0.03"}]
        tissue_rows, mean_row = _split_rows(rows)
        self.assertEqual(tissue_rows, rows)
        self.assertIsNone(mean_row)

    def test_empty_rows(self):
        tissue_rows, mean_row = _split_rows([])
        self.assertEqual(tissue_rows, [])
        self.assertIsNone(mean_row)


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

    def test_injection_attempt_rejected(self):
        """A SQL/script injection payload is rejected with 400 before any query runs.

        Uses a UNION SELECT payload rather than a quote-based one: markupsafe's
        escape() (applied before the injection check) HTML-entity-encodes quote
        characters, so a quote-reliant payload like "' OR '1'='1" no longer
        matches the injection regex by the time is_injection_attempt() runs.
        """
        response = self.client.get(
            "/super_viewer_gene_expression/expression/arabidopsis_NIE_pseudobulk/"
            "AT1G01010%20UNION%20SELECT"
        )
        self.assertEqual(response.status_code, 400)


class TestSUPeRViewerGeneExpressionDataRetrieval(TestCase):
    """Exercise the success/error response mapping by mocking query_efp_database_dynamic."""

    def setUp(self):
        self.client = app.test_client()

    @patch("api.resources.super_viewer_gene_expression.query_efp_database_dynamic")
    def test_success_splits_mean_ctrl_from_tissue_rows(self, mock_query):
        mock_query.return_value = {
            "success": True,
            "data": [
                {"name": "D0_Mesophyll", "value": "0.03"},
                {"name": "Mean_CTRL", "value": "0.05"},
            ],
        }
        response = self.client.get(
            "/super_viewer_gene_expression/expression/arabidopsis_NIE_pseudobulk/AT1G01010"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json["wasSuccessful"])
        self.assertEqual(response.json["data"]["expression"], [{"name": "D0_Mesophyll", "value": "0.03"}])
        self.assertEqual(response.json["data"]["mean_expression"], {"name": "Mean_CTRL", "value": "0.05"})
        mock_query.assert_called_once_with("arabidopsis_NIE_pseudobulk", "AT1G01010")

    @patch("api.resources.super_viewer_gene_expression.query_efp_database_dynamic")
    def test_success_without_mean_ctrl_row(self, mock_query):
        mock_query.return_value = {
            "success": True,
            "data": [{"name": "D0_Mesophyll", "value": "0.03"}],
        }
        response = self.client.get(
            "/super_viewer_gene_expression/expression/arabidopsis_NIE_pseudobulk/AT1G01010"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json["data"]["mean_expression"])

    @patch("api.resources.super_viewer_gene_expression.query_efp_database_dynamic")
    def test_probeset_shaped_id_used_directly_without_normalisation(self, mock_query):
        """A probeset-shaped ID skips species validation/normalisation entirely."""
        mock_query.return_value = {"success": True, "data": []}
        self.client.get(
            "/super_viewer_gene_expression/expression/arabidopsis_NIE_pseudobulk/267643_at"
        )
        mock_query.assert_called_once_with("arabidopsis_NIE_pseudobulk", "267643_at")

    @patch("api.resources.super_viewer_gene_expression.query_efp_database_dynamic")
    def test_404_when_gene_not_found(self, mock_query):
        mock_query.return_value = {"success": False, "error_code": 404}
        response = self.client.get(
            "/super_viewer_gene_expression/expression/arabidopsis_NIE_pseudobulk/AT1G01010"
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.json["wasSuccessful"])

    @patch("api.resources.super_viewer_gene_expression.query_efp_database_dynamic")
    def test_503_when_database_unavailable(self, mock_query):
        mock_query.return_value = {"success": False, "error_code": 503}
        response = self.client.get(
            "/super_viewer_gene_expression/expression/arabidopsis_NIE_pseudobulk/AT1G01010"
        )
        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.json["wasSuccessful"])

    @patch("api.resources.super_viewer_gene_expression.query_efp_database_dynamic")
    def test_500_on_unexpected_error(self, mock_query):
        mock_query.return_value = {"success": False, "error_code": 500}
        response = self.client.get(
            "/super_viewer_gene_expression/expression/arabidopsis_NIE_pseudobulk/AT1G01010"
        )
        self.assertEqual(response.status_code, 500)
        self.assertFalse(response.json["wasSuccessful"])
