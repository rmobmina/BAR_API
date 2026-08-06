from __future__ import annotations

import re

from api.utils.bar_utils import BARUtils, load_combined_master


def _load_database_regex_projects() -> dict[str, str]:
    databases = load_combined_master()["databases"]
    return {
        db: info["gene_id_pattern"] for db, info in databases.items() if info.get("gene_id_pattern")
    }


def _load_database_species() -> dict[str, str]:
    databases = load_combined_master()["databases"]
    return {db: info["species"] for db, info in databases.items() if info.get("species")}


# Per-database species and gene ID pattern, sourced from combined_master.json.
DATABASE_SPECIES: dict[str, str] = _load_database_species()
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
    def validate_gene_id(gene_id: str, species: str) -> bool:
        validator = _VALIDATORS.get(species)
        return validator(gene_id) if validator is not None else True

    @staticmethod
    def validate_gene_for_database(gene_id: str, database: str) -> bool:
        """Validate a gene ID (or probeset) against the pattern configured for a database."""
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
