from __future__ import annotations

import re

from api.utils.bar_utils import BARUtils
from api.utils.master_data_utils import load_combined_master


def _load_database_regex_projects() -> dict[str, str]:
    databases = load_combined_master()["databases"]
    return {
        db: info["regex_project"] for db, info in databases.items() if info.get("regex_project")
    }


_PROBESET_RE = re.compile(r"^.+_at$", re.IGNORECASE)
_AROS_PROBESET_RE = re.compile(r"^A\d{6}_\d{2}$", re.IGNORECASE)
# CATMA microarray probes used by the Seedcoat database (e.g. At30023977)
_CATMA_PROBE_RE = re.compile(r"^At\d{8}$")

# fmt: off
DATABASE_SPECIES: dict[str, str] = {
    "affydb":                               "arabidopsis",
    "arabidopsis_ecotypes":                 "arabidopsis",
    "atgenexp":                             "arabidopsis",
    "atgenexp_hormone":                     "arabidopsis",
    "atgenexp_pathogen":                    "arabidopsis",
    "atgenexp_plus":                        "arabidopsis",
    "atgenexp_stress":                      "arabidopsis",
    "circadian_mutants":                    "arabidopsis",
    "dna_damage":                           "arabidopsis",
    "embryo":                               "arabidopsis",
    "gc_drought":                           "arabidopsis",
    "germination":                          "arabidopsis",
    "guard_cell":                           "arabidopsis",
    "gynoecium":                            "arabidopsis",
    "hnahal":                               "arabidopsis",
    "klepikova":                            "arabidopsis",
    "lateral_root_initiation":              "arabidopsis",
    "light_series":                         "arabidopsis",
    "lipid_map":                            "arabidopsis",
    "meristem_db":                          "arabidopsis",
    "meristem_db_new":                      "arabidopsis",
    "rohan":                                "arabidopsis",
    "root":                                 "arabidopsis",
    "root_Schaefer_lab":                    "arabidopsis",
    "rpatel":                               "arabidopsis",
    "seed_db":                              "arabidopsis",
    "seedcoat":                             "arabidopsis",
    "shoot_apex":                           "arabidopsis",
    "silique":                              "arabidopsis",
    "single_cell":                          "arabidopsis",
    "actinidia_bud_development":            "actinidia",
    "actinidia_flower_fruit_development":   "actinidia",
    "actinidia_postharvest":                "actinidia",
    "actinidia_vegetative_growth":          "actinidia",
    "apple":                                "apple",
    "arachis":                              "arachis",
    "barley_mas":                           "barley",
    "barley_rma":                           "barley",
    "barley_seed":                          "barley",
    "barley_spike_meristem":                "barley",
    "barley_spike_meristem_v3":             "barley",
    "brachypodium":                         "brachypodium",
    "brachypodium_Bd21":                    "brachypodium",
    "brachypodium_embryogenesis":           "brachypodium",
    "brachypodium_grains":                  "brachypodium",
    "brachypodium_metabolites_map":         "brachypodium",
    "brachypodium_photo_thermocycle":       "brachypodium",
    "brassica_rapa":                        "brassica",
    "brassica_rapa_developmental_atlas":    "brassica",
    "cacao_developmental_atlas":            "cacao",
    "cacao_developmental_atlas_sca":        "cacao",
    "cacao_drought_diurnal_atlas":          "cacao",
    "cacao_drought_diurnal_atlas_sca":      "cacao",
    "cacao_infection":                      "cacao",
    "cacao_leaf":                           "cacao",
    "cacao_meristem_atlas_sca":             "cacao",
    "cacao_seed_atlas_sca":                 "cacao",
    "camelina":                             "camelina",
    "camelina_tpm":                         "camelina",
    "cannabis":                             "cannabis",
    "canola":                               "canola",
    "canola_original":                      "canola",
    "canola_original_v2":                   "canola",
    "canola_seed":                          "canola",
    "cassava_atlas":                        "cassava",
    "cassava_cbb":                          "cassava",
    "cassava_eacmv":                        "cassava",
    "cuscuta":                              "cuscuta",
    "cuscuta_early_haustoriogenesis":       "cuscuta",
    "cuscuta_lmd":                          "cuscuta",
    "durum_wheat_abiotic_stress":           "wheat",
    "durum_wheat_biotic_stress":            "wheat",
    "durum_wheat_development":              "wheat",
    "eucalyptus":                           "eucalyptus",
    "euphorbia":                            "euphorbia",
    "grape_developmental":                  "grape",
    "heterodera_schachtii":                 "arabidopsis",
    "human_body_map_2":                     "human",
    "human_developmental":                  "human",
    "human_developmental_SpongeLab":        "human",
    "human_diseased":                       "human",
    "kalanchoe":                            "kalanchoe",
    "kalanchoe_time_course_analysis":       "kalanchoe",
    "little_millet":                        "little_millet",
    "lupin_lcm_leaf":                       "lupin",
    "lupin_lcm_pod":                        "lupin",
    "lupin_lcm_stem":                       "lupin",
    "lupin_pod_seed":                       "lupin",
    "lupin_whole_plant":                    "lupin",
    "maize_RMA_linear":                     "maize",
    "maize_RMA_log":                        "maize",
    "maize_atlas":                          "maize",
    "maize_atlas_v5":                       "maize",
    "maize_buell_lab":                      "maize",
    "maize_early_seed":                     "maize",
    "maize_ears":                           "maize",
    "maize_embryonic_leaf_development":     "maize",
    "maize_enzyme":                         "maize",
    "maize_gdowns":                         "maize",
    "maize_iplant":                         "maize",
    "maize_kernel_v5":                      "maize",
    "maize_leaf_gradient":                  "maize",
    "maize_lipid_map":                      "maize",
    "maize_metabolite":                     "maize",
    "maize_nitrogen_use_efficiency":        "maize",
    "maize_rice_comparison":                "maize",
    "maize_root":                           "maize",
    "maize_stress_v5":                      "maize",
    "mangosteen_aril_vs_rind":              "mangosteen",
    "mangosteen_callus":                    "mangosteen",
    "mangosteen_diseased_vs_normal":        "mangosteen",
    "mangosteen_fruit_ripening":            "mangosteen",
    "mangosteen_seed_development":          "mangosteen",
    "mangosteen_seed_development_germination": "mangosteen",
    "mangosteen_seed_germination":          "mangosteen",
    "marchantia_organ_stress":              "marchantia",
    "medicago_mas":                         "medicago",
    "medicago_rma":                         "medicago",
    "medicago_root":                        "medicago",
    "medicago_root_v5":                     "medicago",
    "medicago_seed":                        "medicago",
    "mouse_db":                             "mouse",
    "oat":                                  "oat",
    "phelipanche":                          "phelipanche",
    "physcomitrella_db":                    "physcomitrella",
    "poplar":                               "poplar",
    "poplar_hormone":                       "poplar",
    "poplar_leaf":                          "poplar",
    "poplar_xylem":                         "poplar",
    "potato_dev":                           "potato",
    "potato_stress":                        "potato",
    "potato_wounding":                      "potato",
    "quinoa_nutrient":                      "quinoa",
    "rice_abiotic_stress_sc_pseudobulk":    "rice",
    "rice_drought_heat_stress":             "rice",
    "rice_leaf_gradient":                   "rice",
    "rice_maize_comparison":                "rice",
    "rice_mas":                             "rice",
    "rice_metabolite":                      "rice",
    "rice_rma":                             "rice",
    "rice_root":                            "rice",
    "selaginella":                          "selaginella",
    "sorghum_atlas_w_BS_cells":             "sorghum",
    "sorghum_comparative_transcriptomics":  "sorghum",
    "sorghum_developmental":                "sorghum",
    "sorghum_developmental_2":              "sorghum",
    "sorghum_flowering_activation":         "sorghum",
    "sorghum_low_phosphorus":               "sorghum",
    "sorghum_nitrogen_stress":              "sorghum",
    "sorghum_nitrogen_use_efficiency":      "sorghum",
    "sorghum_phosphate_stress":             "sorghum",
    "sorghum_plasma":                       "sorghum",
    "sorghum_saline_alkali_stress":         "sorghum",
    "sorghum_stress":                       "sorghum",
    "sorghum_strigolactone_variation":      "sorghum",
    "sorghum_sulfur_stress":                "sorghum",
    "sorghum_temperature_stress":           "sorghum",
    "sorghum_vascularization_and_internode": "sorghum",
    "soybean":                              "soybean",
    "soybean_embryonic_development":        "soybean",
    "soybean_heart_cotyledon_globular":     "soybean",
    "soybean_senescence":                   "soybean",
    "soybean_severin":                      "soybean",
    "spruce":                               "spruce",
    "strawberry":                           "strawberry",
    "striga":                               "striga",
    "sugarcane_culms":                      "sugarcane",
    "sugarcane_leaf":                       "sugarcane",
    "sunflower":                            "sunflower",
    "thellungiella_db":                     "thellungiella",
    "tomato":                               "tomato",
    "tomato_ils":                           "tomato",
    "tomato_ils2":                          "tomato",
    "tomato_ils3":                          "tomato",
    "tomato_meristem":                      "tomato",
    "tomato_renormalized":                  "tomato",
    "tomato_root":                          "tomato",
    "tomato_root_field_pot":                "tomato",
    "tomato_s_pennellii":                   "tomato",
    "tomato_seed":                          "tomato",
    "tomato_shade_mutants":                 "tomato",
    "tomato_shade_timecourse":              "tomato",
    "tomato_trait":                         "tomato",
    "triphysaria":                          "triphysaria",
    "triticale":                            "triticale",
    "triticale_mas":                        "triticale",
    "tung_tree":                            "tung_tree",
    "wheat":                                "wheat",
    "wheat_abiotic_stress":                 "wheat",
    "wheat_embryogenesis":                  "wheat",
    "wheat_meiosis":                        "wheat",
    "wheat_root":                           "wheat",
    "willow":                               "willow",
    "sample_data":                          "arabidopsis",
}

