"""
Tests for the /gene_expression/expression/<database>/<gene_id> endpoint.

Covers three important cases:
  1. Gene ID validation — valid/invalid inputs per database.
  2. Probeset ID input — actual probeset IDs from sample data (no AGI conversion needed).
  3. AGI input for Arabidopsis microarray databases — verifies the AGI→probeset lookup path
     is accepted (data retrieval itself is tested in CI where the lookup DB is present).

Sample probeset IDs are drawn from the JSON files in
api/random_rows_json/ to ensure we test with real IDs, not synthetic ones.
"""
from unittest import TestCase

from api import app
from api.utils.gene_id_utils import GeneIdUtils, DATABASE_EFP_PROJECT


class TestGeneExpressionValidation(TestCase):
    """Validate that the endpoint accepts and rejects the right gene ID formats."""

    def setUp(self):
        self.client = app.test_client()

    # --- Arabidopsis AGI input (microarray databases) ---

    def test_arabidopsis_agi_accepted_for_microarray_db(self):
        """An Arabidopsis AGI is accepted for a microarray-backed database."""
        # The endpoint validates the format; actual data retrieval depends on DB availability
        response = self.client.get("/gene_expression/expression/light_series/AT2G21130")
        # Should not be a 400 validation error
        self.assertNotEqual(response.status_code, 400)

    def test_arabidopsis_agi_case_insensitive(self):
        """AGI IDs are accepted regardless of case."""
        response = self.client.get("/gene_expression/expression/light_series/at2g21130")
        self.assertNotEqual(response.status_code, 400)

    def test_invalid_arabidopsis_gene_rejected(self):
        """A clearly invalid gene ID is rejected with 400."""
        response = self.client.get("/gene_expression/expression/light_series/NOTAGENEID")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json["wasSuccessful"])

    # --- Arabidopsis ATH1 probeset IDs (passed directly) ---

    def test_arabidopsis_probeset_accepted_light_series(self):
        """An ATH1 probeset ID is accepted for the light_series database."""
        # 263677_at is a real probe from light_series_test_data.json
        response = self.client.get("/gene_expression/expression/light_series/263677_at")
        self.assertNotEqual(response.status_code, 400)

    def test_arabidopsis_probeset_s_at_accepted(self):
        """A _s_at probeset ID is accepted for an Arabidopsis microarray database."""
        # 261283_s_at is a real probe from affydb_test_data.json
        response = self.client.get("/gene_expression/expression/affydb/261283_s_at")
        self.assertNotEqual(response.status_code, 400)

    def test_arabidopsis_probeset_accepted_atgenexp(self):
        """A numeric ATH1 probeset is accepted for the atgenexp database."""
        response = self.client.get("/gene_expression/expression/atgenexp/253680_at")
        self.assertNotEqual(response.status_code, 400)

    # --- Seedcoat CATMA/AROS probes ---

    def test_seedcoat_catma_probe_accepted(self):
        """A CATMA probe (At + 8 digits) is accepted for the seedcoat database."""
        # At30023977 is a real probe from seedcoat_test_data.json
        response = self.client.get("/gene_expression/expression/seedcoat/At30023977")
        self.assertNotEqual(response.status_code, 400)

    def test_seedcoat_aros_probe_accepted(self):
        """An AROS probe (non-digit + digits + underscore + digits) is accepted for seedcoat."""
        # A017813_01 is a real probe from seedcoat_test_data.json
        response = self.client.get("/gene_expression/expression/seedcoat/A017813_01")
        self.assertNotEqual(response.status_code, 400)

    def test_seedcoat_invalid_probe_rejected(self):
        """A random string is rejected for the seedcoat database."""
        response = self.client.get("/gene_expression/expression/seedcoat/NOTAPROBE")
        self.assertEqual(response.status_code, 400)

    # --- Barley microarray probesets ---

    def test_barley_probeset_accepted_mas(self):
        """A Contig*_at barley probeset is accepted for barley_mas."""
        # Contig7905_at is a real probe from barley_mas_test_data.json
        response = self.client.get("/gene_expression/expression/barley_mas/Contig7905_at")
        self.assertNotEqual(response.status_code, 400)

    def test_barley_probeset_accepted_rma(self):
        """Complex barley probesets are accepted for barley_rma."""
        # EBro06_SQ001_B02_at is a real probe from barley_rma_test_data.json
        response = self.client.get("/gene_expression/expression/barley_rma/EBro06_SQ001_B02_at")
        self.assertNotEqual(response.status_code, 400)

    def test_barley_invalid_probe_rejected(self):
        """An invalid ID is rejected for barley databases."""
        response = self.client.get("/gene_expression/expression/barley_mas/NOTAPROBE!!!")
        self.assertEqual(response.status_code, 400)

    # --- Rice microarray probesets ---

    def test_rice_mas_probeset_accepted(self):
        """A rice Os.*_at probeset is accepted for rice_mas."""
        # Os.17822.2.S1_s_at is a real probe from rice_mas_test_data.json
        response = self.client.get("/gene_expression/expression/rice_mas/Os.17822.2.S1_s_at")
        self.assertNotEqual(response.status_code, 400)

    def test_rice_rma_affx_probeset_accepted(self):
        """An OsAffx probeset is accepted for rice_rma."""
        # OsAffx.13653.1.S1_at is a real probe from rice_rma_test_data.json
        response = self.client.get("/gene_expression/expression/rice_rma/OsAffx.13653.1.S1_at")
        self.assertNotEqual(response.status_code, 400)

    def test_rice_gene_id_accepted(self):
        """A canonical LOC_Os rice gene ID is accepted for rice_mas."""
        response = self.client.get("/gene_expression/expression/rice_mas/LOC_Os01g01430")
        self.assertNotEqual(response.status_code, 400)

    def test_rice_invalid_id_rejected(self):
        """An invalid ID is rejected for rice databases."""
        response = self.client.get("/gene_expression/expression/rice_mas/NOTAPROBE")
        self.assertEqual(response.status_code, 400)

    # --- Medicago microarray probesets ---

    def test_medicago_mtr_probeset_accepted(self):
        """A Mtr probeset is accepted for medicago_mas."""
        # Mtr.44080.1.S1_at is a real probe from medicago_mas_test_data.json
        response = self.client.get("/gene_expression/expression/medicago_mas/Mtr.44080.1.S1_at")
        self.assertNotEqual(response.status_code, 400)

    def test_medicago_msa_probeset_accepted(self):
        """A Msa probeset is accepted for medicago_rma."""
        # Msa.959.1.S1_at is a real probe from medicago_mas_test_data.json
        response = self.client.get("/gene_expression/expression/medicago_rma/Msa.959.1.S1_at")
        self.assertNotEqual(response.status_code, 400)

    def test_medicago_sme_probeset_accepted(self):
        """A Sme probeset is accepted for medicago databases."""
        # Sme.396.1.S1_at is a real probe from medicago_rma_test_data.json
        response = self.client.get("/gene_expression/expression/medicago_rma/Sme.396.1.S1_at")
        self.assertNotEqual(response.status_code, 400)

    # --- Poplar microarray probesets ---

    def test_poplar_ptpaffx_probeset_accepted(self):
        """A PtpAffx probeset is accepted for the poplar database."""
        # PtpAffx.154622.1.S1_at is a real probe from poplar_test_data.json
        response = self.client.get("/gene_expression/expression/poplar/PtpAffx.154622.1.S1_at")
        self.assertNotEqual(response.status_code, 400)

    def test_poplar_ptp_s_at_probeset_accepted(self):
        """A PtpAffx _s_at probeset is accepted for the poplar database."""
        # PtpAffx.202274.1.S1_s_at is a real probe from poplar_test_data.json
        response = self.client.get(
            "/gene_expression/expression/poplar/PtpAffx.202274.1.S1_s_at"
        )
        self.assertNotEqual(response.status_code, 400)

    # --- Triticale microarray probesets ---

    def test_triticale_probeset_accepted(self):
        """A Ta.*_at triticale probeset is accepted for the triticale database."""
        # Ta.8002.1.S1_at is a real probe from triticale_test_data.json
        response = self.client.get("/gene_expression/expression/triticale/Ta.8002.1.S1_at")
        self.assertNotEqual(response.status_code, 400)

    # --- Unknown database ---

    def test_unknown_database_rejected(self):
        """An unknown database name returns an error response."""
        response = self.client.get(
            "/gene_expression/expression/totally_unknown_database/AT1G01010"
        )
        self.assertFalse(response.json.get("wasSuccessful", True))


