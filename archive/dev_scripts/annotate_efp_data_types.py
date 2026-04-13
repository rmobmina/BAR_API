"""
Reena Obmina | BCB330 Project 2025-2026 | University of Toronto

Annotates each EFP view with a ``data_type`` field: ``"Microarray"``, ``"RNA-Seq"``, or ``"Unknown"``.

Reads:  data/efp_info/efp_species_view_info.json
Writes: data/efp_info/efp_species_view_info_typed.json

Classification is based on the database name using the ``MICROARRAY_DBS`` and
``RNASEQ_DBS`` sets defined below. Views labelled ``"Unknown"`` need manual
review — search the output file for ``"Unknown"`` and add the database to the
appropriate set.
"""

from __future__ import annotations

import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Classification sets — extend these as you confirm more databases
# ---------------------------------------------------------------------------

MICROARRAY_DBS: set[str] = {
    # Arabidopsis ATH1 Affymetrix chip (AtGenExpress + individual studies)
    "affydb",
    "arabidopsis_ecotypes",
    "atgenexp",
    "atgenexp_hormone",
    "atgenexp_pathogen",
    "atgenexp_plus",
    "atgenexp_stress",
    "dna_damage",
    "embryo",
    "germination",
    "guard_cell",
    "gynoecium",
    "hnahal",
    "lateral_root_initiation",
    "light_series",
    "meristem_db",
    "meristem_db_new",
    "root",
    "rohan",
    "rpatel",
    "seed_db",
    "seedcoat",
    "shoot_apex",
    "silique",
    # Barley Affymetrix chip
    "barley_mas",
    "barley_rma",
    # Maize Affymetrix chip (GRMZM* → AB*_at / AC*_FGT* probesets; confirmed from sample data)
    "maize_gdowns",
    "maize_RMA_linear",
    "maize_RMA_log",
    # Tomato Affymetrix GeneChip (Solyc* → TU* probesets; confirmed from sample data)
    "tomato",
    # Medicago Affymetrix chip
    "medicago_mas",
    "medicago_rma",
    # Poplar Affymetrix chip
    "poplar",
    # Rice Affymetrix chip
    "rice_mas",
    "rice_rma",
    # Triticale microarray
    "triticale",
    "triticale_mas",
    # Grape Affymetrix chip (VIT_* → CHRUN_* lookup)
    "grape_developmental",
}

