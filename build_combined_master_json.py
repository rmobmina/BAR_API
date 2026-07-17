#!/usr/bin/env python3
"""
Reena Obmina | BCB330 Project 2025-2026 | University of Toronto
"""

import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

from scrape_species_view_info import extract_db, parse_groups
from scrape_view_databases import EPLANT_SPECIES_FILE

HUMAN_XML_DIR = Path("data/efp_info/efp_human")
VIEW_INFO_FILE = Path("data/efp_info/efp_eplant_species_view_info.json")
REGEX_REGISTRY_FILE = Path("data/regex_master_list_efp_eplant/bar_regex_registry.json")

# eplant_barley and eplant_barley_legacy are two live instances of the same species,
# named to match their BAR URLs exactly (bar.utoronto.ca/eplant_barley_legacy/ etc.).
# Noted here because the version numbers aren't visible anywhere in the instance
# names themselves.
INSTANCE_NOTES = {
    "eplant_barley_legacy": "ePlant Barley v1 (legacy). URL: https://bar.utoronto.ca/eplant_barley_legacy/",
    "eplant_barley": "ePlant Barley v3 (current). URL: https://bar.utoronto.ca/eplant_barley/",
}


def load_json(path):
    with open(path) as f:
        return json.load(f)


def get_validation_patterns():
    """Load Vincent's per-eFP-project regex registry (tested at 99%+ coverage
    against real probeset/gene ID sample data, one pattern per project instead
    of one per database).

    :returns: (patterns, db_regex_project) -- patterns maps eFP project name to
        its regex string; db_regex_project maps database name to the project
        name whose pattern validates it (None if Vincent's registry couldn't
        resolve one, in which case callers fall back to species validation).
    """
    registry = load_json(REGEX_REGISTRY_FILE)
    patterns = {name: info["regex"] for name, info in registry["projects"].items()}
    db_regex_project = {
        db: info.get("regex_project") for db, info in registry["databases"].items()
    }
    return patterns, db_regex_project


# Vincent's registry falls back to a database's species' primary eFP project
# when it can't resolve one from live frontend data (resolved_via
# "species-fallback"). That fallback is wrong for these two: both are hidden/
# legacy databases (not in any current frontend dropdown) whose real values
# are the freeform text a *different*, more specific project already in the
# registry expects -- not gene IDs at all. Obvious from the database's own
# name; confirmed against real sample data in verify_regex_projects().
REGEX_PROJECT_OVERRIDES = {
    "maize_lipid_map": "efp_maize_lipid_map",
    "tomato_trait": "efp_tomato_trait",
}


def load_probeset_samples():
    """Load real gene_id/probeset values per database (api/random_rows_json/),
    for empirically verifying regex_project assignments in verify_regex_projects().
    """
    samples = {}
    for path in sorted(SAMPLE_DUMP_DIR.glob("*_test_data.json")):
        db_name = path.stem.removesuffix("_test_data")
        rows = load_json(path)
        if isinstance(rows, list):
            ids = [
                row.get("data_probeset_id")
                for row in rows
                if isinstance(row, dict) and row.get("data_probeset_id") is not None
            ]
            if ids:
                samples[db_name] = ids
    return samples


def verify_regex_projects(db_regex_project, patterns, sample_ids, threshold=0.9):
    """Empirically check each database's regex_project assignment against its
    own real sample IDs, the same way schema_variants are verified against
    real columns (apply_dump_evidence). Vincent's "species-fallback"
    resolutions are unverified guesses for databases with no live frontend
    view to confirm against, and are sometimes wrong (e.g. a legacy ID scheme
    the species' main project regex doesn't cover). Demote any assignment
    that doesn't validate most of its own database's real IDs, so callers
    fall back to the (already-correct) species validator instead of silently
    rejecting valid input.

    :returns: (verified_db_regex_project, demoted) -- demoted is
        {db: (project, pass_rate)} for visibility/logging.
    """
    verified = dict(db_regex_project)
    for db, override in REGEX_PROJECT_OVERRIDES.items():
        if db in verified:
            verified[db] = override

    demoted = {}
    for db, ids in sample_ids.items():
        project = verified.get(db)
        if not project:
            continue
        pattern = patterns.get(project)
        if not pattern:
            continue
        compiled = re.compile(pattern)
        pass_rate = sum(1 for gid in ids if compiled.search(str(gid))) / len(ids)
        if pass_rate < threshold:
            demoted[db] = (project, pass_rate)
            verified[db] = None

    return verified, demoted


