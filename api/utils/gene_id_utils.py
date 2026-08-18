from __future__ import annotations

import re

from api.utils.bar_utils import EFP_PROJECT_REGEXES, BARUtils, load_combined_master


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

# Species names whose combined_master.json gene_id_patterns key doesn't match
# the species name itself. Every other species falls back to f"efp_{species}".
_SPECIES_EFP_PROJECT_OVERRIDES: dict[str, str] = {
    "brassica": "efp_brassica_rapa",
    "thellungiella": "efp_eutrema",
}

_BARLEY_V3_RE = re.compile(r"\.[Vv]\d+$")


class GeneIdUtils:
    @staticmethod
    def validate_gene_id(gene_id: str, species: str) -> bool:
        """Validate a gene ID against its species' pattern; species with no known pattern pass through as valid."""
        efp_project = _SPECIES_EFP_PROJECT_OVERRIDES.get(species, f"efp_{species}")
        if efp_project not in EFP_PROJECT_REGEXES:
            return True
        return BARUtils.is_efp_gene_valid(gene_id, efp_project)

    @staticmethod
    def validate_gene_for_database(gene_id: str, database: str) -> bool:
        """Validate a gene ID (or probeset) against the pattern configured for a database."""
        if BARUtils.is_injection_attempt(gene_id):
            return False
        efp_project = DATABASE_EFP_PROJECT.get(database)
        if efp_project:
            return BARUtils.is_efp_gene_valid(gene_id, f"efp_{efp_project}")
        species = DATABASE_SPECIES.get(database)
        return GeneIdUtils.validate_gene_id(gene_id, species) if species else True

    @staticmethod
    def normalize_gene_id(gene_id: str, species: str) -> str:
        if species == "barley" and _BARLEY_V3_RE.search(gene_id):
            return _BARLEY_V3_RE.sub(".1", gene_id)
        return gene_id
