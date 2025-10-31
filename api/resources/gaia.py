from flask_restx import Namespace, Resource
from markupsafe import escape
from api import db
from api.utils.bar_utils import BARUtils
from api.models.gaia import Genes, Aliases
from sqlalchemy import func, or_
import json

gaia = Namespace("Gaia", description="Gaia", path="/gaia")


@gaia.route("/aliases/<string:identifier>")
class GaiaAliases(Resource):
    @gaia.param("identifier", _in="path", default="ABI3")
    def get(self, identifier=""):

        # Escape input
        identifier = escape(identifier)

        # Is it valid
        if BARUtils.is_gaia_alias(identifier):

            # Check if alias exists
            # Note: This check can be done in on query, but optimizer is not using indexes for some reason
            # Also, GAIA only uses the first result
            query = db.select(Aliases.genes_id, Aliases.alias).filter(Aliases.alias == identifier)
            row = db.session.execute(query).fetchone()

            if row:
                # Alias exists. Get the genes_id
                query_id = row.genes_id

            else:
                # Alias doesn't exist. Get the genes_id if it's locus or ncbi id
                query = db.select(Genes.id).filter(or_(Genes.locus == identifier, Genes.geneid == identifier))
                row = db.session.execute(query).fetchone()

                if row:
                    query_id = row.id
                else:
                    return BARUtils.error_exit("Nothing found"), 404

            # Left join is important in case aliases do not exist for the given locus / geneid
            query = (
                db.select(Genes.species, Genes.locus, Genes.geneid, func.json_arrayagg(Aliases.alias).label("aliases"))
                .select_from(Genes)
                .outerjoin(Aliases, Aliases.genes_id == Genes.id)
                .filter(Genes.id == query_id)
            )

            result = db.session.execute(query).fetchone()

            # See if aliases exists
            if result.aliases:
                aliases = json.loads(result.aliases)
            else:
                aliases = []

            data = {
                "species": result.species,
                "locus": result.locus,
                "geneid": result.geneid,
                "aliases": aliases,
            }
            return BARUtils.success_exit(data)

        else:
            return BARUtils.error_exit("Invalid identifier"), 400
