from flask import request
from flask_restx import Namespace, Resource, fields
from markupsafe import escape
from api import db
from api.utils.bar_utils import BARUtils
from api.models.gaia import Genes, Aliases, PublicationFigures, PubIds, Figures, AuthorList, FigureModels
from sqlalchemy import func, or_, cast, literal
from sqlalchemy.dialects import mysql
from marshmallow import Schema, ValidationError, fields as marshmallow_fields
import json
import re

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

        # Validate json
        try:
            json_data = PublicationSchema().load(json_data)
        except ValidationError as err:
            return BARUtils.error_exit(err.messages), 400

        pubmeds = json_data["pubmeds"]

        # Check if pubmed ids are valid
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
            .order_by(PubIds.pubmed.desc())
        )

        rows = db.session.execute(query).fetchall()

        record = {}

        if rows and len(rows) > 0:
            for row in rows:

                # Check if record has an id. If it doesn't, this is first row.
                if "id" in record:
                    # Check if this is a new pubmed id
                    if record["id"]["pubmed"] != row.pubmed:
                        # new record. Add old now to data and create a new record
                        data.append(record)
                        record = {}

                # Check if figures exists, if not add it.
                if record.get("figures") is None:
                    # Create a new figures record
                    record["figures"] = []

                # Now append figure to the record
                figure = {"img_name": row.img_name, "caption": row.caption, "img_url": row.img_url}
                record["figures"].append(figure)

                # Now add the id. If it exists don't add
                if record.get("id") is None:
                    record["id"] = {}
                    record["id"]["pubmed"] = row.pubmed
                    record["id"]["pmc"] = row.pmc

        # The last record
        data.append(record)

        # Return final data
        return BARUtils.success_exit(data)


