from flask import request
from flask_restx import Namespace, Resource, fields
from markupsafe import escape
from api import db
from api.utils.bar_utils import BARUtils
from api.models.gaia import Genes, Aliases, PubIds, Figures
from sqlalchemy import func, or_
from marshmallow import Schema, ValidationError, fields as marshmallow_fields
import json

gaia = Namespace("Gaia", description="Gaia", path="/gaia")

parser = gaia.parser()
parser.add_argument(
    "terms",
    type=list,
    action="append",
    required=True,
    help="Publication IDs",
    default=["32492426", "32550561"],
)

publication_request_fields = gaia.model(
    "Publications",
    {
        "pubmeds": fields.List(
            required=True,
            example=["32492426", "32550561"],
            cls_or_instance=fields.String,
        ),
    },
)


# Validation is done in a different way to keep things simple
class PublicationSchema(Schema):
    pubmeds = marshmallow_fields.List(cls_or_instance=marshmallow_fields.String)


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


@gaia.route("/publication_figures")
class GaiaPublicationFigures(Resource):
    @gaia.expect(publication_request_fields)
    def post(self):
        json_data = request.get_json()
        data = {}

        # Validate json
        try:
            json_data = PublicationSchema().load(json_data)
        except ValidationError as err:
            return BARUtils.error_exit(err.messages), 400

        pubmeds = json_data["pubmeds"]

        # Check if pubmed ids are valide
        for pubmed in pubmeds:
            if not BARUtils.is_integer(pubmed):
                return BARUtils.error_exit("Invalid Pubmed ID"), 400

        # It is valid. Continue
        data = []

        # Left join is important in case aliases do not exist for the given locus / geneid
        query = (
            db.select(Figures.img_name, Figures.caption, Figures.img_url, PubIds.pubmed, PubIds.pmc)
            .select_from(Figures)
            .join(PubIds, PubIds.publication_figures_id == Figures.publication_figures_id)
            .filter(PubIds.pubmed.in_(pubmeds))
        )

        rows = db.session.execute(query).fetchall()

        # Just output the rows for now, we will format later
        if rows and len(rows) > 0:
            for row in rows:
                record = {
                    "img_name": row.img_name,
                    "caption": row.caption,
                    "img_url": row.img_url,
                    "pubmed": row.pubmed,
                    "pmc": row.pmc,
                }

                # Add the record to data
                data.append(record)

        # Return final data
        return BARUtils.success_exit(data)
