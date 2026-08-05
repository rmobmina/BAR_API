import json
import re
import redis
import os
from functools import lru_cache
from pathlib import Path

_COMBINED_MASTER_PATH = Path(__file__).resolve().parents[2] / "data" / "efp_info" / "combined_master.json"


@lru_cache(maxsize=1)
def load_combined_master() -> dict:
    """Load data/efp_info/combined_master.json (species, databases, views, and
    validation_patterns), cached after first read.
    """
    with open(_COMBINED_MASTER_PATH) as f:
        return json.load(f)


# Per-eFP-project input validation regexes. Sourced from Vincent's
# regex_master_list_efp_eplant registry (tested at 99%+ coverage against real
# probeset/gene ID sample data) and embedded into combined_master.json at
# build time by build_combined_master_json.py -- see get_validation_patterns().
# Each pattern covers canonical gene IDs AND (where applicable) microarray
# probeset IDs. Copied (not aliased) so the aliases added below don't mutate
# the shared cached master JSON other modules also read.
EFP_PROJECT_REGEXES: dict = dict(load_combined_master()["validation_patterns"])

# Aliases for alternate eFP project key spellings used by the BAR (not present
# in Vincent's registry, which is keyed by canonical eFP project name only).
_PROJECT_ALIASES = {
    "efpbarley": "efp_barley",
    "efprice": "efp_rice",
    "efpmedicago": "efp_medicago",
    "efppop": "efp_poplar",
    "efpsoybean": "efp_soybean",
    "maizeefp": "efp_maize",
}
for _alias, _canonical in _PROJECT_ALIASES.items():
    EFP_PROJECT_REGEXES[_alias] = EFP_PROJECT_REGEXES[_canonical]

# General injection guard, run before any per-project/probeset format check.
# A handful of eFP projects accept loose freeform text (metabolite/enzyme/trait
# names, e.g. "TG 54:5; 16:0_20:1_18:4" or "efpconfig"'s near-unrestricted
# `.{0,16}`), so this can't blacklist individual characters like ';' or "'" --
# those are legitimate in real sample data. Instead it looks for actual attack
# syntax: SQL comment/statement-chaining sequences, tautologies, UNION SELECT,
# script tags, and null bytes.
_INJECTION_RE = re.compile(
    r"(--)"
    r"|(/\*)|(\*/)"
    r"|(;\s*(drop|delete|update|insert|alter|exec|union|select)\b)"
    r"|(\bunion\b\s+\bselect\b)"
    r"|(\bor\b\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+)"
    r"|(<\s*script\b)"
    r"|(javascript\s*:)"
    r"|(\bxp_cmdshell\b)"
    r"|(\x00)",
    re.IGNORECASE,
)


