"""
Reena Obmina | BCB330 Project 2025-2026 | University of Toronto

Generates edge-test CSV for the eFP gene expression endpoints.

Reads:  species_databases.json   — view→database mappings per species
        api/random_rows_json/    — example gene IDs per database
        api/utils/bar_utils.py   — regex patterns (referenced, not imported)
Writes: efp_test_cases.csv

Columns: species, view, database, regex, valid_gene_1..3,
         invalid_gene_1_wrong_initially, invalid_gene_2_wrong_finally,
         invalid_gene_3_other_species
"""

import csv
import json
import re
from pathlib import Path

JSON_DIR = Path("api/random_rows_json")

# ---------------------------------------------------------------------------
# Regex patterns copied verbatim from api/utils/bar_utils.py
# ---------------------------------------------------------------------------
SPECIES_REGEX = {
    "arabidopsis":          r"^At[12345cm]g\d{5}.?\d?$",
    "arabidopsis lipid":    r"^At[12345cm]g\d{5}.?\d?$",
    "arabidopsis cell":     r"^At[12345cm]g\d{5}.?\d?$",
    "arabidopsis seedcoat": r"^At[12345cm]g\d{5}.?\d?$",
    "actinidia":            r"^Acc\d{5}\.\d+$",
    "arachis":              r"^Adur\d{1,10}_comp\d{1,3}_\D{1,3}\d{1,3}_seq\d{1,5}$",
    "barley":               r"^HORVU(\d+Hr\d+G\d+|\.MOREX\.r\d+\.\dHG\d+\.\d+)$",
    "brachypodium":         r"^Bradi\d+g\d+\.\d+$",
    "brassica rapa":        r"^(BraA.{1,4}g\d{1,9}|[A-Z]\d{2}[gp]\d+\.\d+_BraROA)$",
    "cacao ccn":            r"^((CCN-51|SCA-6)_Chr\d+v\d+_\d+|Tc\d+v\d+_g\d+)$",
    "cacao sca":            r"^((CCN-51|SCA-6)_Chr\d+v\d+_\d+|Tc\d+v\d+_g\d+)$",
    "cacao tc":             r"^((CCN-51|SCA-6)_Chr\d+v\d+_\d+|Tc\d+v\d+_g\d+)$",
    "camelina":             r"^Csa\d+[gs]\d+\.\d+$",
    "canola":               r"^(Bna[AC]\d{2}g\d{5}[A-D]?|Bo[A-Z]+_?\d+g\d+\.\d+V\d+)$",
    "cannabis":             r"^AGQN\d{0,10}$",
    "eutrema":              r"^(Thhalv\d+m\.g|nXLOC_\d+)$",
    "grape":                r"^(CHR\d+_JGVV\d+_\d+_T\d+|VIT_\d{0,3}\D\d{0,5}g\d{0,6})$",
    "human":                r"^\d{1,10}$",
    "kalanchoe":            r"^Kaladp\d{1,10}s\d{1,10}$",
    "little millet":        r"^TRINITY_DN\d+_c\d+_g\d+_i\d+$",
    "lupin":                r"^Luan_Oskar_(PB\d+|Trin)_\d+$",
    "maize":                r"^(AC[0-9]{6}\.[0-9]+_FGT?[0-9]{3}|GRMZM[25]G[0-9]{6}(_T[0-9]{2})?|Zm\d+(d|eb)\d+)$",
    "mangosteen":           r"^DN\d+$",
    "medicago":             r"^(Medtr(\d+[gs]\d+|_v1_\d+)|MtrunA17Chr\dg\d+)$",
    "mouse":                r"^XM_\d+\.\d+$",
    "oat":                  r"^AV[A-Z]{3}\.\d{5}[a-z]\.r\d+\.\d[A-Z]{2}\d{8}$",
    "phelipanche":          r"^OrAeBC5_\d{1,6}\.\d{1,3}$",
    "physcomitrella":       r"^Pp1s\d{1,8}_\d{1,8}V6\.\d{1,3}$",
    "poplar":               r"^POTRI\.\d{3}g\d{6}.?\d{0,3}$",
    "potato":               r"^(PGSC0003DMG\d+|EPlSTUG\d+)$",
    "rice":                 r"^(LOC_Os\d{2}g\d{5}|Os\d{2}g\d+)$",
    "selaginella":          r"^Smo\d{1,8}$",
    "soybean":              r"^((Glyma\d{1,3}g\d{1,6}\.?\d?)|(Glyma\.\d{1,3}g\d{1,8}))$",
    "strawberry":           r"^FvH4_\d{1,3}g\d{1,8}$",
    "striga":               r"^StHeBC3_\d{1,6}\.\d{1,5}$",
    "tomato":               r"^Solyc\d\dg\d{6}(\.\d+)?$",
    # no dedicated bar_utils validator; triticale uses wheat probes/IDs
    "triticale":            r"^(TraesCS[0-9A-Z]+(\.\d+)?|TrturSVE[0-9A-Z]+G\d+)$",
    "triphysaria":          r"^TrVeBC3_\d{1,6}\.\d{1,3}$",
    "wheat":                r"^(TraesCS[0-9A-Z]+(\.\d+)?|TrturSVE[0-9A-Z]+G\d+)$",
}

