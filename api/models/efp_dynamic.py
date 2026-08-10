"""Generates one SQLAlchemy model class per database in SIMPLE_EFP_DATABASE_SCHEMAS at import time, instead of hand-writing each one."""

from __future__ import annotations

from typing import Dict

from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.dialects.mysql import INTEGER

from api import db
from api.models.efp_schemas import SIMPLE_EFP_DATABASE_SCHEMAS


def _to_sqla_type(column_spec):
    """Map a schema column spec ('type', 'length', 'unsigned') to a SQLAlchemy column type."""
    col_type = column_spec.get("type")
    if col_type == "string":
        return String(column_spec["length"])
    if col_type == "integer":
        if column_spec.get("unsigned"):
            return INTEGER(unsigned=True)
        return Integer
    if col_type == "float":
        return Float
    if col_type == "text":
        return Text
    raise ValueError(f"Unsupported column type: {col_type}")


def _generate_model(bind_key: str, spec) -> db.Model:
    """Build a concrete SQLAlchemy model class for the given database's schema spec."""
    attrs = {"__bind_key__": bind_key, "__tablename__": spec["table_name"]}

    for column in spec["columns"]:
        kwargs = {"nullable": column.get("nullable", True)}
        if column.get("primary_key"):
            kwargs["primary_key"] = True
        attrs[column["name"]] = db.mapped_column(_to_sqla_type(column), **kwargs)

    class_name = "".join([part.capitalize() for part in bind_key.split("_")]) + "SampleData"
    return type(class_name, (db.Model,), attrs)


SIMPLE_EFP_SAMPLE_MODELS: Dict[str, db.Model] = {
    db_name: _generate_model(db_name, spec) for db_name, spec in SIMPLE_EFP_DATABASE_SCHEMAS.items()
}

__all__ = ["SIMPLE_EFP_SAMPLE_MODELS"]
