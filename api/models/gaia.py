from api import db
from sqlalchemy.dialects.mysql import json


class Aliases(db.Model):
    __bind_key__ = "gaia"
    __tablename__ = "aliases"

    id: db.Mapped[int] = db.mapped_column(db.Integer, nullable=False, primary_key=True)
    data: db.Mapped[json] = db.mapped_column(db.JSON, nullable=True, primary_key=False)