def patch_human_view_groups(view_info):
    """Fill in efp_human's empty sample groups from the local eFP Human XML config.

    efp_human's live views scrape as empty ("groups": {}) because the site 403s the
    scraper (see scrape_view_databases.py's _EFP_FALLBACK comment) -- not because
    the views have no group data. We have that data locally (data/efp_info/efp_human/,
    the actual per-view XML config pulled from eFP Human), so parse it with the same
    extract_db()/parse_groups() scrape_species_view_info.py already uses for every
    other species, and patch the matching efp_human view entries in place.

    Returns True if any view was patched (caller should persist view_info to disk).
    """
    if not HUMAN_XML_DIR.is_dir():
        return False

    human_views = view_info.get("efp", {}).get("efp_human", [])
    if not human_views:
        return False

    views_by_name = {v["view_name"]: v for v in human_views}
    patched = False

    for xml_path in sorted(HUMAN_XML_DIR.glob("*.xml")):
        if xml_path.stem == "efp_info":
            continue

        view_name = xml_path.stem.replace("_", " ")
        view = views_by_name.get(view_name)
        if view is None:
            print(f"  Warning: no matching efp_human view for {xml_path.name}")
            continue

        root = ET.parse(xml_path).getroot()
        db = extract_db(root)
        groups = parse_groups(root)

        if db and db != view["database"]:
            print(f"  Warning: {view_name} db mismatch: scraped={view['database']!r} xml={db!r}")

        view["groups"] = groups
        view["view_file"] = xml_path.stem
        patched = True
        print(f"  Patched '{view_name}' ({db}): {len(groups)} sample groups")

    return patched


SAMPLE_DUMP_DIR = Path("api/random_rows_json")

# Role/type annotations for every sample_data column we've observed in the real
# sample dumps, keyed by column name so both schema variants (and any new column
# a future dump reveals) share one definition instead of two hand-copies.
COLUMN_META = {
    "data_probeset_id": {"type": "varchar", "role": "gene_id"},
    "data_signal": {"type": "float", "role": "value"},
    "data_bot_id": {"type": "varchar", "role": "sample"},
    "sample_id": {"type": "int", "role": "row_id"},
    "proj_id": {"type": "varchar", "role": "project"},
    "sample_file_name": {"type": "varchar", "role": "provenance"},
    "data_call": {"type": "varchar", "role": "present_call"},
    "data_p_val": {"type": "double", "role": "p_value"},
    # Columns below only appear in a handful of legacy/oddball databases --
    # added so every real schema shape found in verify_regex_projects()'s
    # sibling, derive_schema_variants_from_dumps(), has full column metadata
    # instead of a null type/role.
    "data_num": {"type": "int", "role": "secondary_id"},
    "channel": {"type": "varchar", "role": "channel"},
    "project_id": {"type": "varchar", "role": "project"},
    "sample_tissue": {"type": "varchar", "role": "tissue"},
    "data_p_value": {"type": "double", "role": "p_value"},
    "genome": {"type": "varchar", "role": "genome"},
    "genome_id": {"type": "varchar", "role": "genome"},
    "orthogroup": {"type": "varchar", "role": "orthogroup"},
    "version": {"type": "varchar", "role": "version"},
    "log": {"type": "double", "role": "value"},
    "p_val": {"type": "double", "role": "p_value"},
    "qvalue": {"type": "double", "role": "q_value"},
}


def load_sample_dumps():
    """Load Vincent's per-database sample_data row dumps (api/random_rows_json/*_test_data.json).

    Returns {database_name: set(columns)}, with the "db" key dropped since every
    dump file carries it as a database-name tag added by whoever generated the
    dump, not a real sample_data column.
    """
    dumps = {}
    for path in sorted(SAMPLE_DUMP_DIR.glob("*_test_data.json")):
        db_name = path.stem.removesuffix("_test_data")
        rows = load_json(path)
        row = rows[0] if isinstance(rows, list) and rows else rows
        if isinstance(row, dict):
            dumps[db_name] = set(row.keys()) - {"db"}
    return dumps