RNASEQ_DBS: set[str] = {
    # Arabidopsis RNA-Seq
    "klepikova",
    "single_cell",
    # Camelina RNA-Seq (FPKM / TPM in view names)
    "camelina",
    "camelina_tpm",
    # Actinidia RNA-Seq
    "actinidia_bud_development",
    "actinidia_flower_fruit_development",
    "actinidia_postharvest",
    "actinidia_vegetative_growth",
    # Arachis RNA-Seq
    "arachis",
    # Cacao RNA-Seq
    "cacao_developmental_atlas",
    "cacao_developmental_atlas_sca",
    "cacao_drought_diurnal_atlas",
    "cacao_drought_diurnal_atlas_sca",
    "cacao_infection",
    "cacao_leaf",
    "cacao_meristem_atlas_sca",
    "cacao_seed_atlas_sca",
    # Canola RNA-Seq
    "canola_seed",
    # Cannabis RNA-Seq
    "cannabis",
    # Little millet RNA-Seq
    "little_millet",
    # Lupin RNA-Seq
    "lupin_lcm_leaf",
    "lupin_lcm_pod",
    "lupin_lcm_stem",
    "lupin_whole_plant",
    # Mangosteen RNA-Seq
    "mangosteen_aril_vs_rind",
    "mangosteen_callus",
    "mangosteen_diseased_vs_normal",
    "mangosteen_fruit_ripening",
    "mangosteen_seed_development",
    "mangosteen_seed_development_germination",
    "mangosteen_seed_germination",
    # Barley RNA-Seq (HORVU.* gene IDs; confirmed from sample data)
    "barley_seed",
    "barley_spike_meristem",
    "barley_spike_meristem_v3",
    # Eucalyptus RNA-Seq (Eucgr.* gene IDs; confirmed from sample data)
    "eucalyptus",
    # Lupin RNA-Seq (additional database)
    "lupin_pod_seed",
    # Maize RNA-Seq (Zm00001d* gene IDs; confirmed from sample data)
    "maize_buell_lab",
    # Medicago RNA-Seq
    "medicago_root",
    "medicago_root_v5",
    "medicago_seed",
    # Potato RNA-Seq (PGSC0003DMG* gene IDs stored directly; confirmed from sample data)
    "potato_dev",
    "potato_stress",
    "potato_wounding",
    # Rice RNA-Seq (LOC_Os* gene IDs; confirmed from sample data)
    "rice_drought_heat_stress",
    "rice_leaf_gradient",
    "rice_maize_comparison",
    "rice_root",
    # Sugarcane RNA-Seq (Sh01_g* gene IDs; confirmed from sample data)
    "sugarcane_leaf",
    "sugarcane_culms",
    # Tomato RNA-Seq (Solyc* gene IDs; ILs databases only — main tomato db is Microarray)
    "tomato_ils",
    "tomato_ils2",
    "tomato_ils3",
    "tomato_meristem",
    "tomato_renormalized",
    "tomato_root",
    "tomato_root_field_pot",
    "tomato_s_pennellii",
    "tomato_seed",
    "tomato_shade_mutants",
    "tomato_shade_timecourse",
    "tomato_trait",
    # Wheat RNA-Seq (TraesCS* gene IDs; confirmed from sample data)
    "wheat",
    "wheat_abiotic_stress",
    "wheat_embryogenesis",
    "wheat_meiosis",
    "wheat_root",
    "durum_wheat_abiotic_stress",
    "durum_wheat_biotic_stress",
    "durum_wheat_development",
    # Willow RNA-Seq (Trinity IDs; confirmed from sample data — SapurV1A lookup still needed)
    "willow",
    # Sunflower RNA-Seq (Ha1_* gene IDs; confirmed from sample data)
    "sunflower",
}

# ---------------------------------------------------------------------------
# Everything not in either set above will be labelled "Unknown"
# Run the script, then search for "Unknown" in the output file to find gaps.
# ---------------------------------------------------------------------------


def classify(db_name: str) -> str:
    """Return the data type label for a given database name.

    :param db_name: Database name to classify (e.g., 'embryo', 'klepikova').
    :returns: 'Microarray', 'RNA-Seq', or 'Unknown'.
    :rtype: str
    """
    if db_name in MICROARRAY_DBS:
        return "Microarray"
    if db_name in RNASEQ_DBS:
        return "RNA-Seq"
    return "Unknown"


def main() -> None:
    """Read the untyped view info JSON, annotate each view with data_type, and write output."""
    repo_root = Path(__file__).resolve().parent.parent
    src = repo_root / "data" / "efp_info" / "efp_species_view_info.json"
    dst = repo_root / "data" / "efp_info" / "efp_species_view_info_typed.json"

    with src.open() as f:
        data = json.load(f)

    unknown: list[tuple[str, str, str]] = []  # (species, view, database)

    for species, sp_entry in data.items():
        views = sp_entry["data"]["views"]
        for view_name, view_data in views.items():
            db = view_data["database"]
            data_type = classify(db)
            view_data["data_type"] = data_type
            if data_type == "Unknown":
                unknown.append((species, view_name, db))

    with dst.open("w") as f:
        json.dump(data, f, indent=2)

    print(f"Written → {dst}")
    print(f"\nTotal views annotated: {sum(len(v['data']['views']) for v in data.values())}")

    if unknown:
        print(f"\n{'=' * 60}")
        print(f"  {len(unknown)} views still marked 'Unknown' — update the sets above:")
        print(f"{'=' * 60}")
        for species, view, db in sorted(unknown):
            print(f"  {species:25s}  {view:50s}  db={db}")
    else:
        print("\nAll views classified — no Unknowns.")


if __name__ == "__main__":
    main()