# ---------------------------------------------------------------------------
# Microarray / probeset databases → gene IDs come from a non-probeset sibling
# ---------------------------------------------------------------------------
PROBESET_FALLBACK = {
    # Arabidopsis Affymetrix ATH1 arrays → use klepikova RNA-seq (AGI format)
    "affydb":                        "klepikova",
    "arabidopsis_ecotypes":          "klepikova",
    "atgenexp":                      "klepikova",
    "atgenexp_hormone":              "klepikova",
    "atgenexp_pathogen":             "klepikova",
    "atgenexp_plus":                 "klepikova",
    "atgenexp_stress":               "klepikova",
    "guard_cell":                    "klepikova",
    "hnahal":                        "klepikova",
    "lateral_root_initiation":       "klepikova",
    "light_series":                  "klepikova",
    "meristem_db":                   "klepikova",
    "meristem_db_new":               "klepikova",
    "root":                          "klepikova",
    "rohan":                         "klepikova",
    "rpatel":                        "klepikova",
    "seed_db":                       "klepikova",
    # Lipid map stores lipid-class IDs, not AGI — fall back to RNA-seq for AGI examples
    "lipid_map":                     "klepikova",
    # Seedcoat uses a legacy non-AGI format; fall back to standard RNA-seq AGI IDs
    "seedcoat":                      "klepikova",
    # Non-arabidopsis microarray databases
    "barley_mas":                    "barley_seed",
    "barley_rma":                    "barley_seed",
    "human_developmental":           "human_body_map_2",
    "human_developmental_SpongeLab": "human_body_map_2",
    "human_diseased":                "human_body_map_2",
    "maize_gdowns":                  "maize_atlas",
    "medicago_mas":                  "medicago_root",
    "medicago_rma":                  "medicago_root",
    "poplar":                        "poplar_hormone",
    "rice_mas":                      "rice_drought_heat_stress",
    "rice_rma":                      "rice_drought_heat_stress",
    # Triticale has no non-probeset database; use wheat IDs (triticale is wheat × rye)
    "triticale":                     "wheat",
    "triticale_mas":                 "wheat",
}

# ---------------------------------------------------------------------------
# Cross-species invalid gene (invalid type 3: completely wrong species)
# ---------------------------------------------------------------------------
CROSS_SPECIES = {
    "arabidopsis":          "Solyc04g054700",   # tomato gene
    "arabidopsis lipid":    "Solyc04g054700",
    "arabidopsis cell":     "Solyc04g054700",
    "arabidopsis seedcoat": "Solyc04g054700",
    "human":                "At1g01010",        # plant gene
    "mouse":                "At1g01010",
}
_DEFAULT_CROSS = "At1g01010"  # arabidopsis gene — wrong for every non-arabidopsis species


def _load_genes(db_name: str, species_regex: str, n: int = 3) -> list[str]:
    """Return up to *n* unique data_probeset_id values that match *species_regex*."""
    path = JSON_DIR / f"{db_name}_test_data.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    seen: set[str] = set()
    result: list[str] = []
    for row in data:
        gid = str(row.get("data_probeset_id") or "").strip()
        if gid and gid not in seen and re.search(species_regex, gid, re.I):
            seen.add(gid)
            result.append(gid)
        if len(result) >= n:
            break
    return result


def _invalid_initially(gene: str) -> str:
    """Change the first character to a wrong type (letter→digit, digit/other→letter)."""
    if not gene:
        return "INVALID"
    return ("9" if gene[0].isalpha() else "Z") + gene[1:]


def _invalid_finally(gene: str, regex: str = "") -> str:
    """Change the last character to a wrong type; fall back to appending '.X' if the
    first mutation still passes the regex (e.g. when the regex uses [0-9A-Z]+)."""
    if not gene:
        return "INVALID"
    candidate = gene[:-1] + ("X" if gene[-1].isdigit() else "9")
    if regex and re.search(regex, candidate, re.I):
        # First mutation wasn't enough — append a clearly invalid version suffix
        candidate = gene + ".X"
    return candidate


def main() -> None:
    db_data: dict = json.loads(Path("species_databases.json").read_text())

    fieldnames = [
        "species", "view", "database", "regex",
        "valid_gene_1", "valid_gene_2", "valid_gene_3",
        "invalid_gene_1_wrong_initially",
        "invalid_gene_2_wrong_finally",
        "invalid_gene_3_other_species",
    ]
    rows: list[dict] = []

    for species, views in db_data.items():
        regex = SPECIES_REGEX.get(species, "")
        cross = CROSS_SPECIES.get(species, _DEFAULT_CROSS)

        for view, db in views.items():
            source_db = PROBESET_FALLBACK.get(db, db)
            genes = _load_genes(source_db, regex) if regex else []

            # Pad to 3 slots
            while len(genes) < 3:
                genes.append("")

            ref = genes[0]
            rows.append({
                "species":                       species,
                "view":                          view,
                "database":                      db,
                "regex":                         regex,
                "valid_gene_1":                  genes[0],
                "valid_gene_2":                  genes[1],
                "valid_gene_3":                  genes[2],
                "invalid_gene_1_wrong_initially": _invalid_initially(ref) if ref else "INVALID",
                "invalid_gene_2_wrong_finally":  _invalid_finally(ref, regex) if ref else "INVALID",
                "invalid_gene_3_other_species":  cross,
            })

    out = Path("efp_test_cases.csv")
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Written {len(rows)} rows to {out}")


if __name__ == "__main__":
    main()
