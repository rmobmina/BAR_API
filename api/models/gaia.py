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


class PublicationFigures(db.Model):
    __bind_key__ = "gaia"
    __tablename__ = "publication_figures"

    id: db.Mapped[int] = db.mapped_column(db.Integer, nullable=False, primary_key=True)
    title: db.Mapped[str] = db.mapped_column(db.String(512), nullable=True)
    abstract: db.Mapped[str] = db.mapped_column(db.Text, nullable=True)
    children: db.Mapped[List["PubIds"]] = relationship()
    children: db.Mapped[List["Figures"]] = relationship()


class PubIds(db.Model):
    __bind_key__ = "gaia"
    __tablename__ = "pub_ids"

    id: db.Mapped[int] = db.mapped_column(db.Integer, nullable=False, primary_key=True)
    publication_figures_id: db.Mapped[int] = db.mapped_column(db.Integer, nullable=False)
    publication_figures_id: db.Mapped[int] = db.mapped_column(
        ForeignKey("publication_figures.id", ondelete="CASCADE"), nullable=False
    )
    pubmed: db.Mapped[str] = db.mapped_column(db.String(16), nullable=True)
    pmc: db.Mapped[str] = db.mapped_column(db.String(16), nullable=True)


class Figures(db.Model):
    __bind_key__ = "gaia"
    __tablename__ = "figures"

    id: db.Mapped[int] = db.mapped_column(db.Integer, nullable=False, primary_key=True)
    publication_figures_id: db.Mapped[int] = db.mapped_column(db.Integer, nullable=False)
    publication_figures_id: db.Mapped[int] = db.mapped_column(
        ForeignKey("publication_figures.id", ondelete="CASCADE"), nullable=False
    )
    img_name: db.Mapped[str] = db.mapped_column(db.String(64), nullable=False)
    caption: db.Mapped[str] = db.mapped_column(db.Text, nullable=True)
    img_url: db.Mapped[str] = db.mapped_column(db.String(256), nullable=True)
