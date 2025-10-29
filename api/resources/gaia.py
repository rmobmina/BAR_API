from flask_restx import Namespace, Resource
from markupsafe import escape
from api import db
from api.utils.bar_utils import BARUtils
from api.models.gaia import Aliases
from sqlalchemy import func
import json

gaia = Namespace("Gaia", description="Gaia", path="/gaia")


@gaia.route("/aliases/<string:identifier>")
class GaiaAliases(Resource):
    @gaia.param("identifier", _in="path", default="ABI3")
    def get(self, identifier=""):

        # Escape input
        identifier = escape(identifier)

        # Is it valid
        if BARUtils.is_alphanumeric(identifier):
            # Convert to json
            identifier_json = json.dumps([identifier])

            # Get data
            # Note: SQLAlchmemy or_ did not work here. Query had AND for some reason.
            query = db.select(Aliases).filter(
                (func.json_contains(func.lower(Aliases.data), func.lower(identifier_json), "$.aliases"))
                | (func.json_extract(func.lower(Aliases.data), "$.geneid") == func.lower(identifier))
                | (func.json_extract(func.lower(Aliases.data), "$.locus") == func.lower(identifier)),
            )
            row = db.session.execute(query).scalars().first()

            if row:
                return BARUtils.success_exit(row.data)
            else:
                return BARUtils.error_exit("Nothing found"), 404

        else:
            return BARUtils.error_exit("Invalid identifier"), 400
