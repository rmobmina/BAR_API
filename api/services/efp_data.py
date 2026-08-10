"""Centralised query service for all eFP databases -- resolves the DB engine, converts AGI to probeset when needed, and runs a parameterized query."""

from __future__ import annotations

import re
import traceback
from typing import Any, Dict, List, Optional

from flask import has_app_context
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from api import db
from api.models.annotations_lookup import AtAgiLookup
from api.models.efp_schemas import SIMPLE_EFP_DATABASE_SCHEMAS
from api.utils.bar_utils import BARUtils
from api.utils.gene_id_utils import GeneIdUtils

DEFAULT_SAMPLE_SCHEMA = {
    "table": "sample_data",
    "gene_column": "data_probeset_id",
    "sample_column": "data_bot_id",
    "value_column": "data_signal",
}

# Manual list covers datasets still backed by shipped dumps
_MANUAL_DEFAULT_DATABASES = [
    "canola_nssnp",
    "eplant2",
    "eplant_poplar",
    "eplant_rice",
    "eplant_soybean",
    "eplant_tomato",
    "fastpheno",
    "homologs_db",
    "interactions_vincent_v2",
    "llama3",
    "poplar_nssnp",
    "rice_interactions",
    "soybean_nssnp",
    "tomato_nssnp",
    "tomato_sequence",
]

MANUAL_DATABASE_SCHEMAS = {
    name: {
        **DEFAULT_SAMPLE_SCHEMA,
        "identifier_type": "agi",
        "metadata": {},
    }
    for name in _MANUAL_DEFAULT_DATABASES
}


def _build_schema_catalog() -> Dict[str, Dict[str, Any]]:
    """Stitch together the python schemas + legacy dumps into one lookup table."""
    catalog: Dict[str, Dict[str, Any]] = {}
    for db_name, spec in SIMPLE_EFP_DATABASE_SCHEMAS.items():
        schema = dict(DEFAULT_SAMPLE_SCHEMA)
        schema.update(
            {
                "identifier_type": spec.get("identifier_type", "agi"),
                "metadata": spec.get("metadata") or {},
            }
        )
        catalog[db_name] = schema

    for db_name, schema in MANUAL_DATABASE_SCHEMAS.items():
        catalog[db_name] = dict(schema)

    return catalog


def agi_to_probset(gene_id: str) -> Optional[str]:
    """Look up the most recent probeset mapping for an Arabidopsis AGI ID."""
    try:
        subquery = (
            db.select(AtAgiLookup.probeset)
            .where(AtAgiLookup.agi == gene_id.upper())
            .order_by(AtAgiLookup.date.desc())
            .limit(1)
            .subquery()
        )

        sq_query = db.session.query(subquery)
        if sq_query.count() > 0:
            return sq_query[0][0]
        return None
    except Exception as exc:
        print(f"[error] agi to probeset conversion failed {exc}")
        return None


def _get_engine(database: str) -> Optional[Engine]:
    """Return the Flask-SQLAlchemy MySQL bind engine for the given database, if any."""
    if not has_app_context():
        return None
    try:
        return db.engines.get(database)
    except Exception as exc:
        print(f"[warn] unable to load sqlalchemy bind for {database}: {exc}")
        return None


