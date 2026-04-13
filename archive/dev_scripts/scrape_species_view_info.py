"""
Reena Obmina | BCB330 Project 2025-2026 | University of Toronto

Scrapes groups, controls, and treatments for every view of every species.

Reads:  each species' view XML at {efp_base}/data/{view_name}.xml
Writes: efp_species_view_info.json — full nested structure used by the API,
        keyed as ``{ species: { wasSuccessful, data: { species, views: { ... } } } }``

This is the clean extraction pass. For duplicate auditing run
audit_efp_xml_duplicates.py instead.
"""

import requests
import xml.etree.ElementTree as ET
import json

# efp base urls
EFP_SITES = {
    "actinidia": "https://bar.utoronto.ca/efp_actinidia/cgi-bin/efpWeb.cgi",
    "arabidopsis": "https://bar.utoronto.ca/efp/cgi-bin/efpWeb.cgi",
    "arabidopsis seedcoat": "https://bar.utoronto.ca/efp_seedcoat/cgi-bin/efpWeb.cgi",
    "arachis": "https://bar.utoronto.ca/efp_arachis/cgi-bin/efpWeb.cgi",
    "barley": "https://bar.utoronto.ca/efpbarley/cgi-bin/efpWeb.cgi",
    "brachypodium": "https://bar.utoronto.ca/efp_brachypodium/cgi-bin/efpWeb.cgi",
    "brassica rapa": "https://bar.utoronto.ca/efp_brassica_rapa/cgi-bin/efpWeb.cgi",
    "cacao ccn": "https://bar.utoronto.ca/efp_cacao_ccn/cgi-bin/efpWeb.cgi",
    "cacao sca": "https://bar.utoronto.ca/efp_cacao_sca/cgi-bin/efpWeb.cgi",
    "cacao tc": "https://bar.utoronto.ca/efp_cacao_tc/cgi-bin/efpWeb.cgi",
    "camelina": "https://bar.utoronto.ca/efp_camelina/cgi-bin/efpWeb.cgi",
    "cannabis": "https://bar.utoronto.ca/efp_cannabis/cgi-bin/efpWeb.cgi",
    "canola": "https://bar.utoronto.ca/efp_canola/cgi-bin/efpWeb.cgi",
    "eutrema": "https://bar.utoronto.ca/efp_eutrema/cgi-bin/efpWeb.cgi",
    "grape": "https://bar.utoronto.ca/efp_grape/cgi-bin/efpWeb.cgi",
    "kalanchoe": "https://bar.utoronto.ca/efp_kalanchoe/cgi-bin/efpWeb.cgi",
    "little millet": "https://bar.utoronto.ca/efp_little_millet/cgi-bin/efpWeb.cgi",
    "lupin": "https://bar.utoronto.ca/efp_lupin/cgi-bin/efpWeb.cgi",
    "maize": "https://bar.utoronto.ca/efp_maize/cgi-bin/efpWeb.cgi",
    "mangosteen": "https://bar.utoronto.ca/efp_mangosteen/cgi-bin/efpWeb.cgi",
    "medicago": "https://bar.utoronto.ca/efpmedicago/cgi-bin/efpWeb.cgi",
    "poplar": "https://bar.utoronto.ca/efppop/cgi-bin/efpWeb.cgi",
    "potato": "https://bar.utoronto.ca/efp_potato/cgi-bin/efpWeb.cgi",
    "rice": "https://bar.utoronto.ca/efprice/cgi-bin/efpWeb.cgi",
    "soybean": "https://bar.utoronto.ca/efpsoybean/cgi-bin/efpWeb.cgi",
    "strawberry": "https://bar.utoronto.ca/efp_strawberry/cgi-bin/efpWeb.cgi",
    "tomato": "https://bar.utoronto.ca/efp_tomato/cgi-bin/efpWeb.cgi",
    "triticale": "https://bar.utoronto.ca/efp_triticale/cgi-bin/efpWeb.cgi",
    "wheat": "https://bar.utoronto.ca/efp_wheat/cgi-bin/efpWeb.cgi"
}

