"""
Task 4 (Jun 2026): assemble the final "master list" of every BAR database
discovered across both frontends, organized the way Vincent asked for --
by species, noting eFP vs ePlant vs both, and microarray vs RNA-seq.

Platform (microarray vs RNA-seq) is determined from the real sample IDs
themselves (GeneIdUtils.is_probeset_id), not from which validator code path
happens to handle a database, since a handful of gene-ID (RNA-seq) databases
are routed through Vincent's per-project eFP regex anyway for better coverage
(see DATABASE_EFP_PROJECT comments in gene_id_utils.py) -- that routing is an
implementation detail, not the underlying data type.

Note on atgenexp-style databases: a handful of databases (atgenexp_plus,
atgenexp_pathogen, maize_RMA_linear, tomato_renormalized, etc.) bundle multiple
papers/projects into one physical database -- one view per paper, not one view
per database like everywhere else. proj_id_view_mapping.json (built by
build_proj_id_view_mapping.py) already works out, per view, which proj_id(s)
in the real sample data that view actually corresponds to, and classifies the
database as "multi_project" (genuinely separate papers, disjoint proj_ids) vs
"duplicate_view_names" (same proj_id, just different eFP/ePlant display names)
vs "partial_overlap". This script folds that breakdown into the master list
under "proj_id_breakdown" so the per-paper granularity isn't lost when an API
caller only has the database name to go on.

Reads:  data/efp_info/db_source_summary.json   -- db -> efp/eplant/both (scrape_species_view_info.py)
        db_regex_coverage_report.csv           -- per-db validation results (validate_db_regex_coverage.py)
        species_databases.json                 -- project -> view -> db (scrape_view_databases.py)
        proj_id_view_mapping.json              -- per-view proj_id breakdown (build_proj_id_view_mapping.py)
        api/utils/gene_id_utils.DATABASE_SPECIES -- db -> canonical species key
Writes: data/efp_info/master_db_list.json -- { species: { db: {source, platform, views, validation, proj_id_breakdown} } }
"""

import csv
import json
import sys
import types
from collections import defaultdict
from pathlib import Path

sys.modules.setdefault("api", types.ModuleType("api"))
sys.modules["api"].__path__ = ["api"]
sys.modules.setdefault("api.utils", types.ModuleType("api.utils"))
sys.modules["api.utils"].__path__ = ["api/utils"]

from api.utils.gene_id_utils import DATABASE_SPECIES  # noqa: E402


def load_coverage():
    with open("db_regex_coverage_report.csv") as f:
        return {r["database"]: r for r in csv.DictReader(f)}


def load_views_by_db():
    """Invert species_databases.json (project -> view -> db) into db -> {project: [views]}."""
    species_db = json.load(open("species_databases.json"))
    views_by_db = defaultdict(lambda: defaultdict(list))
    for project, views in species_db.items():
        for view_name, db in views.items():
            views_by_db[db][project].append(view_name)
    return views_by_db


def main():
    db_sources = json.load(open("data/efp_info/db_source_summary.json"))
    coverage = load_coverage()
    views_by_db = load_views_by_db()
    proj_id_mapping = json.load(open("proj_id_view_mapping.json"))

    # coverage (db_regex_coverage_report.csv) is the full universe -- every db with
    # real sample data in api/random_rows_json/, including ones no longer reachable
    # from any live dropdown ("legacy_not_in_dropdown"). db_sources only has the
    # live-discoverable subset. Union them so the master list is genuinely complete.
    all_dbs = set(coverage) | set(db_sources)

    master = defaultdict(dict)
    n_multi_project_dbs = 0
    n_legacy = 0
    for db in sorted(all_dbs):
        species = DATABASE_SPECIES.get(db, "unknown")
        row = coverage.get(db, {})
        source = row.get("source", db_sources.get(db, "unknown"))
        if source == "legacy_not_in_dropdown":
            n_legacy += 1
        looks_like_probeset = row.get("looks_like_probeset") == "True"

        entry = {
            "source": source,
            "platform": "microarray" if looks_like_probeset else "rna_seq",
            "views": dict(views_by_db.get(db, {})),
            "validation": {
                "n_samples": int(row.get("n_samples", 0)),
                "n_pass": int(row.get("n_pass", 0)),
                "n_fail": int(row.get("n_fail", 0)),
            },
        }

        proj_id_info = proj_id_mapping.get(db)
        if proj_id_info:
            entry["proj_id_breakdown"] = proj_id_info
            if proj_id_info["classification"] == "multi_project":
                n_multi_project_dbs += 1

        master[species][db] = entry

    out_file = Path("data/efp_info/master_db_list.json")
    with open(out_file, "w") as f:
        json.dump(dict(sorted(master.items())), f, indent=2, sort_keys=False)

    n_species = len(master)
    n_dbs = sum(len(dbs) for dbs in master.values())
    n_microarray = sum(1 for dbs in master.values() for d in dbs.values() if d["platform"] == "microarray")
    n_rna_seq = n_dbs - n_microarray
    n_efp_only = sum(1 for dbs in master.values() for d in dbs.values() if d["source"] == "efp")
    n_eplant_only = sum(1 for dbs in master.values() for d in dbs.values() if d["source"] == "eplant")
    n_both = sum(1 for dbs in master.values() for d in dbs.values() if d["source"] == "both")

    print(f"Species: {n_species} | Databases: {n_dbs} ({n_legacy} legacy/not in any current dropdown)")
    print(f"  eFP-only: {n_efp_only} | ePlant-only: {n_eplant_only} | both: {n_both}")
    print(f"  microarray: {n_microarray} | rna_seq: {n_rna_seq}")
    print(f"  Multi-project databases (e.g. atgenexp_*): {n_multi_project_dbs}")
    print(f"Output written to {out_file}")


if __name__ == "__main__":
    main()