# Maps databases that store microarray probeset IDs (or, for a handful of
# metabolite/enzyme/trait eFPs, freeform category names) to their eFP project
# regex key. Sourced from Vincent's regex_master_list_efp_eplant registry via
# combined_master.json's per-database "regex_project" field, which is itself
# empirically verified against real sample data at build time (see
# verify_regex_projects() in build_combined_master_json.py) -- databases whose
# assigned project doesn't actually validate most of their own real IDs are
# left out here and fall back to species-based validation below instead.
DATABASE_EFP_PROJECT: dict[str, str] = _load_database_regex_projects()


_VALIDATORS: dict = {
    "actinidia":     BARUtils.is_actinidia_gene_valid,
    "apple":         BARUtils.is_apple_gene_valid,
    "arabidopsis":   BARUtils.is_arabidopsis_gene_valid,
    "arachis":       BARUtils.is_arachis_gene_valid,
    "barley":        BARUtils.is_barley_gene_valid,
    "brachypodium":  BARUtils.is_brachypodium_gene_valid,
    "brassica":      BARUtils.is_brassica_rapa_gene_valid,
    "cacao":         BARUtils.is_cacao_gene_valid,
    "camelina":      BARUtils.is_camelina_gene_valid,
    "cannabis":      BARUtils.is_cannabis_gene_valid,
    "canola":        BARUtils.is_canola_gene_valid,
    "cassava":       BARUtils.is_cassava_gene_valid,
    "cuscuta":       BARUtils.is_cuscuta_gene_valid,
    "eucalyptus":    BARUtils.is_eucalyptus_gene_valid,
    "euphorbia":     BARUtils.is_euphorbia_gene_valid,
    "grape":         BARUtils.is_grape_gene_valid,
    "human":         BARUtils.is_human_gene_valid,
    "kalanchoe":     BARUtils.is_kalanchoe_gene_valid,
    "little_millet": BARUtils.is_little_millet_gene_valid,
    "lupin":         BARUtils.is_lupin_gene_valid,
    "maize":         BARUtils.is_maize_gene_valid,
    "mangosteen":    BARUtils.is_mangosteen_gene_valid,
    "marchantia":    BARUtils.is_marchantia_gene_valid,
    "medicago":      BARUtils.is_medicago_gene_valid,
    "mouse":         BARUtils.is_mouse_gene_valid,
    "oat":           BARUtils.is_oat_gene_valid,
    "phelipanche":   BARUtils.is_phelipanche_gene_valid,
    "physcomitrella": BARUtils.is_physcomitrella_gene_valid,
    "poplar":        BARUtils.is_poplar_gene_valid,
    "potato":        BARUtils.is_potato_gene_valid,
    "quinoa":        BARUtils.is_quinoa_gene_valid,
    "rice":          BARUtils.is_rice_gene_valid,
    "selaginella":   BARUtils.is_selaginella_gene_valid,
    "sorghum":       BARUtils.is_sorghum_gene_valid,
    "soybean":       BARUtils.is_soybean_gene_valid,
    "spruce":        BARUtils.is_spruce_gene_valid,
    "strawberry":    BARUtils.is_strawberry_gene_valid,
    "striga":        BARUtils.is_striga_gene_valid,
    "sugarcane":     BARUtils.is_sugarcane_gene_valid,
    "sunflower":     BARUtils.is_sunflower_gene_valid,
    "thellungiella": BARUtils.is_thellungiella_gene_valid,
    "tomato":        BARUtils.is_tomato_gene_valid,
    "triphysaria":   BARUtils.is_triphysaria_gene_valid,
    "tung_tree":     BARUtils.is_tung_tree_gene_valid,
    "wheat":         BARUtils.is_wheat_gene_valid,
    "willow":        BARUtils.is_willow_gene_valid,
}

