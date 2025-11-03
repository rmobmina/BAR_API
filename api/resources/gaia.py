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
            query_ids = []
            data = []

            # Check if alias exists
            # Note: This check can be done in on query, but optimizer is not using indexes for some reason
            query = db.select(Aliases.genes_id, Aliases.alias).filter(Aliases.alias == identifier)
            rows = db.session.execute(query).fetchall()

            if rows and len(rows) > 0:
                # Alias exists. Get the genes_ids
                for row in rows:
                    query_ids.append(row.genes_id)

            else:
                # Alias doesn't exist. Get the ids if it's locus or ncbi id
                query = db.select(Genes.id).filter(or_(Genes.locus == identifier, Genes.geneid == identifier))
                rows = db.session.execute(query).fetchall()

                if rows and len(rows) > 0:
                    for row in rows:
                        query_ids.append(row.id)
                else:
                    return BARUtils.error_exit("Nothing found"), 404

            # Left join is important in case aliases do not exist for the given locus / geneid
            query = (
                db.select(Genes.species, Genes.locus, Genes.geneid, func.json_arrayagg(Aliases.alias).label("aliases"))
                .select_from(Genes)
                .outerjoin(Aliases, Aliases.genes_id == Genes.id)
                .filter(Genes.id.in_(query_ids))
                .group_by(Genes.species, Genes.locus, Genes.geneid)
            )

            rows = db.session.execute(query).fetchall()

            if rows and len(rows) > 0:
                for row in rows:

                    # JSONify aliases
                    if row.aliases:
                        aliases = json.loads(row.aliases)
                    else:
                        aliases = []

                    record = {
                        "species": row.species,
                        "locus": row.locus,
                        "geneid": row.geneid,
                        "aliases": aliases,
                    }

                    # Add the record to data
                    data.append(record)

            # Return final data
            return BARUtils.success_exit(data)

        else:
            return BARUtils.error_exit("Invalid identifier"), 400