class BARUtils:
    @staticmethod
    def error_exit(msg):
        """Exit if failed
        :param msg: message to pass on failure
        :return:
        """
        result = {"wasSuccessful": False, "error": msg}
        return result

    @staticmethod
    def success_exit(msg):
        """Output if success
        :param msg: the actual data the needs to be output
        :return:
        """
        result = {"wasSuccessful": True, "data": msg}
        return result

    @staticmethod
    def is_arabidopsis_gene_valid(gene):
        """Validates arabidopsis gene IDs against Vincent's tested efp_arabidopsis registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_arabidopsis")

    @staticmethod
    def normalize_arabidopsis_gene(gene):
        """Return Arabidopsis gene in canonical case (At1g01010)."""
        if not gene:
            return gene
        lowered = gene.lower()
        if re.search(r"^at[12345cm]g\d{5}.?\d?$", lowered):
            return "At" + lowered[2:]
        return gene

    @staticmethod
    def is_actinidia_gene_valid(gene):
        """Validates actinidia gene IDs against Vincent's tested efp_actinidia registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_actinidia")

    @staticmethod
    def is_apple_gene_valid(gene):
        """Validates apple gene IDs against Vincent's tested efp_apple registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_apple")

    @staticmethod
    def is_barley_gene_valid(gene):
        """Validates barley gene IDs against Vincent's tested efp_barley registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_barley")

    @staticmethod
    def is_brachypodium_gene_valid(gene):
        """Validates brachypodium gene IDs against Vincent's tested efp_brachypodium registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_brachypodium")

    @staticmethod
    def is_cacao_gene_valid(gene):
        """Validates cacao gene IDs against Vincent's tested registry patterns.

        Cacao is split across three eFP projects (CCN-51, SCA-6, and Tc-prefixed
        lines), each with its own pattern, so this checks all three.
        """
        return any(
            BARUtils.is_efp_gene_valid(gene, project)
            for project in ("efp_cacao_ccn", "efp_cacao_sca", "efp_cacao_tc")
        )

    @staticmethod
    def is_camelina_gene_valid(gene):
        """Validates camelina gene IDs against Vincent's tested efp_camelina registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_camelina")

    @staticmethod
    def is_cassava_gene_valid(gene):
        """Validates cassava gene IDs: Manes.01G040000.v8.1"""
        # No matching project in Vincent's regex registry -- hand-maintained.
        return bool(gene and re.search(r"^Manes\.\d{2}G\d+\.v\d+\.\d+$", gene, re.I))

    @staticmethod
    def is_cuscuta_gene_valid(gene):
        """Validates Cuscuta gene IDs: Cc000663.t1 or Cc000082"""
        # No matching project in Vincent's regex registry -- hand-maintained.
        return bool(gene and re.search(r"^Cc\d+(\.t\d+)?$", gene, re.I))

    @staticmethod
    def is_eucalyptus_gene_valid(gene):
        """Validates eucalyptus gene IDs against Vincent's tested efp_eucalyptus registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_eucalyptus")

    @staticmethod
    def is_euphorbia_gene_valid(gene):
        """Validates euphorbia gene IDs against Vincent's tested efp_euphorbia registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_euphorbia")

    @staticmethod
    def is_grape_gene_valid(gene):
        """Validates grape gene IDs against Vincent's tested efp_grape registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_grape")

    @staticmethod
    def is_poplar_gene_valid(gene):
        """Validates poplar gene IDs against Vincent's tested efp_poplar registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_poplar")

    @staticmethod
    def is_rice_gene_valid(gene, isoform_id=False):
        """Validates rice gene IDs against Vincent's tested efp_rice registry pattern.

        isoform_id is kept for call-site compatibility but is no longer used:
        efp_rice has no isoform-suffix variant for the LOC_Os form (e.g.
        LOC_Os01g01430.1), so isoform-suffixed IDs -- previously accepted when
        isoform_id=True -- are now rejected. Accepted trade-off for having one
        tested source of truth instead of a separately hand-maintained regex.
        """
        return BARUtils.is_efp_gene_valid(gene, "efp_rice")

    @staticmethod
    def is_spruce_gene_valid(gene):
        """Validates spruce clone IDs from either of two cDNA libraries:
        GQ0031_G08.1 or WS0321_C07.1 / WS03217_B11.1"""
        # No matching project in Vincent's regex registry -- hand-maintained.
        return bool(gene and re.search(r"^(GQ|WS)\d{4,5}_[A-Z]\d{2}\.\d+$", gene))

    @staticmethod
    def is_sugarcane_gene_valid(gene):
        """Validates sugarcane gene IDs against Vincent's tested efp_sugarcane registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_sugarcane")

    @staticmethod
    def is_sunflower_gene_valid(gene):
        """Validates sunflower gene IDs against Vincent's tested efp_sunflower registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_sunflower")

    @staticmethod
    def is_tung_tree_gene_valid(gene):
        """Validates tung_tree gene IDs against Vincent's tested efp_tung_tree registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_tung_tree")

    @staticmethod
    def is_wheat_gene_valid(gene):
        """Validates wheat gene IDs against Vincent's tested efp_wheat registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_wheat")

    @staticmethod
    def is_willow_gene_valid(gene):
        """Validates willow Trinity gene IDs: comp170315_c0_seq1"""
        # No matching project in Vincent's regex registry -- hand-maintained.
        return bool(gene and re.search(r"^comp\d+_c\d+_seq\d+$", gene, re.I))

    @staticmethod
    def is_thellungiella_gene_valid(gene):
        """Validates thellungiella gene IDs against Vincent's tested efp_eutrema registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_eutrema")

    @staticmethod
    def is_tomato_gene_valid(gene, isoform_id=False):
        """Validates tomato gene IDs against Vincent's tested efp_tomato registry pattern.

        isoform_id is kept for call-site compatibility but no longer narrows the
        check -- efp_tomato's pattern already accepts both isoform and bare forms.
        """
        return BARUtils.is_efp_gene_valid(gene, "efp_tomato")

    @staticmethod
    def is_cannabis_gene_valid(gene):
        """Validates cannabis gene IDs against Vincent's tested efp_cannabis registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_cannabis")

    @staticmethod
    def is_canola_gene_valid(gene):
        """Validates canola gene IDs against Vincent's tested efp_canola registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_canola")

    @staticmethod
    def is_arachis_gene_valid(gene):
        """Validates arachis gene IDs against Vincent's tested efp_arachis registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_arachis")

    @staticmethod
    def is_brassica_rapa_gene_valid(gene):
        """Validates brassica_rapa gene IDs against Vincent's tested efp_brassica_rapa registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_brassica_rapa")

    @staticmethod
    def is_human_gene_valid(gene):
        """Validates human gene IDs against Vincent's tested efp_human registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_human")

    @staticmethod
    def is_little_millet_gene_valid(gene):
        """Validates little_millet gene IDs against Vincent's tested efp_little_millet registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_little_millet")

    @staticmethod
    def is_lupin_gene_valid(gene):
        """Validates lupin gene IDs against Vincent's tested efp_lupin registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_lupin")

    @staticmethod
    def is_mangosteen_gene_valid(gene):
        """Validates mangosteen gene IDs against Vincent's tested efp_mangosteen registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_mangosteen")

    @staticmethod
    def is_marchantia_gene_valid(gene):
        """Validates marchantia gene IDs against Vincent's tested efp_marchantia registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_marchantia")

    @staticmethod
    def is_medicago_gene_valid(gene):
        """Validates medicago gene IDs against Vincent's tested efp_medicago registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_medicago")

    @staticmethod
    def is_mouse_gene_valid(gene):
        """Validates mouse gene IDs against Vincent's tested mouse_efp registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "mouse_efp")

    @staticmethod
    def is_oat_gene_valid(gene):
        """Validates oat gene IDs against Vincent's tested efp_oat registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_oat")

    @staticmethod
    def is_potato_gene_valid(gene):
        """Validates potato gene IDs against Vincent's tested efp_potato registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_potato")

    @staticmethod
    def is_quinoa_gene_valid(gene):
        """Validates quinoa gene IDs: CquiG00000000055"""
        # No matching project in Vincent's regex registry -- hand-maintained.
        return bool(gene and re.search(r"^CquiG\d+$", gene, re.I))

    @staticmethod
    def is_soybean_gene_valid(gene):
        """Validates soybean gene IDs against Vincent's tested efp_soybean registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_soybean")

    @staticmethod
    def is_maize_gene_valid(gene):
        """Validates maize gene IDs against Vincent's tested efp_maize registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_maize")

    @staticmethod
    def is_sorghum_gene_valid(gene):
        """Validates sorghum gene IDs against Vincent's tested efp_sorghum registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_sorghum")

    @staticmethod
    def is_kalanchoe_gene_valid(gene):
        """Validates kalanchoe gene IDs against Vincent's tested efp_kalanchoe registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_kalanchoe")

    @staticmethod
    def is_phelipanche_gene_valid(gene):
        """Validates phelipanche gene IDs against Vincent's tested efp_phelipanche registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_phelipanche")

    @staticmethod
    def is_physcomitrella_gene_valid(gene):
        """Validates physcomitrella gene IDs against Vincent's tested efp_physcomitrella registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_physcomitrella")

    @staticmethod
    def is_selaginella_gene_valid(gene):
        """Validates selaginella gene IDs against Vincent's tested efp_selaginella registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_selaginella")

    @staticmethod
    def is_strawberry_gene_valid(gene):
        """Validates strawberry gene IDs against Vincent's tested efp_strawberry registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_strawberry")

    @staticmethod
    def is_striga_gene_valid(gene):
        """Validates striga gene IDs against Vincent's tested efp_striga registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_striga")

    @staticmethod
    def is_triphysaria_gene_valid(gene):
        """Validates triphysaria gene IDs against Vincent's tested efp_triphysaria registry pattern."""
        return BARUtils.is_efp_gene_valid(gene, "efp_triphysaria")

    @staticmethod
    def is_integer(data):
        """Check if the input is at max ten figure number.
        :param data: int number
        :return: True if a number
        """
        if re.search(r"^\d{1,10}$", data):
            return True
        else:
            return False

    @staticmethod
    def is_gaia_alias(data):
        """Check if the input is a valid gaia alias.
        :param data
        :return: True if valid gaia alias
        """
        if re.search(r"^[a-z0-9_]{1,50}$", data, re.I):
            return True
        else:
            return False

    @staticmethod
    def format_poplar(poplar_gene):
        """Format Poplar gene ID to be Potri.016G107900, i.e. capitalized P and G
        :param poplar_gene: gene id
        :return: String
        """
        return poplar_gene.translate(str.maketrans("pOTRIg", "PotriG"))

    @staticmethod
    def is_injection_attempt(data: str) -> bool:
        """Flag obvious SQL/script injection payloads.

        Meant to run before any format-specific check (probeset-shape check,
        per-project regex, species validator) since some of those are
        deliberately permissive -- e.g. efpconfig's near-unrestricted
        `.{0,16}` or the metabolite/lipid projects' freeform text patterns --
        and would otherwise let attack syntax through unexamined.

        :param data: Raw input string to inspect
        :return: True if the input looks like an injection attempt
        """
        return bool(_INJECTION_RE.search(data))

    @staticmethod
    def is_efp_gene_valid(gene: str, efp_project: str) -> bool:
        """Validate a gene ID against the named eFP project's input regex.

        Accepts both canonical gene IDs (e.g. AT1G01010 for Arabidopsis) and
        microarray probeset IDs (e.g. 267643_at, Contig7905_at) depending on the
        project. Returns False if the eFP project name is unknown.

        :param gene: Gene identifier to validate
        :param efp_project: eFP project key (e.g. 'efp_arabidopsis', 'efpbarley')
        :return: True if the gene ID matches the project's accepted format
        """
        if not gene:
            return False
        if BARUtils.is_injection_attempt(gene):
            return False
        pattern = EFP_PROJECT_REGEXES.get(efp_project)
        if not pattern:
            return False
        return bool(re.search(pattern, gene, re.I))

    @staticmethod
    def connect_redis():
        """This function connects to redis
        :returns: redis connection
        """
        if os.environ.get("BAR"):
            r = redis.Redis(
                host=os.environ.get("BAR_REDIS_HOST"), port=6379, password=os.environ.get("BAR_REDIS_PASSWORD")
            )
        else:
            r = redis.Redis(host="localhost")

        return r