# database and view mappings for each species
species_databases = {
    "actinidia": {
        "Bud_Development": "actinidia_bud_development",
        "Flower_Fruit_Development": "actinidia_flower_fruit_development",
        "Postharvest": "actinidia_postharvest",
        "Vegetative_Growth": "actinidia_vegetative_growth"
    },
    "arabidopsis": {
        "Abiotic_Stress": "atgenexp_stress",
        "Abiotic_Stress_II": "atgenexp_stress",
        "Biotic_Stress": "atgenexp_pathogen",
        "Biotic_Stress_II": "atgenexp_pathogen",
        "Chemical": "atgenexp_hormone",
        "DNA_Damage": "dna_damage",
        "Development_RMA": "atgenexp",
        "Developmental_Map": "atgenexp_plus",
        "Developmental_Mutants": "atgenexp_plus",
        "Embryo": "embryo",
        "Germination": "germination",
        "Guard_Cell": "guard_cell",
        "Gynoecium": "gynoecium",
        "Hormone": "atgenexp_hormone",
        "Klepikova_Atlas": "klepikova",
        "Lateral_Root_Initiation": "lateral_root_initiation",
        "Light_Series": "light_series",
        "Natural_Variation": "arabidopsis_ecotypes",
        "Regeneration": "meristem_db",
        "Root": "root",
        "Root_II": "root",
        "Seed": "seed_db",
        "Shoot_Apex": "shoot_apex",
        "Silique": "silique",
        "Single_Cell": "single_cell",
        "Tissue_Specific": "atgenexp_plus"
    },
    "arabidopsis seedcoat": {
        "Seed_Coat": "seedcoat"
    },
    "arachis": {
        "Arachis_Atlas": "arachis"
    },
    "barley": {
        "barley_mas": "barley_mas",
        "barley_rma": "barley_rma"
    },
    "brachypodium": {
        "Brachypodium_Atlas": "brachypodium",
        "Brachypodium_Grains": "brachypodium_grains",
        "Brachypodium_Spikes": "brachypodium_Bd21",
        "Photo_Thermocycle": "brachypodium_photo_thermocycle"
    },
    "brassica rapa": {
        "Embryogenesis": "brassica_rapa"
    },
    "cacao ccn": {
        "Developmental_Atlas": "cacao_developmental_atlas",
        "Drought_Diurnal_Atlas": "cacao_drought_diurnal_atlas"
    },
    "cacao sca": {
        "Developmental_Atlas": "cacao_developmental_atlas_sca",
        "Drought_Diurnal_Atlas": "cacao_drought_diurnal_atlas_sca",
        "Meristem_Atlas": "cacao_meristem_atlas_sca",
        "Seed_Atlas": "cacao_seed_atlas_sca"
    },
    "cacao tc": {
        "Cacao_Infection": "cacao_infection",
        "Cacao_Leaf": "cacao_leaf"
    },
    "camelina": {
        "Developmental_Atlas_FPKM": "camelina",
        "Developmental_Atlas_TPM": "camelina_tpm"
    },
    "cannabis": {
        "Cannabis_Atlas": "cannabis"
    },
    "canola": {
        "Canola_Seed": "canola_seed"
    },
    "eutrema": {
        "Eutrema": "thellungiella_db"
    },
    "grape": {
        "grape_developmental": "grape_developmental"
    },
    "kalanchoe": {
        "Light_Response": "kalanchoe"
    },
    "little millet": {
        "Life_Cycle": "little_millet"
    },
    "lupin": {
        "LCM_Leaf": "lupin_lcm_leaf",
        "LCM_Pod": "lupin_lcm_pod",
        "LCM_Stem": "lupin_lcm_stem",
        "Whole_Plant": "lupin_whole_plant"
    },
    "maize": {
        "Downs_et_al_Atlas": "maize_gdowns",
        "Early_Seed": "maize_early_seed",
        "Embryonic_Leaf_Development": "maize_embryonic_leaf_development",
        "Hoopes_et_al_Atlas": "maize_buell_lab",
        "Hoopes_et_al_Stress": "maize_buell_lab",
        "Maize_Kernel": "maize_early_seed",
        "Maize_Root": "maize_root",
        "Sekhon_et_al_Atlas": "maize_RMA_linear",
        "Tassel_and_Ear_Primordia": "maize_ears",
        "maize_iplant": "maize_iplant",
        "maize_leaf_gradient": "maize_leaf_gradient",
        "maize_rice_comparison": "maize_rice_comparison"
    },
    "mangosteen": {
        "Aril_vs_Rind": "mangosteen_aril_vs_rind",
        "Callus": "mangosteen_callus",
        "Diseased_vs_Normal": "mangosteen_diseased_vs_normal",
        "Fruit_Ripening": "mangosteen_fruit_ripening",
        "Seed_Development": "mangosteen_seed_development",
        "Seed_Germination": "mangosteen_seed_germination"
    },
    "medicago": {
        "medicago_mas": "medicago_mas",
        "medicago_rma": "medicago_rma",
        "medicago_seed": "medicago_seed"
    },
    "poplar": {
        "Poplar": "poplar",
        "PoplarTreatment": "poplar"
    },
    "potato": {
        "Potato_Developmental": "potato_dev",
        "Potato_Stress": "potato_stress"
    },
    "rice": {
        "rice_drought_heat_stress": "rice_drought_heat_stress",
        "rice_leaf_gradient": "rice_leaf_gradient",
        "rice_maize_comparison": "rice_maize_comparison",
        "rice_mas": "rice_mas",
        "rice_rma": "rice_rma",
        "riceanoxia_mas": "rice_mas",
        "riceanoxia_rma": "rice_rma",
        "ricestigma_mas": "rice_mas",
        "ricestigma_rma": "rice_rma",
        "ricestress_mas": "rice_mas",
        "ricestress_rma": "rice_rma"
    },
    "soybean": {
        "soybean": "soybean",
        "soybean_embryonic_development": "soybean_embryonic_development",
        "soybean_heart_cotyledon_globular": "soybean_heart_cotyledon_globular",
        "soybean_senescence": "soybean_senescence",
        "soybean_severin": "soybean_severin"
    },
    "strawberry": {
        "Developmental_Map_Strawberry_Flower_and_Fruit": "strawberry",
        "Strawberry_Green_vs_White_Stage": "strawberry"
    },
    "tomato": {
        "ILs_Leaf_Chitwood_et_al": "tomato_ils",
        "ILs_Root_Tip_Brady_Lab": "tomato_ils2",
        "M82_S_pennellii_Atlases_Koenig_et_al": "tomato_s_pennellii",
        "Rose_Lab_Atlas": "tomato",
        "Rose_Lab_Atlas_Renormalized": "tomato_renormalized",
        "SEED_Lab_Angers": "tomato_seed",
        "Shade_Mutants": "tomato_shade_mutants",
        "Shade_Timecourse_WT": "tomato_shade_timecourse",
        "Tomato_Meristem": "tomato_meristem"
    },
    "triticale": {
        "triticale": "triticale",
        "triticale_mas": "triticale_mas"
    },
    "wheat": {
        "Developmental_Atlas": "wheat",
        "Wheat_Abiotic_Stress": "wheat_abiotic_stress",
        "Wheat_Embryogenesis": "wheat_embryogenesis",
        "Wheat_Meiosis": "wheat_meiosis"
    }
}


