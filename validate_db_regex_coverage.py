"""
Reena Obmina | BCB330 Project 2025-2026 | University of Toronto

Task 2 (Jun 11 2026): test Vincent's per-project eFP regexes against every
database that has real sample data in api/random_rows_json/, to find
databases whose probeset/gene IDs the current production validator
(GeneIdUtils.validate_gene_for_database) would incorrectly reject.

The universe tested is the FULL random_rows_json folder, not just the
databases reachable from a live eFP/ePlant dropdown today (data/efp_info/
db_source_summary.json) -- some databases Vincent has sample data for are no
longer linked from any current dropdown (legacy/retired views) but are still
queryable directly by db name and already validator-ready (DATABASE_SPECIES /
DATABASE_EFP_PROJECT), so they're tested too and flagged via in_master_list.

Reads:  api/random_rows_json/{db}_test_data.json — real sample rows, one file per db
        data/efp_info/db_source_summary.json — db -> efp/eplant/both, for dbs reachable live
        api/utils/gene_id_utils.py / bar_utils.py — current production validators
Writes: db_regex_coverage_report.csv — one row per db: pass/fail counts + gap flag
"""

import csv
import json
import sys
import types
from pathlib import Path

# importing api.utils.gene_id_utils normally runs api/__init__.py's create_app(),
# which tries to connect to MySQL even for this standalone script. Pre-register
# empty stand-in packages so Python loads the submodules directly instead.
sys.modules.setdefault("api", types.ModuleType("api"))
sys.modules["api"].__path__ = ["api"]
sys.modules.setdefault("api.utils", types.ModuleType("api.utils"))
sys.modules["api.utils"].__path__ = ["api/utils"]

from api.utils.gene_id_utils import DATABASE_EFP_PROJECT, DATABASE_SPECIES, GeneIdUtils  # noqa: E402

SAMPLE_DIR = Path("api/random_rows_json")


def load_samples(db):
    path = SAMPLE_DIR / f"{db}_test_data.json"
    if not path.exists():
        return None
    with open(path) as f:
        rows = json.load(f)
    ids = []
    seen = set()
    for row in rows:
        gene_id = row.get("data_probeset_id")
        if gene_id and gene_id not in seen:
            seen.add(gene_id)
            ids.append(gene_id)
    return ids


def main():
    with open("data/efp_info/db_source_summary.json") as f:
        db_sources = json.load(f)

    sample_dbs = {p.name[: -len("_test_data.json")] for p in SAMPLE_DIR.glob("*_test_data.json")}
    all_dbs = sample_dbs | set(db_sources)

    report_rows = []
    gap_count = 0
    no_sample_count = 0
    no_species_mapping_count = 0

    for db in sorted(all_dbs):
        source = db_sources.get(db, "legacy_not_in_dropdown")
        sample_ids = load_samples(db)
        if sample_ids is None:
            no_sample_count += 1
            report_rows.append(
                {
                    "database": db,
                    "source": source,
                    "in_master_list": db in db_sources,
                    "has_species_mapping": db in DATABASE_SPECIES,
                    "has_efp_project_override": db in DATABASE_EFP_PROJECT,
                    "n_samples": 0,
                    "n_pass": 0,
                    "n_fail": 0,
                    "looks_like_probeset": "",
                    "failing_ids": "NO SAMPLE DATA",
                }
            )
            continue
        if db not in DATABASE_SPECIES and db not in DATABASE_EFP_PROJECT:
            no_species_mapping_count += 1

        n_pass = 0
        failing_ids = []
        any_probeset_shaped = False
        for gene_id in sample_ids:
            if GeneIdUtils.is_probeset_id(gene_id):
                any_probeset_shaped = True
            if GeneIdUtils.validate_gene_for_database(gene_id, db):
                n_pass += 1
            else:
                failing_ids.append(gene_id)

        is_gap = bool(failing_ids)
        if is_gap:
            gap_count += 1

        report_rows.append(
            {
                "database": db,
                "source": source,
                "in_master_list": db in db_sources,
                "has_species_mapping": db in DATABASE_SPECIES,
                "has_efp_project_override": db in DATABASE_EFP_PROJECT,
                "n_samples": len(sample_ids),
                "n_pass": n_pass,
                "n_fail": len(failing_ids),
                "looks_like_probeset": any_probeset_shaped,
                "failing_ids": "|".join(failing_ids[:5]),
            }
        )

    out_file = "db_regex_coverage_report.csv"
    with open(out_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(report_rows[0].keys()))
        writer.writeheader()
        writer.writerows(report_rows)

    print(f"Checked {len(all_dbs)} databases ({len(db_sources)} in live master list, "
          f"{len(all_dbs) - len(db_sources)} legacy/not currently linked from any dropdown).")
    print(f"  No sample data found: {no_sample_count}")
    print(f"  No species/eFP-project mapping at all: {no_species_mapping_count}")
    print(f"  Databases with >=1 real sample ID rejected by current validation: {gap_count}")
    print(f"Report written to {out_file}")


if __name__ == "__main__":
    main()