# Named baselines used only to generate readable, stable variant names (e.g.
# "legacy_microarray_projinfo_plus_sample_tissue") for real column signatures
# that diverge from the two original hand-authored shapes -- every variant's
# actual columns still come straight from real dumps, not these baselines.
_RNASEQ_BASELINE_NAME = "rnaseq_simple"
_RNASEQ_BASELINE_CORE = {"data_bot_id", "data_probeset_id", "data_signal", "proj_id", "sample_id"}
_MICROARRAY_BASELINE_NAME = "legacy_microarray_projinfo"
_MICROARRAY_BASELINE_CORE = {
    "data_bot_id", "data_call", "data_p_val", "data_probeset_id",
    "data_signal", "proj_id", "sample_file_name", "sample_id",
}
# Legacy microarray databases document a companion proj_info table alongside
# sample_data; not derivable from the sample_data dumps, so attached as-is to
# every microarray-platform variant.
_PROJ_INFO_TABLE = {
    "columns": {
        "proj_id": {"role": "project"},
        "proj_title": {},
        "proj_pi": {},
        "proj_res_area": {},
        "proj_num_samps": {},
    }
}


def _variant_name(platform, signature):
    if platform == "rna_seq":
        base_name, baseline = _RNASEQ_BASELINE_NAME, _RNASEQ_BASELINE_CORE
    else:
        base_name, baseline = _MICROARRAY_BASELINE_NAME, _MICROARRAY_BASELINE_CORE
    if signature == baseline:
        return base_name
    extra = sorted(signature - baseline)
    missing = sorted(baseline - signature)
    suffix_parts = []
    if extra:
        suffix_parts.append("plus_" + "_".join(extra))
    if missing:
        suffix_parts.append("minus_" + "_".join(missing))
    return f"{base_name}_" + "_".join(suffix_parts)


def derive_schema_variants_from_dumps(master_db_list, sample_dumps):
    """Group every database into a schema_variant matching its OWN real
    sample_data columns (api/random_rows_json/), instead of forcing every
    database into one of two variants based on platform (rna_seq/microarray)
    alone regardless of its actual column shape -- the source of the ~47
    "schema_verified: false" mismatches this replaces. Every current database
    has a real dump, so every variant here is an exact observed signature,
    not a threshold-pooled approximation that only "mostly" fits.

    :returns: (schema_variants, db_variant) -- schema_variants is
        {variant_name: {"tables": {...}, "assigned_databases": n}} ready for
        the combined JSON; db_variant maps database name -> variant name.
    """
    platform_by_db = {
        db_name: db_info.get("platform", "unknown")
        for dbs in master_db_list.values()
        for db_name, db_info in dbs.items()
    }

    schema_variants = {}
    db_variant = {}
    variant_db_counts = defaultdict(int)

    for db_name, cols in sample_dumps.items():
        platform = platform_by_db.get(db_name, "unknown")
        signature = frozenset(cols)
        name = _variant_name(platform, signature)
        db_variant[db_name] = name
        variant_db_counts[name] += 1

        if name not in schema_variants:
            columns = {
                col: dict(COLUMN_META.get(col, {"type": None, "role": None}))
                for col in sorted(signature)
            }
            tables = {"sample_data": {"columns": columns}}
            if platform != "rna_seq":
                tables["proj_info"] = dict(_PROJ_INFO_TABLE)
            schema_variants[name] = {"tables": tables}

    for name, count in variant_db_counts.items():
        schema_variants[name]["assigned_databases"] = count

    return schema_variants, db_variant


def _eplant_scientific_names():
    """Scientific names as ePlant itself names each species.

    Sourced from EPLANT_SPECIES_FILE (scrape_view_databases.py), the per-project
    species filename ePlant's own XML data paths use (e.g. .../Arabidopsis_thaliana.xml).
    This is the same name that appears in the "ActiveSpecies=" query param once an
    ePlant project's landing page finishes its client-side redirect (confirmed against
    the eplant_potato example: ActiveSpecies=Solanum%20tuberosum -> Solanum_tuberosum),
    just with underscores in place of the URL's spaces. We use this filename directly
    rather than re-fetching each ActiveSpecies URL live, since that redirect only
    happens in-browser via JS and isn't present in the static HTML/XML a scraper sees;
    EPLANT_SPECIES_FILE is the same mapping scrape_species_view_info.py already relies
    on to successfully pull real data from these projects, so it's proven correct.

    Two ePlant projects are two live versions of the same barley species -- see
    INSTANCE_NOTES -- and both resolve to the same name, so no conflict there.
    """
    return {
        species.removeprefix("eplant_"): name.replace("_", " ")
        for species, name in EPLANT_SPECIES_FILE.items()
    }


