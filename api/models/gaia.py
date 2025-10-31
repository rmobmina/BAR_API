from typing import List
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from api import db


class Genes(db.Model):
    __bind_key__ = "gaia"
    __tablename__ = "genes"

    id: db.Mapped[int] = db.mapped_column(db.Integer, nullable=False, primary_key=True)
    species: db.Mapped[str] = db.mapped_column(db.String(64), nullable=False)
    locus: db.Mapped[str] = db.mapped_column(db.String(64), nullable=True)
    geneid: db.Mapped[str] = db.mapped_column(db.String(32), nullable=True)
    children: db.Mapped[List["Aliases"]] = relationship()


class Aliases(db.Model):
    __bind_key__ = "gaia"
    __tablename__ = "aliases"

    id: db.Mapped[int] = db.mapped_column(db.Integer, nullable=False, primary_key=True)
    genes_id: db.Mapped[int] = db.mapped_column(ForeignKey("genes.id", ondelete="CASCADE"), nullable=False)
    alias: db.Mapped[str] = db.mapped_column(db.String(256), nullable=False)
