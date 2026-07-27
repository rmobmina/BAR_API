"""
Tests for the /umap_expression/<database>/<gene_id> endpoint.

Covers gene ID validation and unknown-database handling for the per-cell UMAP
coordinate/expression endpoint, plus the actual coords+expression merge logic
exercised against an in-memory SQLite engine standing in for the MySQL bind
(so the query/retry/merge code gets real coverage without needing a live
MySQL server, in CI or locally).
"""
from unittest import TestCase

from sqlalchemy import create_engine, text

from api import app, db
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

    def test_injection_attempt_rejected(self):
        """A SQL/script injection payload is rejected with 400 before any query runs.

        Uses a UNION SELECT payload rather than a quote-based one: markupsafe's
        escape() (applied before the injection check) HTML-entity-encodes quote
        characters, so a quote-reliant payload like "' OR '1'='1" no longer
        matches the injection regex by the time is_injection_attempt() runs.
        """
        response = self.client.get("/umap_expression/arabidopsis_NIE_umap/AT1G01010%20UNION%20SELECT")
        self.assertEqual(response.status_code, 400)


class TestUMAPExpressionDataRetrieval(TestCase):
    """
    Exercise the real query/retry/merge logic against an in-memory SQLite
    engine registered as the MySQL bind for one UMAP database, matching the
    real dump's schema and its all-uppercase AGI storage convention (see
    config/databases/arabidopsis_NIE_umap.sql).
    """

    TEST_DATABASE = "arabidopsis_NIE_umap"

    def setUp(self):
        self.client = app.test_client()
        self.engine = create_engine("sqlite:///:memory:")
        with self.engine.begin() as conn:
            conn.execute(text("CREATE TABLE umap_coords (cell_id INTEGER, umap_1 FLOAT, umap_2 FLOAT, cell_type TEXT)"))
            conn.execute(text(
                "INSERT INTO umap_coords VALUES "
                "(0, -3.696337, -0.631605, 'Vascular'), (1, 2.269168, 1.4399, 'Xylem.Parenchyma')"
            ))
            conn.execute(text("CREATE TABLE umap_expression (gene_id TEXT, expression TEXT)"))
            conn.execute(text("INSERT INTO umap_expression VALUES ('AT3G55980', '{\"0\": 1.5, \"1\": 2.5}')"))
        with app.app_context():
            db.engines[self.TEST_DATABASE] = self.engine

    def tearDown(self):
        with app.app_context():
            db.engines.pop(self.TEST_DATABASE, None)

    def test_merges_coords_and_expression(self):
        """Exact-case match: no retry needed, coords and expression merge by cell_id."""
        response = self.client.get(f"/umap_expression/{self.TEST_DATABASE}/AT3G55980")
        self.assertEqual(response.status_code, 200)
        body = response.json["data"]
        self.assertEqual(body["record_count"], 2)
        self.assertEqual(
            body["data"][0],
            {"umap_1": -3.696337, "umap_2": -0.631605, "expression": 1.5, "cell_type": "Vascular"},
        )
        self.assertEqual(body["data"][1]["expression"], 2.5)

    def test_case_insensitive_retry(self):
        """Lowercase input doesn't match the uppercase-stored row -- the uppercase retry does."""
        response = self.client.get(f"/umap_expression/{self.TEST_DATABASE}/at3g55980")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["data"]["record_count"], 2)

    def test_gene_not_found_returns_404(self):
        """A validly-formatted AGI with no matching row returns 404."""
        response = self.client.get(f"/umap_expression/{self.TEST_DATABASE}/AT1G01010")
        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.json["wasSuccessful"])

    def test_query_failure_returns_500(self):
        """A broken bind (tables missing) surfaces as a 500, not a crash."""
        broken_engine = create_engine("sqlite:///:memory:")
        with app.app_context():
            db.engines[self.TEST_DATABASE] = broken_engine
        response = self.client.get(f"/umap_expression/{self.TEST_DATABASE}/AT3G55980")
        self.assertEqual(response.status_code, 500)
        self.assertFalse(response.json["wasSuccessful"])