# Curated fallback for species with no ePlant instance to source a name from
# (efp-only species). Kept as our own best-available nomenclature.
_FALLBACK_SCIENTIFIC_NAMES = {
    "actinidia": None,
    "apple": "Malus domestica",
    "arabidopsis": "Arabidopsis thaliana",
    "arachis": "Arachis hypogaea",
    "barley": "Hordeum vulgare",
    "brachypodium": "Brachypodium distachyon",
    "brassica": "Brassica rapa",
    "cacao": "Theobroma cacao",
    "camelina": "Camelina sativa",
    "cannabis": "Cannabis sativa",
    "canola": "Brassica napus",
    "cassava": "Manihot esculenta",
    "cuscuta": "Cuscuta campestris",
    "eucalyptus": "Eucalyptus grandis",
    "euphorbia": "Euphorbia pulcherrima",
    "grape": "Vitis vinifera",
    "human": "Homo sapiens",
    "kalanchoe": "Kalanchoe fedtschenkoi",
    "little_millet": "Panicum sumatrense",
    "lupin": "Lupinus angustifolius",
    "maize": "Zea mays",
    "mangosteen": "Garcinia mangostana",
    "marchantia": "Marchantia polymorpha",
    "medicago": "Medicago truncatula",
    "mouse": "Mus musculus",
    "oat": "Avena sativa",
    "phelipanche": "Phelipanche aegyptiaca",
    "physcomitrella": "Physcomitrium patens",
    "poplar": "Populus trichocarpa",
    "potato": "Solanum tuberosum",
    "quinoa": "Chenopodium quinoa",
    "rice": "Oryza sativa",
    "selaginella": "Selaginella moellendorffii",
    "sorghum": "Sorghum bicolor",
    "soybean": "Glycine max",
    "spruce": "Picea abies",
    "strawberry": "Fragaria vesca",
    "striga": "Striga hermonthica",
    "sugarcane": "Saccharum officinarum",
    "sunflower": "Helianthus annuus",
    "thellungiella": "Thellungiella halophila",
    "tomato": "Solanum lycopersicum",
    "triphysaria": "Triphysaria versicolor",  # not sure
    "triticale": "Triticosecale",
    "tung_tree": "Vernicia fordii",
    "wheat": "Triticum aestivum",
    "willow": "Salix purpurea",
}


def get_species_scientific_names(master_db_list):
    """Build species -> scientific_name map, preferring ePlant's own naming.

    For species with a live ePlant instance, the name comes from ePlant (see
    _eplant_scientific_names). Everything else -- efp-only species -- falls back
    to the curated list.
    """
    eplant_names = _eplant_scientific_names()

    result = {}
    for species in master_db_list.keys():
        if species in eplant_names:
            result[species] = {
                "scientific_name": eplant_names[species],
                "name_source": "eplant",
            }
        else:
            result[species] = {
                "scientific_name": _FALLBACK_SCIENTIFIC_NAMES.get(species),
                "name_source": "curated",
            }
    return result


