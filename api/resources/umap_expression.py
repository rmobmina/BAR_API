import json

from flask_restx import Namespace, Resource
from markupsafe import escape
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api import db
from api.utils.bar_utils import BARUtils
from api.utils.gene_id_utils import GeneIdUtils

umap_expression = Namespace(
    "UMAP Expression",
    description="Per-cell UMAP coordinates and expression data for SUPeR Viewer",
    path="/umap_expression",
)

# Maps UMAP database names to their species. Add a new entry here whenever a
# new UMAP dump is generated. These databases are queried directly (raw SQL
# against umap_coords/umap_expression) rather than through the shared
# sample_data schema catalog, so they are intentionally not part of
# combined_master.json / SIMPLE_EFP_DATABASE_SCHEMAS.
UMAP_DATABASE_SPECIES: dict[str, str] = {
    "rice_OW_umap": "rice",
    "arabidopsis_NIE_umap": "arabidopsis",
    "arabidopsis_root_shahan_umap": "arabidopsis",
    "arabidopsis_seed_martin_umap": "arabidopsis",
    "arabidopsis_flower_lee_umap": "arabidopsis",
    "arabidopsis_silique_lee_umap": "arabidopsis",
    "arabidopsis_stem_lee_umap": "arabidopsis",
}

_EXPRESSION_SQL = text("SELECT expression FROM umap_expression WHERE gene_id = :gene_id")
_COORDS_SQL = text("SELECT cell_id, umap_1, umap_2, cell_type FROM umap_coords ORDER BY cell_id")


def _fetch_expression_row(engine, gene_id):
    """Look up the expression JSON blob for gene_id, retrying uppercase
    (some datasets store IDs in uppercase).

    :returns: (row, error_response) -- exactly one of the two is None.
    """
    try:
        with Session(engine) as session:
            row = session.execute(_EXPRESSION_SQL, {"gene_id": gene_id}).first()
            if row is None:
                row = session.execute(_EXPRESSION_SQL, {"gene_id": gene_id.upper()}).first()
    except SQLAlchemyError:
        return None, (BARUtils.error_exit("Database query failed"), 500)

    if row is None:
        return None, (BARUtils.error_exit("No data found for the given gene"), 404)
    return row, None


def _fetch_coords(engine):
    """Return every UMAP coordinate row (same for every gene), or an error response.

    :returns: (rows, error_response) -- exactly one of the two is None.
    """
    try:
        with Session(engine) as session:
            return session.execute(_COORDS_SQL).all(), None
    except SQLAlchemyError:
        return None, (BARUtils.error_exit("Database query failed"), 500)


def _merge_coords_and_expression(coords, expr_map):
    """Zip UMAP coordinates with each cell's expression value, keyed by cell_id."""
    return [
        {
            "umap_1": float(c.umap_1),
            "umap_2": float(c.umap_2),
            "expression": float(expr_map.get(str(c.cell_id), 0.0)),
            "cell_type": str(c.cell_type),
        }
        for c in coords
    ]


@umap_expression.route("/<string:database>/<string:gene_id>")
@umap_expression.doc(description="Retrieve per-cell UMAP coordinates and expression values for a gene.")
@umap_expression.param(
    "gene_id",
    "Gene ID (e.g. AT1G01010 for Arabidopsis, Os10g0168500 for rice)",
    _in="path",
    default="Os10g0168500",
)
@umap_expression.param(
    "database",
    "UMAP database name (e.g. rice_OW_umap, arabidopsis_NIE_umap)",
    _in="path",
    default="rice_OW_umap",
)
class UMAPExpression(Resource):
    def get(self, database, gene_id):
        """Retrieve per-cell UMAP coordinates and expression for a gene."""
        database = str(escape(database))
        gene_id = str(escape(gene_id))

        species = UMAP_DATABASE_SPECIES.get(database)
        if species is None:
            return BARUtils.error_exit(
                f"Unknown UMAP database '{database}'. "
                f"Available: {', '.join(sorted(UMAP_DATABASE_SPECIES.keys()))}"
            ), 400

        if BARUtils.is_injection_attempt(gene_id):
            return BARUtils.error_exit(f"Invalid {species} gene ID: '{gene_id}'"), 400
        if not GeneIdUtils.validate_gene_id(gene_id, species):
            return BARUtils.error_exit(f"Invalid {species} gene ID: '{gene_id}'"), 400
        gene_id = GeneIdUtils.normalize_gene_id(gene_id, species)

        engine = db.engines.get(database)
        if engine is None:
            return BARUtils.error_exit("Database not available"), 503

        expr_row, error = _fetch_expression_row(engine, gene_id)
        if error:
            return error

        expr_raw = expr_row.expression
        expr_map = json.loads(expr_raw) if isinstance(expr_raw, str) else expr_raw

        coords, error = _fetch_coords(engine)
        if error:
            return error

        data = _merge_coords_and_expression(coords, expr_map)

        return BARUtils.success_exit({
            "gene_id": gene_id,
            "database": database,
            "species": species,
            "record_count": len(data),
            "data": data,
        })


umap_expression.add_resource(UMAPExpression, "/<string:database>/<string:gene_id>")
