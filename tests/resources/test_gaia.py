from api import app, db
from unittest import TestCase
from sqlalchemy.exc import UnboundExecutionError


class TestGaiaPublicationFiguresByGene(TestCase):
    def setUp(self):
        self.app_client = app.test_client()
        with app.app_context():
            try:
                self.gaia_is_mysql = db.engines["gaia"].dialect.name == "mysql"
            except (KeyError, UnboundExecutionError):
                self.gaia_is_mysql = False

    def _require_mysql(self):
        if not self.gaia_is_mysql:
            self.skipTest("requires MySQL gaia bind; skipped under SQLite harness")

    def test_publication_figures_by_gene_abi3(self):
        """ABI3 should surface OCR-detected figures grouped by PMC, exercising every
        fixture rule (match, word-boundary catch/reject, bare-name guard, null-url skip).
        :return:
        """
        self._require_mysql()
        response = self.app_client.get("/gaia/publication_figures_by_gene/ABI3")
        self.assertEqual(response.status_code, 200)

        body = response.json
        self.assertTrue(body["wasSuccessful"])
        data = body["data"]
        figures = data["figures"]

        # ABI3 returns two REAL pubs -> assert by set membership, not position.
        self.assertLessEqual({"PMC6403161", "PMC151246"}, set(figures))

        # PMC151246: abi3 OCR'd on f2 + f4 only (NOT f1/f3/f5).
        self.assertIn("PMC151246", figures)
        pmc151246_names = {f["img_name"] for f in figures["PMC151246"]["figures"]}
        self.assertIn("01-0441f2.jpg", pmc151246_names)
        self.assertIn("01-0441f4.jpg", pmc151246_names)
        self.assertNotIn("01-0441f1.jpg", pmc151246_names)
        self.assertNotIn("01-0441f3.jpg", pmc151246_names)
        self.assertNotIn("01-0441f5.jpg", pmc151246_names)

        # PMC6403161: word-boundary match must CATCH the gene:false word abi3/vp1 ->
        # fpls-10-00228-g003.jpg. Exact IN(...) would miss it -> this pins boundary-vs-exact.
        self.assertIn("PMC6403161", figures)
        pmc6403161_names = {f["img_name"] for f in figures["PMC6403161"]["figures"]}
        self.assertIn("fpls-10-00228-g003.jpg", pmc6403161_names)

        # Across all PMCs: gr1.jpg dropped (bare-name guard), nullfig.jpg dropped
        # (null img_url), gabitest.jpg dropped (gabi390_r boundary-rejected).
        all_names = {f["img_name"] for pmc in figures.values() for f in pmc["figures"]}
        self.assertNotIn("gr1.jpg", all_names)
        self.assertNotIn("nullfig.jpg", all_names)
        self.assertNotIn("gabitest.jpg", all_names)

        # allImageWords powers the gene-name filter.
        self.assertIn("abi3", data["allImageWords"])

        # Authors are attached per publication.
        self.assertIn("Finkelstein RR", figures["PMC151246"]["authors"])

    def test_publication_figures_by_gene_empty_payload(self):
        """A valid gene with no OCR-matched figures returns 200 with an empty payload,
        not a 404.
        :return:
        """
        self._require_mysql()
        response = self.app_client.get("/gaia/publication_figures_by_gene/NOMATCH4")
        self.assertEqual(response.status_code, 200)
        expected = {"wasSuccessful": True, "data": {"figures": {}, "allImageWords": {}}}
        self.assertEqual(response.json, expected)

    def test_publication_figures_by_gene_short_alias_34g(self):
        """A short (<=3 char) alias uses EXACT-IN matching, not the word-boundary regex.
        34G must match the OCR word '34g' exactly and reject the boundary-delimited decoy
        '34g/x' and the substring decoy 'x34gy'. Also covers the malformed (no-bbox) OCR
        entry -> the figure still returns with a clean bbox list (no None).
        :return:
        """
        self._require_mysql()
        response = self.app_client.get("/gaia/publication_figures_by_gene/34G")
        self.assertEqual(response.status_code, 200)

        body = response.json
        self.assertTrue(body["wasSuccessful"])
        figures = body["data"]["figures"]

        self.assertIn("PMC7000001", figures)
        names = {f["img_name"] for f in figures["PMC7000001"]["figures"]}

        # Exact match on '34g' returns its real figure (g002) and the malformed-bbox figure (g003).
        self.assertIn("fpls-11-01234-g002.jpg", names)
        self.assertIn("fpls-11-01234-g003.jpg", names)

        # Exact-IN must NOT match the boundary decoy '34g/x' (the regex WOULD have) nor the
        # substring decoy 'x34gy' (a LIKE would have) -> both figures absent.
        self.assertNotIn("fpls-11-01234-g005.jpg", names)
        self.assertNotIn("fpls-11-01234-g009.jpg", names)

        # Malformed OCR entry (imageName but no bbox) -> figure returns with a clean, None-free
        # bbox list (here empty, since its only OCR entry had no box).
        by_name = {f["img_name"]: f for f in figures["PMC7000001"]["figures"]}
        self.assertEqual(by_name["fpls-11-01234-g003.jpg"]["bbox"], [])
        for fig in figures["PMC7000001"]["figures"]:
            self.assertNotIn(None, fig["bbox"])

        # allImageWords keeps the malformed image's key but maps it to [] (not null, not absent),
        # so the gene-name filter still lists it without the frontend choking on a null box.
        words_34g = body["data"]["allImageWords"]["34g"]
        self.assertEqual(words_34g["fpls-11-01234-g003.jpg"], [])

    def test_publication_figures_by_gene_invalid_identifier(self):
        """An identifier failing the gaia alias check returns a 400 error.
        :return:
        """
        response = self.app_client.get("/gaia/publication_figures_by_gene/abc!def")
        expected = {"wasSuccessful": False, "error": "Invalid identifier"}
        self.assertEqual(response.json, expected)
