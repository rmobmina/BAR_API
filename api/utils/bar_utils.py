import json
import re
import redis
import os
from functools import lru_cache
from pathlib import Path

_COMBINED_MASTER_PATH = Path(__file__).resolve().parents[2] / "data" / "efp_info" / "combined_master.json"


@lru_cache(maxsize=1)
def load_combined_master() -> dict:
    """Load data/efp_info/combined_master.json, cached after first read."""
    with open(_COMBINED_MASTER_PATH) as f:
        return json.load(f)


# regexes keyed by both bare species name ("arabidopsis") and "efp_"-prefixed name
_GENE_ID_PATTERNS = load_combined_master()["gene_id_patterns"]
EFP_PROJECT_REGEXES: dict = {
    **_GENE_ID_PATTERNS,
    **{f"efp_{name}": pattern for name, pattern in _GENE_ID_PATTERNS.items()},
}

# catches SQL comment/chaining, tautologies, UNION SELECT, script tags, null bytes -- not a per-char blacklist since some eFP projects accept freeform text
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
    def normalize_arabidopsis_gene(gene):
        """Return Arabidopsis gene in canonical case (At1g01010)."""
        if not gene:
            return gene
        lowered = gene.lower()
        if re.search(r"^at[12345cm]g\d{5}.?\d?$", lowered):
            return "At" + lowered[2:]
        return gene

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
        """Flag obvious SQL/script injection payloads, run before any format-specific check since some of those are permissive by design."""
        return bool(_INJECTION_RE.search(data))

    @staticmethod
    def is_efp_gene_valid(gene: str, efp_project: str) -> bool:
        """Validate a gene ID or probeset ID against the named eFP project's input regex."""
        if not gene:
            return False
        if BARUtils.is_injection_attempt(gene):
            return False
        pattern = EFP_PROJECT_REGEXES.get(efp_project)
        if not pattern:
            return False
        return bool(re.fullmatch(pattern, gene, re.I))

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