def fetch_view_data(xml_url, db_name, view_name):
    """Fetch a view's XML and parse groups, controls, and treatments.

    :param xml_url: Full URL to the view's XML file.
    :type xml_url: str
    :param db_name: Database name associated with this view.
    :type db_name: str
    :param view_name: Display name of the view (e.g. ``'Bud_Development'``).
    :type view_name: str
    :returns: Dict with keys ``database``, ``view_name``, and ``groups``.
    :rtype: dict
    """
    groups = {}
    try:
        resp = requests.get(xml_url, timeout=15)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)

        for group in root.findall(".//group"):
            group_name = group.get("name")
            if not group_name:
                continue

            controls = [
                c.get("sample")
                for c in group.findall("control")
                if c.get("sample")
            ]

            treatments = {}
            for tissue in group.findall("tissue"):
                t_name = tissue.get("name")
                if not t_name:
                    continue
                t_key = t_name.replace(" ", "_")

                samples = [
                    s.get("name")
                    for s in tissue.findall("sample")
                    if s.get("name")
                ]

                treatments.setdefault(t_key, [])
                treatments[t_key].extend(samples)

            groups[group_name.replace(" ", "_")] = {
                "controls": controls,
                "treatments": treatments
            }

    except Exception as e:
        print(f"  Error parsing {xml_url}: {e}")

    return {
        "database": db_name,
        "view_name": view_name,
        "groups": groups
    }


def main():
    """Iterate over all species and views, fetch XML data, and write output."""
    all_species_data = {}

    for species, views in species_databases.items():
        print(f"Processing {species}...")
        efp_url = EFP_SITES.get(species)
        if not efp_url:
            print(f"  No efp url for {species}")
            continue

        base_url = efp_url.rsplit("/", 2)[0]

        species_views = {}
        for view_name, db_name in views.items():
            xml_url = f"{base_url}/data/{view_name}.xml"
            print(f"  Fetching {xml_url}...")
            view_data = fetch_view_data(xml_url, db_name, view_name)
            species_views[view_name] = view_data

        all_species_data[species] = {
            "wasSuccessful": True,
            "data": {
                "species": species,
                "views": species_views
            }
        }

    out_file = "efp_species_view_info.json"
    with open(out_file, "w") as f:
        json.dump(all_species_data, f, indent=2)

    print(f"\nOutput written to {out_file}")


if __name__ == "__main__":
    main()
