"""
Reena Obmina | BCB330 Project 2025-2026 | University of Toronto

Task (Jul 2026): test the production gene ID validators against each live
efp/eplant project's OWN example gene ID, instead of only against Vincent's
curated sample dumps in api/random_rows_json/.

Motivation: api/random_rows_json/ only has data for the databases Vincent
happened to sample, and even where it does, the specific IDs picked can miss
edge cases -- e.g. every barley_spike_meristem_v3 sample happened to include
a trailing isoform suffix (HORVU.MOREX.r3.2HG0105390.1), which masked a real
gap: BAR's own eplant_barley (v3) page uses a bare gene ID with no suffix
(HORVU.MOREX.r3.1HG0000030) as its canonical example, and that failed
is_barley_gene_valid until this test caught it (see git history/PR for the fix).

Each species view's datasource XML (data/{view}.xml) does NOT contain gene
IDs at all -- it only has tissue/sample/group names for the diagram -- so
that's not usable as a source here. The actual live, authoritative example
gene ID for a project lives in the page HTML itself:
  - eFP (efpWeb.cgi, server-rendered): the "Primary Gene ID" <input
    name="primaryGene" value="..."> default.
  - ePlant (client-rendered SPA): a static "Example: <a>ID</a>" search hint
    baked into the page shell (present even before any JS runs).

Reads (live, over HTTP): every project in EFP_SITES and EPLANT_SITES
Reads (local):  api/utils/bar_utils.py       -- EFP_PROJECT_REGEXES, BARUtils
                api/utils/gene_id_utils.py   -- GeneIdUtils.validate_gene_id
Writes: live_example_gene_id_coverage.csv -- one row per project: the live
        example ID, which validator it was checked against, and the result.
"""

import csv
import re
import sys
import types
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

# importing api.utils.* normally runs api/__init__.py's create_app(), which
# tries to connect to MySQL even for this standalone script. Pre-register
# empty stand-in packages so Python loads the submodules directly instead.
sys.modules.setdefault("api", types.ModuleType("api"))
sys.modules["api"].__path__ = ["api"]
sys.modules.setdefault("api.utils", types.ModuleType("api.utils"))
sys.modules["api.utils"].__path__ = ["api/utils"]

from api.utils.bar_utils import EFP_PROJECT_REGEXES, BARUtils  # noqa: E402
from api.utils.gene_id_utils import GeneIdUtils, _VALIDATORS  # noqa: E402

from scrape_view_databases import EFP_SITES, EPLANT_SITES  # noqa: E402

REQUEST_TIMEOUT = 20

# EFP_SITES keys that map straight to "efp_" + key.replace(" ", "_") in
# EFP_PROJECT_REGEXES for every project EXCEPT these two.
EFP_PROJECT_KEY_OVERRIDES = {
    "arabidopsis seedcoat": "efp_seedcoat",
    "mouse": "mouse_efp",
}

PRIMARY_GENE_RE = re.compile(r'<input[^>]*name="primaryGene"[^>]*>', re.IGNORECASE)
VALUE_ATTR_RE = re.compile(r'value="([^"]*)"')
EPLANT_EXAMPLE_RE = re.compile(r"Example:\s*<a[^>]*>([^<]+)</a>", re.IGNORECASE)


def efp_project_key(species):
    return EFP_PROJECT_KEY_OVERRIDES.get(species, f"efp_{species.replace(' ', '_')}")


def eplant_species_key(site):
    """eplant_barley_legacy -> barley, eplant_maize -> maize, etc."""
    return site.removeprefix("eplant_").removesuffix("_legacy")


def fetch(url):
    resp = requests.get(url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.text


def check_efp_project(species, efp_url):
    project_key = efp_project_key(species)
    row = {
        "source": "efp",
        "project": f"efp_{species.replace(' ', '_')}",
        "validator_key": project_key,
        "example_gene_id": "",
        "result": "",
    }
    try:
        html = fetch(efp_url)
    except Exception as e:
        row["result"] = f"FETCH_ERROR: {e}"
        return row

    tag_match = PRIMARY_GENE_RE.search(html)
    value_match = VALUE_ATTR_RE.search(tag_match.group(0)) if tag_match else None
    if not value_match or not value_match.group(1):
        row["result"] = "NO_EXAMPLE_FOUND"
        return row

    example_id = value_match.group(1)
    row["example_gene_id"] = example_id

    if project_key not in EFP_PROJECT_REGEXES:
        row["result"] = "NO_REGEX_MAPPING"
        return row

    row["result"] = "PASS" if BARUtils.is_efp_gene_valid(example_id, project_key) else "FAIL"
    return row


def check_eplant_project(site, base_url):
    species_key = eplant_species_key(site)
    row = {
        "source": "eplant",
        "project": site,
        "validator_key": species_key,
        "example_gene_id": "",
        "result": "",
    }
    try:
        html = fetch(base_url)
    except Exception as e:
        row["result"] = f"FETCH_ERROR: {e}"
        return row

    match = EPLANT_EXAMPLE_RE.search(html)
    if not match:
        row["result"] = "NO_EXAMPLE_FOUND"
        return row

    example_id = match.group(1).strip()
    row["example_gene_id"] = example_id

    if species_key not in _VALIDATORS:
        row["result"] = "NO_VALIDATOR_MAPPING"
        return row

    row["result"] = "PASS" if GeneIdUtils.validate_gene_id(example_id, species_key) else "FAIL"
    return row


def main():
    rows = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(check_efp_project, species, url): species for species, url in EFP_SITES.items()}
        futures.update(
            {pool.submit(check_eplant_project, site, url): site for site, url in EPLANT_SITES.items()}
        )
        for future in as_completed(futures):
            rows.append(future.result())

    rows.sort(key=lambda r: (r["source"], r["project"]))

    out_file = "live_example_gene_id_coverage.csv"
    with open(out_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["source", "project", "validator_key", "example_gene_id", "result"])
        writer.writeheader()
        writer.writerows(rows)

    counts = {}
    for row in rows:
        key = row["result"].split(":")[0]
        counts[key] = counts.get(key, 0) + 1

    print(f"Checked {len(rows)} projects ({sum(1 for r in rows if r['source'] == 'efp')} efp, "
          f"{sum(1 for r in rows if r['source'] == 'eplant')} eplant).")
    for key, count in sorted(counts.items()):
        print(f"  {key}: {count}")
    print(f"Report written to {out_file}")

    fails = [r for r in rows if r["result"] == "FAIL"]
    if fails:
        print("\nFAILURES (live example ID rejected by production validator):")
        for r in fails:
            print(f"  {r['project']:30s} example={r['example_gene_id']!r:35s} validator={r['validator_key']}")


if __name__ == "__main__":
    main()