@gaia.route("/publication_figures_by_gene/<string:identifier>")
class GaiaPublicationFiguresByGene(Resource):
    @gaia.param("identifier", _in="path", default="ABI3")
    def get(self, identifier=""):

        # Escape input
        identifier = escape(identifier)

        # Is it valid
        if not BARUtils.is_gaia_alias(identifier):
            return BARUtils.error_exit("Invalid identifier"), 400

        # Resolve to gene ids: try alias first, then locus / ncbi id
        rows = db.session.execute(db.select(Aliases.genes_id).filter(Aliases.alias == identifier)).fetchall()
        gene_ids = [r.genes_id for r in rows]

        if not gene_ids:
            rows = db.session.execute(
                db.select(Genes.id).filter(or_(Genes.locus == identifier, Genes.geneid == identifier))
            ).fetchall()
            gene_ids = [r.id for r in rows]

        if not gene_ids:
            return BARUtils.error_exit("Nothing found"), 404

        # Get the gene's full alias set
        aliases = [
            r.alias.lower()
            for r in db.session.execute(db.select(Aliases.alias).filter(Aliases.genes_id.in_(gene_ids))).fetchall()
        ]

        # Match OCR words: word-boundary regex for long aliases, exact match for short ones
        long_aliases = sorted({re.escape(a) for a in aliases if len(a) >= 4})
        short_aliases = sorted({a for a in aliases if len(a) < 4})

        # No usable aliases, nothing to match on
        if not long_aliases and not short_aliases:
            return BARUtils.success_exit({"figures": {}, "allImageWords": {}})

        word_expr = func.lower(func.json_unquote(func.json_extract(FigureModels.data, "$.word")))
        match_conds = []
        if long_aliases:
            alias_re = "(^|[^a-z0-9])(" + "|".join(long_aliases) + ")([^a-z0-9]|$)"
            match_conds.append(word_expr.regexp_match(alias_re))
        if short_aliases:
            match_conds.append(word_expr.in_(short_aliases))

        matched_rows = db.session.execute(db.select(FigureModels.data).where(or_(*match_conds))).fetchall()
        if not matched_rows:
            return BARUtils.success_exit({"figures": {}, "allImageWords": {}})

        # Collect each matched image and its boxes (keep the image even if a box is missing)
        bbox_by_name = {}
        for row in matched_rows:
            d = row.data if isinstance(row.data, dict) else json.loads(row.data)
            for img in d.get("image", []):
                name = (img.get("imageName") or "").lstrip("/")
                if not name:
                    continue
                bbox_list = bbox_by_name.setdefault(name, [])
                bbox = img.get("bbox")
                if bbox is not None:
                    bbox_list.append(bbox)

        stripped_names = list(bbox_by_name.keys())
        if not stripped_names:
            return BARUtils.success_exit({"figures": {}, "allImageWords": {}})

        # Drop image names used by more than one publication, we can't attribute those
        collision = (
            db.select(Figures.img_name)
            .group_by(Figures.img_name)
            .having(func.count(func.distinct(Figures.publication_figures_id)) > 1)
        )

        # Pull the figures and their publication info, skip null urls, newest pubmed first
        core_stmt = (
            db.select(
                PubIds.pmc,
                PubIds.pubmed,
                PublicationFigures.id.label("pf_id"),
                PublicationFigures.title,
                PublicationFigures.abstract,
                Figures.img_name,
                Figures.img_url,
                Figures.caption,
            )
            .select_from(Figures)
            .join(PublicationFigures, PublicationFigures.id == Figures.publication_figures_id)
            .join(PubIds, PubIds.publication_figures_id == PublicationFigures.id)
            .where(Figures.img_name.in_(stripped_names))
            .where(Figures.img_url.isnot(None))
            .where(Figures.img_name.not_in(collision))
            .order_by(cast(PubIds.pubmed, mysql.INTEGER(unsigned=True)).desc())
        )
        fig_rows = db.session.execute(core_stmt).fetchall()

        if not fig_rows:
            return BARUtils.success_exit({"figures": {}, "allImageWords": {}})

        # Group figures by PMC, one entry per image name
        figures_by_pmc, pmc_to_pf, pf_ids, seen_names = {}, {}, set(), set()
        for r in fig_rows:
            pf_ids.add(r.pf_id)
            pmc_to_pf[r.pmc] = r.pf_id
            if r.pmc not in figures_by_pmc:
                figures_by_pmc[r.pmc] = {
                    "title": r.title,
                    "abstract": r.abstract,
                    "authors": [],
                    "pubmed": r.pubmed,
                    "figures": [],
                }
            if r.img_name in seen_names:
                continue
            seen_names.add(r.img_name)
            figures_by_pmc[r.pmc]["figures"].append(
                {
                    "img_name": r.img_name,
                    "img_url": r.img_url,
                    "caption": r.caption,
                    "bbox": bbox_by_name.get(r.img_name, []),
                }
            )

        # Attach authors to each publication
        authors_by_pf = {}
        for r in db.session.execute(
            db.select(AuthorList.publication_figures_id, AuthorList.author).filter(
                AuthorList.publication_figures_id.in_(pf_ids)
            )
        ).fetchall():
            authors_by_pf.setdefault(r.publication_figures_id, []).append(r.author)
        for pmc, pf_id in pmc_to_pf.items():
            figures_by_pmc[pmc]["authors"] = authors_by_pf.get(pf_id, [])

        # allImageWords: gene words detected on the shown figures, for the gene-name filter
        displayed_names = list({r.img_name for r in fig_rows})
        all_image_words = {}
        if displayed_names:
            displayed_slashed = json.dumps(["/" + n for n in displayed_names])  # stored names keep a leading /
            words_rows = db.session.execute(
                db.select(FigureModels.data)
                .where(func.json_unquote(func.json_extract(FigureModels.data, "$.gene")) == "true")
                .where(
                    func.json_overlaps(
                        func.json_extract(FigureModels.data, "$.image[*].imageName"),
                        cast(literal(displayed_slashed), mysql.JSON),
                    )
                )
            ).fetchall()
            displayed_set = set(displayed_names)
            for row in words_rows:
                d = row.data if isinstance(row.data, dict) else json.loads(row.data)
                word = (d.get("word") or "").lower()
                for img in d.get("image", []):
                    name = (img.get("imageName") or "").lstrip("/")
                    if name in displayed_set:
                        bbox = img.get("bbox")
                        all_image_words.setdefault(word, {})[name] = bbox if bbox is not None else []

        # Return final data
        return BARUtils.success_exit({"figures": figures_by_pmc, "allImageWords": all_image_words})
