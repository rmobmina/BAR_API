from unittest import TestCase
from api.utils.bar_utils import BARUtils, EFP_PROJECT_REGEXES


class UtilsUnitTest(TestCase):
    def test_error_exit(self):
        msg = "A test error message"
        result = BARUtils.error_exit(msg)
        expected = {"wasSuccessful": False, "error": msg}
        self.assertEqual(result, expected)

    def test_successful_exit(self):
        msg = "A successful test message"
        result = BARUtils.success_exit(msg)
        expected = {"wasSuccessful": True, "data": msg}
        self.assertEqual(result, expected)

    def test_is_arabidopsis_gene_valid(self):
        # Valid gene
        result = BARUtils.is_arabidopsis_gene_valid("At1g01010")
        self.assertTrue(result)
        result = BARUtils.is_arabidopsis_gene_valid("At1g01010.1")
        self.assertTrue(result)

        # Invalid gene
        result = BARUtils.is_arabidopsis_gene_valid("abc")
        self.assertFalse(result)
        result = BARUtils.is_arabidopsis_gene_valid("At1g01010.11")
        self.assertFalse(result)

    def test_is_brassica_rapa_gene_valid(self):
        # Valid gene
        result = BARUtils.is_brassica_rapa_gene_valid("BraA01g000010")
        self.assertTrue(result)

        # Invalid gene
        result = BARUtils.is_brassica_rapa_gene_valid("abc")
        self.assertFalse(result)

    def test_is_grape_gene_valid(self):
        result = BARUtils.is_grape_gene_valid("VIT_00s0120g00060")
        self.assertTrue(result)

        # Invalid gene
        result = BARUtils.is_grape_gene_valid("abc")
        self.assertFalse(result)

    def test_is_kalanchoe_gene_valid(self):
        # Valid gene
        result = BARUtils.is_kalanchoe_gene_valid("Kaladp0001s0001")
        self.assertTrue(result)

        # Invalid gene
        result = BARUtils.is_kalanchoe_gene_valid("abc")
        self.assertFalse(result)

    def test_is_phelipanche_gene_valid(self):
        # Valid gene
        result = BARUtils.is_phelipanche_gene_valid("OrAeBC5_9992.10")
        self.assertTrue(result)

        # Invalid gene
        result = BARUtils.is_phelipanche_gene_valid("abc")
        self.assertFalse(result)

    def test_is_physcomitrella_gene_valid(self):
        # Valid gene
        result = BARUtils.is_physcomitrella_gene_valid("Pp1s9_70V6.1")
        self.assertTrue(result)

        # Invalid gene
        result = BARUtils.is_physcomitrella_gene_valid("abc")
        self.assertFalse(result)

    def test_is_selaginella_gene_valid(self):
        # Valid gene
        result = BARUtils.is_selaginella_gene_valid("Smo402070")
        self.assertTrue(result)

        # Invalid gene
        result = BARUtils.is_selaginella_gene_valid("abc")
        self.assertFalse(result)

    def test_is_strawberry_gene_valid(self):
        # Valid gene
        result = BARUtils.is_strawberry_gene_valid("FvH4_1g00010")
        self.assertTrue(result)

        # Invalid gene
        result = BARUtils.is_strawberry_gene_valid("abc")
        self.assertFalse(result)

    def test_is_striga_gene_valid(self):
        # Valid gene
        result = BARUtils.is_striga_gene_valid("StHeBC3_9993.10")
        self.assertTrue(result)

        # Invalid gene
        result = BARUtils.is_striga_gene_valid("abc")
        self.assertFalse(result)

    def test_is_triphysaria_gene_valid(self):
        # Valid gene
        result = BARUtils.is_triphysaria_gene_valid("TrVeBC3_9999.18")
        self.assertTrue(result)

        # Invalid gene
        result = BARUtils.is_triphysaria_gene_valid("abc")
        self.assertFalse(result)

    def test_is_tomato_gene_valid(self):
        # For some reason, coverage is saying that we need this test
        result = BARUtils.is_tomato_gene_valid("Solyc04g014530")
        self.assertTrue(result)

    def test_is_integer(self):
        # Valid result
        result = BARUtils.is_integer("5")
        self.assertTrue(result)

        # Valid but too large
        result = BARUtils.is_integer("99999999999999")
        self.assertFalse(result)

        # Invalid
        result = BARUtils.is_integer("abc")
        self.assertFalse(result)

    def test_is_poplar_gene_valid(self):
        # Valid gene
        result = BARUtils.is_poplar_gene_valid("Potri.019G123900.1")
        self.assertTrue(result)

        # Invalid gene
        result = BARUtils.is_poplar_gene_valid("abc")
        self.assertFalse(result)

    def test_is_sorghum_gene_valid(self):
        # Valid gene
        result = BARUtils.is_sorghum_gene_valid("Sobic.001G000100")
        self.assertTrue(result)

        # Invalid gene
        result = BARUtils.is_sorghum_gene_valid("abc")
        self.assertFalse(result)

    def test_format_poplar(self):
        # Test format
        result = BARUtils.format_poplar("potri.019g123900.1")
        expected = "Potri.019G123900.1"
        self.assertEqual(result, expected)

    def test_efp_project_regexes_exist(self):
        """All expected eFP project keys must be present in EFP_PROJECT_REGEXES."""
        required = [
            "efp", "efp_arabidopsis", "efp_seedcoat",
            "efp_barley", "efpbarley",
            "efp_rice", "efprice",
            "efp_medicago", "efpmedicago",
            "efp_poplar", "efppop",
            "efp_soybean", "efpsoybean",
            "efp_maize", "maizeefp",
            "efp_triticale",
            "efp_human",
        ]
        for key in required:
            self.assertIn(key, EFP_PROJECT_REGEXES, f"Missing eFP project key: {key}")

    def test_is_efp_gene_valid_arabidopsis(self):
        """efp_arabidopsis accepts AGI, ATH1 probeset IDs, and standalone numerics."""
        # Valid canonical AGI gene IDs
        self.assertTrue(BARUtils.is_efp_gene_valid("AT2G21130", "efp_arabidopsis"))
        self.assertTrue(BARUtils.is_efp_gene_valid("At1g01010", "efp_arabidopsis"))
        self.assertTrue(BARUtils.is_efp_gene_valid("AtCg00020", "efp_arabidopsis"))

        # Valid Arabidopsis ATH1 probeset IDs (from sample data)
        self.assertTrue(BARUtils.is_efp_gene_valid("267643_at", "efp_arabidopsis"))
        self.assertTrue(BARUtils.is_efp_gene_valid("267644_s_at", "efp_arabidopsis"))
        self.assertTrue(BARUtils.is_efp_gene_valid("261283_s_at", "efp_arabidopsis"))
        self.assertTrue(BARUtils.is_efp_gene_valid("253680_at", "efp_arabidopsis"))

        # Valid standalone numeric IDs
        self.assertTrue(BARUtils.is_efp_gene_valid("267643", "efp_arabidopsis"))

        # Invalid IDs
        self.assertFalse(BARUtils.is_efp_gene_valid("9T2G21130", "efp_arabidopsis"))
        self.assertFalse(BARUtils.is_efp_gene_valid("AT2G2113X", "efp_arabidopsis"))
        self.assertFalse(BARUtils.is_efp_gene_valid("Solyc04g054700", "efp_arabidopsis"))
        self.assertFalse(BARUtils.is_efp_gene_valid("randomjunk", "efp_arabidopsis"))

    def test_is_efp_gene_valid_seedcoat(self):
        """efp_seedcoat accepts AGI, ATH1 probesets, CATMA probes, and AROS probes."""
        self.assertTrue(BARUtils.is_efp_gene_valid("At1g01010", "efp_seedcoat"))
        self.assertTrue(BARUtils.is_efp_gene_valid("At30023977", "efp_seedcoat"))
        self.assertTrue(BARUtils.is_efp_gene_valid("At30027789", "efp_seedcoat"))
        self.assertTrue(BARUtils.is_efp_gene_valid("A017813_01", "efp_seedcoat"))
        self.assertTrue(BARUtils.is_efp_gene_valid("A006881_01", "efp_seedcoat"))
        self.assertFalse(BARUtils.is_efp_gene_valid("randomjunk", "efp_seedcoat"))

    def test_is_efp_gene_valid_barley(self):
        """efp_barley accepts barley gene IDs and Affymetrix barley probeset IDs."""
        # Probeset IDs from barley_mas and barley_rma sample data
        self.assertTrue(BARUtils.is_efp_gene_valid("Contig7905_at", "efp_barley"))
        self.assertTrue(BARUtils.is_efp_gene_valid("Contig440_s_at", "efp_barley"))
        self.assertTrue(BARUtils.is_efp_gene_valid("EBro06_SQ001_B02_at", "efp_barley"))
        self.assertTrue(BARUtils.is_efp_gene_valid("HVSMEi0007J05r2_at", "efp_barley"))
        self.assertTrue(BARUtils.is_efp_gene_valid("Contig12089_at", "efp_barley"))
        # efpbarley alias
        self.assertTrue(BARUtils.is_efp_gene_valid("Contig7905_at", "efpbarley"))

        self.assertFalse(BARUtils.is_efp_gene_valid("AT1G01010", "efp_barley"))
        self.assertFalse(BARUtils.is_efp_gene_valid("randomjunk", "efp_barley"))

    def test_is_efp_gene_valid_rice(self):
        """efp_rice accepts canonical rice gene IDs and rice array probeset IDs."""
        self.assertTrue(BARUtils.is_efp_gene_valid("LOC_Os01g01430", "efp_rice"))
        self.assertTrue(BARUtils.is_efp_gene_valid("Os.17822.2.S1_s_at", "efp_rice"))
        self.assertTrue(BARUtils.is_efp_gene_valid("OsAffx.4511.1.S1_s_at", "efp_rice"))
        self.assertTrue(BARUtils.is_efp_gene_valid("Os.12223.2.S1_at", "efp_rice"))
        # efprice alias
        self.assertTrue(BARUtils.is_efp_gene_valid("LOC_Os01g01430", "efprice"))

        self.assertFalse(BARUtils.is_efp_gene_valid("AT1G01010", "efp_rice"))
        self.assertFalse(BARUtils.is_efp_gene_valid("randomjunk", "efp_rice"))

    def test_is_efp_gene_valid_medicago(self):
        """efp_medicago accepts canonical Medicago gene IDs and Medicago array probeset IDs."""
        self.assertTrue(BARUtils.is_efp_gene_valid("Medtr1g018805", "efp_medicago"))
        self.assertTrue(BARUtils.is_efp_gene_valid("Mtr.44080.1.S1_at", "efp_medicago"))
        self.assertTrue(BARUtils.is_efp_gene_valid("Msa.959.1.S1_at", "efp_medicago"))
        self.assertTrue(BARUtils.is_efp_gene_valid("Sme.396.1.S1_at", "efp_medicago"))
        # _s_at variants must also match (e.g. Mtr.50680.1.S1_s_at from medicago_rma)
        self.assertTrue(BARUtils.is_efp_gene_valid("Mtr.50680.1.S1_s_at", "efp_medicago"))
        # efpmedicago alias
        self.assertTrue(BARUtils.is_efp_gene_valid("Medtr1g018805", "efpmedicago"))

        self.assertFalse(BARUtils.is_efp_gene_valid("AT1G01010", "efp_medicago"))
        self.assertFalse(BARUtils.is_efp_gene_valid("randomjunk", "efp_medicago"))

    def test_is_efp_gene_valid_poplar(self):
        """efp_poplar accepts Potri gene IDs and poplar array probeset IDs."""
        self.assertTrue(BARUtils.is_efp_gene_valid("Potri.019G123900.1", "efp_poplar"))
        self.assertTrue(BARUtils.is_efp_gene_valid("PtpAffx.154622.1.S1_at", "efp_poplar"))
        self.assertTrue(BARUtils.is_efp_gene_valid("PtpAffx.37687.1.S1_at", "efp_poplar"))
        self.assertTrue(BARUtils.is_efp_gene_valid("PtpAffx.202274.1.S1_s_at", "efp_poplar"))
        # efppop alias
        self.assertTrue(BARUtils.is_efp_gene_valid("PtpAffx.154622.1.S1_at", "efppop"))

        self.assertFalse(BARUtils.is_efp_gene_valid("AT1G01010", "efp_poplar"))
        self.assertFalse(BARUtils.is_efp_gene_valid("randomjunk", "efp_poplar"))

    def test_is_efp_gene_valid_triticale(self):
        """efp_triticale accepts Ta.* and TaAffx.* probeset IDs (both occur in data)."""
        self.assertTrue(BARUtils.is_efp_gene_valid("Ta.8002.1.S1_at", "efp_triticale"))
        # TaAffx probes from triticale_test_data.json — require TaAffx prefix support
        self.assertTrue(BARUtils.is_efp_gene_valid("TaAffx.54155.1.S1_at", "efp_triticale"))
        self.assertTrue(BARUtils.is_efp_gene_valid("TaAffx.6560.1.S1_at", "efp_triticale"))
        self.assertTrue(BARUtils.is_efp_gene_valid("Ta.3469.1.A1_at", "efp_triticale"))

        self.assertFalse(BARUtils.is_efp_gene_valid("randomjunk", "efp_triticale"))
        self.assertFalse(BARUtils.is_efp_gene_valid("AT1G01010", "efp_triticale"))

    def test_is_efp_gene_valid_unknown_project(self):
        """Unknown eFP project returns False regardless of gene ID."""
        self.assertFalse(BARUtils.is_efp_gene_valid("AT1G01010", "efp_unknown_species"))
