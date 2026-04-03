from datetime import datetime
from api import db
from sqlalchemy.dialects.mysql import DECIMAL


class Sites(db.Model):
    __bind_key__ = "fastpheno"
    __tablename__ = "sites"

    sites_pk: db.Mapped[int] = db.mapped_column(db.Integer, primary_key=True, nullable=False)
    site_name: db.Mapped[str] = db.mapped_column(db.String(45), nullable=False)
    lat: db.Mapped[float] = db.mapped_column(DECIMAL(15, 12), nullable=False)
    lng: db.Mapped[float] = db.mapped_column(DECIMAL(15, 12), nullable=False)
    site_desc: db.Mapped[str] = db.mapped_column(db.String(999), nullable=True)


class Flights(db.Model):
    __bind_key__ = "fastpheno"
    __tablename__ = "flights"

    flights_pk: db.Mapped[int] = db.mapped_column(db.Integer, primary_key=True, nullable=False)
    pilot: db.Mapped[str] = db.mapped_column(db.String(45), nullable=True)
    flight_date: db.Mapped[datetime] = db.mapped_column(db.DateTime, nullable=False)
    sites_pk: db.Mapped[int] = db.mapped_column(db.Integer, nullable=False)
    height: db.Mapped[float] = db.mapped_column(DECIMAL(15, 10), nullable=True)
    speed: db.Mapped[float] = db.mapped_column(DECIMAL(15, 10), nullable=True)


class Trees(db.Model):
    __bind_key__ = "fastpheno"
    __tablename__ = "trees"

    trees_pk: db.Mapped[int] = db.mapped_column(db.Integer, primary_key=True, nullable=False)
    sites_pk: db.Mapped[int] = db.mapped_column(db.Integer, nullable=False)
    longitude: db.Mapped[float] = db.mapped_column(DECIMAL(15, 12), nullable=False)
    latitude: db.Mapped[float] = db.mapped_column(DECIMAL(15, 12), nullable=False)
    tree_site_id: db.Mapped[str] = db.mapped_column(db.String(45), nullable=True)
    family_id: db.Mapped[str] = db.mapped_column(db.String(45), nullable=True)
    external_link: db.Mapped[str] = db.mapped_column(db.String(200), nullable=True)
    block_num: db.Mapped[int] = db.mapped_column(db.Integer, nullable=True)
    seq_id: db.Mapped[str] = db.mapped_column(db.String(25), nullable=True)
    x_pos: db.Mapped[int] = db.mapped_column(db.Integer, nullable=True)
    y_pos: db.Mapped[int] = db.mapped_column(db.Integer, nullable=True)
    height_2022: db.Mapped[str] = db.mapped_column(db.String(10), nullable=True)


class TreesFlightsJoinTbl(db.Model):
    __bind_key__ = "fastpheno"
    __tablename__ = "trees_flights_join_tbl"

    trees_pk: db.Mapped[int] = db.mapped_column(db.Integer, primary_key=True, nullable=False)
    flights_pk: db.Mapped[int] = db.mapped_column(db.Integer, primary_key=True, nullable=False)
    confidence: db.Mapped[float] = db.mapped_column(DECIMAL(8, 5), nullable=True)


class Bands(db.Model):
    __bind_key__ = "fastpheno"
    __tablename__ = "bands"
    __table_args__ = (db.Index("bands_flight_band_tree_idx", "flights_pk", "band", "trees_pk"),)

    trees_pk: db.Mapped[int] = db.mapped_column(db.Integer, primary_key=True, nullable=False)
    flights_pk: db.Mapped[int] = db.mapped_column(db.Integer, primary_key=True, nullable=False)
    band: db.Mapped[str] = db.mapped_column(db.String(20), primary_key=True, nullable=False)
    value: db.Mapped[float] = db.mapped_column(DECIMAL(8, 5), nullable=False)


class Pigments(db.Model):
    __bind_key__ = "fastpheno"
    __tablename__ = "pigments"

    trees_pk: db.Mapped[int] = db.mapped_column(db.Integer, primary_key=True, nullable=False)
    flights_pk: db.Mapped[int] = db.mapped_column(db.Integer, primary_key=True, nullable=False)
    pigment: db.Mapped[int] = db.mapped_column(db.Integer, primary_key=True, nullable=False)
    value: db.Mapped[float] = db.mapped_column(DECIMAL(20, 15), nullable=False)


class Unispec(db.Model):
    __bind_key__ = "fastpheno"
    __tablename__ = "unispec"

    trees_pk: db.Mapped[int] = db.mapped_column(db.Integer, primary_key=True, nullable=False)
    flights_pk: db.Mapped[int] = db.mapped_column(db.Integer, primary_key=True, nullable=False)
    pigment: db.Mapped[int] = db.mapped_column(db.Integer, primary_key=True, nullable=False)
    value: db.Mapped[float] = db.mapped_column(DECIMAL(20, 15), nullable=False)
