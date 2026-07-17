import json
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