def build_databases(master_db_list, view_info, schema_variants, db_regex_project, db_variant):
    """
    Build the databases section with full metadata, used_by, views, and SQL column structure.
    """
    databases = {}

    db_frontend_usage = defaultdict(lambda: {"efp": set(), "eplant": set()})

    for frontend_name, projects in view_info.items():
        frontend = frontend_name.lower()

        for project_key, views_list in projects.items():
            for view_info_obj in views_list:
                db = view_info_obj.get("database")
                view_name = view_info_obj.get("view_name")
                instance = project_key

                if db and view_name:
                    db_frontend_usage[db][frontend].add((instance, view_name))

    for species, dbs in master_db_list.items():
        for db_name, db_info in dbs.items():
            instance_families = set()
            used_by = []

            for frontend in ["efp", "eplant"]:
                for instance, view_name in db_frontend_usage[db_name][frontend]:
                    instance_families.add(instance)
                    used_by.append({
                        "frontend": frontend,
                        "instance": instance,
                        "view": view_name
                    })

            source = db_info.get("source", "unknown")
            platform = db_info.get("platform", "unknown")
            gene_id_class = "gene_model" if platform == "rna_seq" else "probeset"

            variant = db_variant.get(db_name)
            if variant is not None:
                schema_verified = True
                schema_verification_note = (
                    f"Schema variant '{variant}' derived directly from this database's own sample dump."
                )
            else:
                variant = "rnaseq_simple" if platform == "rna_seq" else "legacy_microarray_projinfo"
                schema_verified = False
                schema_verification_note = "No sample dump available to verify against."

            db_entry = {
                "species": species,
                "instance_families": sorted(list(instance_families)) if instance_families else None,
                "source": source,
                "platform": platform,
                "schema_variant": variant,
                "schema_verified": schema_verified,
                "schema_verification_note": schema_verification_note,
                "value_semantics": db_info.get("value_semantics"),
                "gene_id_class": gene_id_class,
                "gene_id_namespace": db_info.get("gene_id_namespace"),
                "regex_project": db_regex_project.get(db_name),
                "used_by": used_by,
                "views": {}
            }

            databases[db_name] = db_entry

    for frontend_name, projects in view_info.items():
        frontend = frontend_name.lower()

        for project_key, views_list in projects.items():
            for view_info_obj in views_list:
                db = view_info_obj.get("database")
                view_name = view_info_obj.get("view_name")
                groups = view_info_obj.get("groups", {})
                proj_ids = view_info_obj.get("proj_ids", [])

                if db not in databases:
                    continue

                view_key = f"{project_key}::{view_name}"

                databases[db]["views"][view_key] = {
                    "frontend": frontend,
                    "instance": project_key,
                    "display_name": view_name,
                    "proj_ids": proj_ids,
                    "sample_groups": groups
                }

    return databases


def build_combined_json():
    """Build and output the combined master JSON."""
    print("Loading input files...")
    master_db_list = load_json("data/efp_info/master_db_list.json")
    view_info = load_json(VIEW_INFO_FILE)

    print("Patching efp_human sample groups from local eFP Human XML...")
    if patch_human_view_groups(view_info):
        with open(VIEW_INFO_FILE, "w") as f:
            json.dump(view_info, f, indent=2)
        print(f"  Updated {VIEW_INFO_FILE}")
    else:
        print("  Nothing to patch")

    print("Loading Vincent's sample_data dumps (api/random_rows_json/)...")
    sample_dumps = load_sample_dumps()

    print("Building schema variants from real sample dumps...")
    schema_variants, db_variant = derive_schema_variants_from_dumps(master_db_list, sample_dumps)
    print(f"  {len(schema_variants)} distinct schema shapes across {len(db_variant)} databases")

    print("Loading Vincent's regex registry...")
    validation_patterns, db_regex_project = get_validation_patterns()
    probeset_samples = load_probeset_samples()
    db_regex_project, demoted = verify_regex_projects(db_regex_project, validation_patterns, probeset_samples)
    print(f"  {len(validation_patterns)} eFP project patterns covering {len(db_regex_project)} databases")
    if demoted:
        print(f"  Demoted {len(demoted)} unverified regex_project assignments to species-fallback (pass rate too low against real sample data):")
        for db, (project, rate) in sorted(demoted.items()):
            print(f"    {db}: {project} ({rate:.0%} pass rate)")

    print("Building databases...")
    databases = build_databases(master_db_list, view_info, schema_variants, db_regex_project, db_variant)
    n_verified = sum(1 for db in databases.values() if db["schema_verified"])
    n_flagged = len(databases) - n_verified
    print(f"  {len(sample_dumps)} dumps checked -- {n_verified} verified, {n_flagged} flagged (no sample dump to derive a variant from)")

    print("Building species map...")
    species = get_species_scientific_names(master_db_list)

    print("Building output structure...")
    output = {
        "species": species,
        "schema_variants": schema_variants,
        "instance_notes": INSTANCE_NOTES,
        "validation_patterns": validation_patterns,
        "databases": databases
    }

    out_file = Path("data/efp_info/combined_master.json")
    print(f"Writing to {out_file}...")
    with open(out_file, "w") as f:
        json.dump(output, f, indent=2, sort_keys=False)

    n_dbs = len(databases)
    n_species = len(species)

    print("\n✓ Combined master JSON generated:")
    print(f"  Species: {n_species}")
    print(f"  Databases: {n_dbs}")
    print(f"  Output: {out_file}")


if __name__ == "__main__":
    build_combined_json()