def query_efp_database_dynamic(
    database: str,
    gene_id: str,
    sample_ids: Optional[List[str]] = None,
    allow_empty_results: bool = False,
    sample_case_insensitive: bool = False,
) -> Dict[str, object]:
    """Query an eFP database by gene ID, converting AGI to probeset when the schema requires it."""
    try:
        database = str(database)
        gene_id = str(gene_id)

        schema = DYNAMIC_DATABASE_SCHEMAS.get(database)
        if not schema:
            return {
                "success": False,
                "error": (
                    f"Database '{database}' is not supported. "
                    f"Select one of: {', '.join(sorted(DYNAMIC_DATABASE_SCHEMAS.keys()))}"
                ),
                "error_code": 400,
            }

        species = schema.get("metadata", {}).get("species", "").lower()

        query_id = gene_id
        probset_display = None
        gene_case_insensitive = False
        upper_id = gene_id.upper()
        is_agi_id = upper_id.startswith("AT") and "G" in upper_id

        if is_agi_id:
            if not BARUtils.is_efp_gene_valid(upper_id, "efp_arabidopsis"):
                return {"success": False, "error": "Invalid Arabidopsis gene ID format", "error_code": 400}
        elif species and schema["identifier_type"] == "agi":
            if not GeneIdUtils.validate_gene_for_database(upper_id, database):
                return {"success": False, "error": f"Invalid {species.capitalize()} gene ID", "error_code": 400}

        # Arabidopsis probeset databases need the AGI converted first; everyone else queries as-is
        if is_agi_id:
            if schema["identifier_type"] == "probeset":
                probset = agi_to_probset(upper_id)
                if not probset:
                    return {
                        "success": False,
                        "error": f"Could not find probeset for gene {gene_id}",
                        "error_code": 404,
                    }
                query_id = probset
                probset_display = probset
                print(f"[info] Converted {gene_id} to probeset {query_id} for {database}")
            else:
                query_id = upper_id
                gene_case_insensitive = True
                probset_display = upper_id
        else:
            query_id = upper_id if species else gene_id
            gene_case_insensitive = bool(species)

        gene_col = schema["gene_column"]
        sample_col = schema["sample_column"]
        value_col = schema["value_column"]
        table_name = schema["table"]

        # Column/table names come from the internal schema catalog, but validate anyway before interpolating into SQL
        for identifier, name in [
            (gene_col, "gene_column"),
            (sample_col, "sample_column"),
            (value_col, "value_column"),
            (table_name, "table"),
        ]:
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", identifier):
                return {
                    "success": False,
                    "error": f"Invalid schema identifier for {name}: {identifier}",
                    "error_code": 500,
                }

        gene_column_expr = f"UPPER({gene_col})" if gene_case_insensitive else gene_col
        params = {"gene_id": query_id.upper() if gene_case_insensitive else query_id}
        where_clauses = [f"{gene_column_expr} = :gene_id"]

        if sample_ids:
            filtered = [s for s in sample_ids if s]
            if filtered:
                sample_column_expr = f"UPPER({sample_col})" if sample_case_insensitive else sample_col
                sample_conditions = []
                for idx, sample in enumerate(filtered):
                    key = f"sample_{idx}"
                    params[key] = sample.upper() if sample_case_insensitive else sample
                    sample_conditions.append(f"{sample_column_expr} = :{key}")
                where_clauses.append(f"({' OR '.join(sample_conditions)})")

        query_sql = text(
            f"SELECT {sample_col} AS sample, {value_col} AS value "
            f"FROM {table_name} "
            f"WHERE {' AND '.join(where_clauses)}"
        )

        engine = _get_engine(database)
        results = None
        last_error = None

        if engine:
            try:
                with Session(engine) as session:
                    results = session.execute(query_sql, params).all()
            except SQLAlchemyError as exc:
                last_error = f"query failed: {exc}"
                print(f"[warn] {last_error}")
            except Exception as exc:
                last_error = f"unexpected failure: {exc}"
                print(f"[warn] {last_error}")
        else:
            last_error = f"Database {database} is not available (no active bind configured)."

        if results is None:
            _UNAVAILABLE_PHRASES = (
                "Unknown database",
                "Can't connect",
                "Connection refused",
                "not available",
            )
            is_missing_db = last_error and any(
                phrase in last_error for phrase in _UNAVAILABLE_PHRASES
            )
            if is_missing_db:
                print(f"[warn] {database}: {last_error}")
                return {
                    "success": False,
                    "error": f"Database '{database}' is not available.",
                    "error_code": 503,
                }
            return {
                "success": False,
                "error": (
                    f"Database query failed for {database}. "
                    f"{'Last error: ' + last_error if last_error else ''}"
                ).strip(),
                "error_code": 500,
            }

        if not results and not allow_empty_results:
            error_dict = BARUtils.error_exit(
                f"No expression data found for {gene_id} (query identifier: {query_id})"
            )
            return {
                "success": False,
                "error": error_dict["error"],
                "error_code": 404,
            }

        expression_data = [{"name": row.sample, "value": str(row.value)} for row in results]

        return {
            "success": True,
            "gene_id": gene_id,
            "probset_id": probset_display or query_id,
            "database": database,
            "record_count": len(expression_data),
            "data": expression_data,
        }

    except Exception as exc:
        error_trace = traceback.format_exc()
        print(f"[error] Database query exception: {error_trace}")
        return {
            "success": False,
            "error": f"Database query failed: {str(exc)}",
            "error_code": 500,
        }


DYNAMIC_DATABASE_SCHEMAS = _build_schema_catalog()