class TestGeneIdUtilsDatabase(TestCase):
    """Unit tests for validate_gene_for_database() and DATABASE_EFP_PROJECT mapping."""

    def test_database_efp_project_has_microarray_dbs(self):
        """All expected microarray databases must have an eFP project mapping."""
        expected_dbs = [
            "affydb", "arabidopsis_ecotypes", "atgenexp", "light_series",
            "seedcoat",
            "barley_mas", "barley_rma",
            "rice_mas", "rice_rma",
            "medicago_mas", "medicago_rma",
            "poplar",
            "triticale", "triticale_mas",
        ]
        for db in expected_dbs:
            self.assertIn(db, DATABASE_EFP_PROJECT, f"Missing DATABASE_EFP_PROJECT entry for {db}")

    def test_validate_arabidopsis_agi(self):
        """AGI IDs are valid for arabidopsis microarray databases."""
        self.assertTrue(GeneIdUtils.validate_gene_for_database("AT1G01010", "light_series"))
        self.assertTrue(GeneIdUtils.validate_gene_for_database("AT2G21130", "affydb"))

    def test_validate_arabidopsis_probeset(self):
        """ATH1 probeset IDs are valid for arabidopsis microarray databases."""
        self.assertTrue(GeneIdUtils.validate_gene_for_database("267643_at", "light_series"))
        self.assertTrue(GeneIdUtils.validate_gene_for_database("261283_s_at", "affydb"))

    def test_validate_seedcoat_catma_probe(self):
        """CATMA probe IDs are valid for the seedcoat database."""
        self.assertTrue(GeneIdUtils.validate_gene_for_database("At30023977", "seedcoat"))
        self.assertTrue(GeneIdUtils.validate_gene_for_database("At30027789", "seedcoat"))

    def test_validate_seedcoat_aros_probe(self):
        """AROS probe IDs are valid for the seedcoat database."""
        self.assertTrue(GeneIdUtils.validate_gene_for_database("A017813_01", "seedcoat"))

    def test_validate_barley_probeset(self):
        """Barley probeset IDs are valid for barley microarray databases."""
        self.assertTrue(GeneIdUtils.validate_gene_for_database("Contig7905_at", "barley_mas"))
        self.assertTrue(
            GeneIdUtils.validate_gene_for_database("EBro06_SQ001_B02_at", "barley_rma")
        )

    def test_validate_rice_probeset(self):
        """Rice probeset IDs are valid for rice microarray databases."""
        self.assertTrue(GeneIdUtils.validate_gene_for_database("Os.17822.2.S1_s_at", "rice_mas"))
        self.assertTrue(GeneIdUtils.validate_gene_for_database("OsAffx.13653.1.S1_at", "rice_rma"))

    def test_validate_medicago_probeset(self):
        """Medicago probeset IDs are valid for medicago microarray databases."""
        self.assertTrue(GeneIdUtils.validate_gene_for_database("Mtr.44080.1.S1_at", "medicago_mas"))
        self.assertTrue(GeneIdUtils.validate_gene_for_database("Sme.396.1.S1_at", "medicago_rma"))

    def test_validate_poplar_probeset(self):
        """Poplar probeset IDs are valid for the poplar microarray database."""
        self.assertTrue(GeneIdUtils.validate_gene_for_database("PtpAffx.154622.1.S1_at", "poplar"))

    def test_validate_triticale_probeset(self):
        """Triticale probeset IDs are valid for the triticale database."""
        self.assertTrue(GeneIdUtils.validate_gene_for_database("Ta.8002.1.S1_at", "triticale"))

    def test_is_probeset_id_detects_catma_probe(self):
        """CATMA probes (At + 8 digits) are recognised as probeset IDs."""
        self.assertTrue(GeneIdUtils.is_probeset_id("At30023977"))
        self.assertTrue(GeneIdUtils.is_probeset_id("At30027789"))

    def test_is_probeset_id_detects_affymetrix_probe(self):
        """Standard _at probes are recognised as probeset IDs."""
        self.assertTrue(GeneIdUtils.is_probeset_id("267643_at"))
        self.assertTrue(GeneIdUtils.is_probeset_id("Contig7905_at"))
        self.assertTrue(GeneIdUtils.is_probeset_id("Os.17822.2.S1_s_at"))

    def test_is_probeset_id_rejects_gene_ids(self):
        """Canonical gene IDs are NOT treated as probeset IDs."""
        self.assertFalse(GeneIdUtils.is_probeset_id("AT1G01010"))
        self.assertFalse(GeneIdUtils.is_probeset_id("LOC_Os01g01430"))
        self.assertFalse(GeneIdUtils.is_probeset_id("randomjunk"))

    def test_validate_gene_for_non_efp_database_falls_back_to_species(self):
        """Non-microarray databases use species-based validation."""
        self.assertTrue(GeneIdUtils.validate_gene_for_database("AT1G01010", "klepikova"))
        self.assertFalse(GeneIdUtils.validate_gene_for_database("NOTAGENEID", "klepikova"))
