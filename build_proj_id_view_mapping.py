"""
Reena Obmina | BCB330 Project 2025-2026 | University of Toronto

Task 3 (Jun 11 2026): for databases like atgenexp where multiple eFP/ePlant
views/papers share one physical database, derive which proj_id(s) belong to
which view, by cross-referencing each view's known sample names (from Task 1's
XML scrape) against the real proj_id values recorded for those exact sample
names in the production sample data.

A database is "genuinely multi-project" if its views resolve to disjoint (or
mostly disjoint) proj_id sets — i.e. each view really is a separate
paper/experiment. If two differently-named views resolve to the same proj_id
set, they're not separate projects — just the eFP and ePlant frontends using
different display names for the one underlying dataset.

Reads:  data/efp_info/efp_eplant_species_view_info.json — view -> sample names (Task 1)
        api/random_rows_json/{db}_test_data.json — real (proj_id, data_bot_id) pairs
Writes: proj_id_view_mapping.json — per multi-view db: view -> proj_id set,
        classified as "multi_project" or "duplicate_view_names"
"""

import json
from collections import defaultdict
from pathlib import Path

INFO_PATH = "data/efp_info/efp_eplant_species_view_info.json"
SAMPLE_DIR = Path("api/random_rows_json")


def build_view_samples():
    """Map (db, view_name) -> set of sample names, from Task 1's XML scrape."""
    info = json.load(open(INFO_PATH))
    view_samples = defaultdict(set)
    for source in ("efp", "eplant"):
        for _key, views in info[source].items():
            for v in views:
                db = v.get("database")
                if not db:
                    continue
                samples = set()
                for group in v.get("groups", {}).values():
                    samples.update(group.get("controls", []))
                    for tissue_samples in group.get("treatments", {}).values():
                        samples.update(tissue_samples)
                view_samples[(db, v["view_name"])] |= samples
    return view_samples


def load_bot_to_proj(db):
    path = SAMPLE_DIR / f"{db}_test_data.json"
    if not path.exists():
        return {}
    rows = json.load(open(path))
    bot_to_proj = defaultdict(set)
    for row in rows:
        bot_id = row.get("data_bot_id")
        proj_id = row.get("proj_id")
        if bot_id is not None and proj_id is not None:
            bot_to_proj[bot_id].add(str(proj_id))
    return bot_to_proj


def main():
    view_samples = build_view_samples()

    by_db = defaultdict(dict)
    for (db, view_name), samples in view_samples.items():
        by_db[db][view_name] = samples

    multi_view_dbs = {db: views for db, views in by_db.items() if len(views) > 1}

    report = {}
    for db, views in sorted(multi_view_dbs.items()):
        bot_to_proj = load_bot_to_proj(db)
        view_proj_ids = {}
        for view_name, samples in views.items():
            proj_ids = set()
            matched = 0
            for s in samples:
                if s in bot_to_proj:
                    proj_ids |= bot_to_proj[s]
                    matched += 1
            view_proj_ids[view_name] = {
                "n_view_samples": len(samples),
                "n_matched_in_real_data_sample": matched,
                "proj_ids": sorted(proj_ids),
            }

        # Classify: do any two views share NO proj_ids in common (genuine
        # separate projects) vs all views resolving to the same proj_id set
        # (same project, just different eFP/ePlant display names)?
        proj_id_sets = [set(v["proj_ids"]) for v in view_proj_ids.values() if v["proj_ids"]]
        if len(proj_id_sets) < 2:
            classification = "insufficient_data"
        else:
            all_identical = all(s == proj_id_sets[0] for s in proj_id_sets)
            any_disjoint = any(
                proj_id_sets[i].isdisjoint(proj_id_sets[j])
                for i in range(len(proj_id_sets))
                for j in range(i + 1, len(proj_id_sets))
            )
            if all_identical:
                classification = "duplicate_view_names"
            elif any_disjoint:
                classification = "multi_project"
            else:
                classification = "partial_overlap"

        report[db] = {"classification": classification, "views": view_proj_ids}

    out_file = "proj_id_view_mapping.json"
    with open(out_file, "w") as f:
        json.dump(report, f, indent=2)

    counts = defaultdict(int)
    for r in report.values():
        counts[r["classification"]] += 1
    print(f"Checked {len(report)} multi-view databases.")
    for cls, n in sorted(counts.items()):
        print(f"  {cls}: {n}")
    print(f"Report written to {out_file}")


if __name__ == "__main__":
    main()