_BARLEY_V3_RE = re.compile(r"\.[Vv]\d+$")


class GeneIdUtils:
    @staticmethod
    def is_probeset_id(gene_id: str) -> bool:
        """Return True if the gene_id looks like a microarray probeset rather than a gene ID.

        Covers:
        - Standard Affymetrix probes ending in _at (e.g. 267643_at, Contig7905_at)
        - AROS array probes (e.g. A017813_01)
        - CATMA array probes used by the Seedcoat database (e.g. At30023977)
        """
        return bool(
            _PROBESET_RE.match(gene_id)
            or _AROS_PROBESET_RE.match(gene_id)
            or _CATMA_PROBE_RE.match(gene_id)
        )

    @staticmethod
    def validate_gene_id(gene_id: str, species: str) -> bool:
        validator = _VALIDATORS.get(species)
        return validator(gene_id) if validator is not None else True

    @staticmethod
    def validate_gene_for_database(gene_id: str, database: str) -> bool:
        """Validate a gene ID against the rules for a specific database.

        For microarray databases, uses the eFP project regex which accepts both
        canonical gene IDs and probeset IDs. Falls back to species-based validation
        for all other databases.

        :param gene_id: Gene identifier to validate
        :param database: Database name (e.g. 'light_series', 'barley_mas')
        :return: True if the gene ID is valid for the given database
        """
        if BARUtils.is_injection_attempt(gene_id):
            return False
        efp_project = DATABASE_EFP_PROJECT.get(database)
        if efp_project:
            return BARUtils.is_efp_gene_valid(gene_id, efp_project)
        species = DATABASE_SPECIES.get(database)
        return GeneIdUtils.validate_gene_id(gene_id, species) if species else True

    @staticmethod
    def normalize_gene_id(gene_id: str, species: str) -> str:
        if species == "barley" and _BARLEY_V3_RE.search(gene_id):
            return _BARLEY_V3_RE.sub(".1", gene_id)
        return gene_id
