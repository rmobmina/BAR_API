"""
Centralised query service for all eFP databases.

Exposes a single entry point query_efp_database_dynamic() that handles:
  - Engine resolution via Flask-SQLAlchemy MySQL binds
  - AGI-to-probeset lookup for Arabidopsis microarray databases
  - Parameterised queries to prevent SQL injection
"""

from __future__ import annotations

import re
import traceback
from typing import Any, Dict, Iterable, List, Optional, Tuple

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


class EFPDataService:
    """Service class for querying eFP (electronic Fluorescent Pictograph) databases."""

    @staticmethod
    def _build_schema_catalog() -> Dict[str, Dict[str, Any]]:
        """Stitch together the python schemas + legacy dumps into one lookup table.

        :return: Catalog of database schemas
        :rtype: Dict[str, Dict[str, Any]]
        """
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

    @staticmethod
    def agi_to_probset(gene_id: str) -> Optional[str]:
        """
        Convert an Arabidopsis AGI identifier to its corresponding probeset ID.

        Looks up the most recent mapping in the AtAgiLookup table, ordered by date
        descending. This ensures the newest array design mapping is used when multiple
        mappings exist for the same AGI.

        :param gene_id: Arabidopsis gene ID in AGI format (e.g., 'AT1G01010')
        :type gene_id: str
        :return: Probeset ID (e.g., '261585_at') if found, None otherwise
        :rtype: Optional[str]

        Example::

            probeset = EFPDataService.agi_to_probset('AT1G01010')
            # Returns: '261585_at' (if mapping exists)
        """
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

    @staticmethod
    def _iter_engine_candidates(database: str) -> Iterable[Tuple[str, Engine]]:
        """
        Yield the Flask-SQLAlchemy MySQL bind engine for the given database, if any.

        :param database: Database name (e.g., 'cannabis', 'dna_damage')
        :type database: str
        :yields: Tuples of (engine_type, engine) where engine_type is 'sqlalchemy_bind'
        :rtype: Iterator[Tuple[str, sqlalchemy.engine.Engine]]

        Example::

            for engine_type, engine in EFPDataService._iter_engine_candidates('cannabis'):
                try:
                    result = engine.execute('SELECT * FROM sample_data LIMIT 1')
                    break  # Found working engine
                except Exception:
                    continue  # Try next engine
        """
        if not has_app_context():
            return

        try:
            bound_engine = db.engines.get(database)
            if bound_engine:
                yield ("sqlalchemy_bind", bound_engine)
        except Exception as exc:
            print(f"[warn] unable to load sqlalchemy bind for {database}: {exc}")

    @staticmethod
    def query_efp_database_dynamic(
        database: str,
        gene_id: str,
        sample_ids: Optional[List[str]] = None,
        allow_empty_results: bool = False,
        sample_case_insensitive: bool = False,
    ) -> Dict[str, object]:
        """
        Dynamically query any eFP database using the shared schema catalog.

        This function provides a unified interface for querying expression data across
        different eFP databases, handling species-specific gene ID validation and
        automatic probeset conversion when needed.

        :param database: Database name (e.g., 'cannabis', 'embryo', 'klepikova')
        :type database: str
        :param gene_id: Gene identifier (AGI format, probeset, or species-specific format)
        :type gene_id: str
        :param sample_ids: Optional list of sample IDs to filter results; if None, returns all samples
        :type sample_ids: Optional[List[str]]
        :param allow_empty_results: If True, return success even when no data found; if False, return 404 error
        :type allow_empty_results: bool
        :param sample_case_insensitive: If True, compare sample IDs case-insensitively
        :type sample_case_insensitive: bool
        :return: Dictionary with 'success' boolean, data or error message, and HTTP status code
        :rtype: Dict[str, object]

        Example::

            result = EFPDataService.query_efp_database_dynamic('embryo', 'AT1G01010')
            # Returns: {'success': True, 'gene_id': 'AT1G01010', 'data': [...]}

            result = EFPDataService.query_efp_database_dynamic('klepikova', 'AT1G01010')
            # Auto-converts to probeset, returns: {'probset_id': '261585_at', ...}
        """
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
                if not BARUtils.is_arabidopsis_gene_valid(upper_id):
                    return {"success": False, "error": "Invalid Arabidopsis gene ID format", "error_code": 400}
            elif species and schema["identifier_type"] == "agi":
                if not GeneIdUtils.validate_gene_id(upper_id, species):
                    return {"success": False, "error": f"Invalid {species.capitalize()} gene ID", "error_code": 400}

            # Handle Arabidopsis-specific logic for AGI IDs
            if is_agi_id:
                if schema["identifier_type"] == "probeset":
                    probset = EFPDataService.agi_to_probset(upper_id)
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
                # Non-AGI IDs: use as-is, typically already uppercase from validation
                query_id = upper_id if species else gene_id
                gene_case_insensitive = bool(species)

            # Build SQL query using parameterized queries to prevent SQL injection
            # Column and table names come from the internal schema catalog, which is safe
            gene_col = schema["gene_column"]
            sample_col = schema["sample_column"]
            value_col = schema["value_column"]
            table_name = schema["table"]

            # Validate identifiers contain only safe characters (alphanumeric and underscore)
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

            engine_candidates = list(EFPDataService._iter_engine_candidates(database))
            results = None
            last_error = None

            if engine_candidates:
                for source_label, engine in engine_candidates:
                    try:
                        with Session(engine) as session:
                            results = session.execute(query_sql, params).all()
                        if results:
                            break
                    except SQLAlchemyError as exc:
                        last_error = f"{source_label} failed: {exc}"
                        print(f"[warn] {last_error}")
                    except Exception as exc:
                        last_error = f"{source_label} unexpected failure: {exc}"
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


# Build the schema catalog at module load time
DYNAMIC_DATABASE_SCHEMAS = EFPDataService._build_schema_catalog()


# Maintain backward compatibility with existing code that imports these functions directly
def agi_to_probset(gene_id: str) -> Optional[str]:
    """Backward compatibility wrapper for EFPDataService.agi_to_probset()"""
    return EFPDataService.agi_to_probset(gene_id)


def query_efp_database_dynamic(
    database: str,
    gene_id: str,
    sample_ids: Optional[List[str]] = None,
    allow_empty_results: bool = False,
    sample_case_insensitive: bool = False,
) -> Dict[str, object]:
    """Backward compatibility wrapper for EFPDataService.query_efp_database_dynamic()"""
    return EFPDataService.query_efp_database_dynamic(
        database, gene_id, sample_ids, allow_empty_results, sample_case_insensitive
    )
