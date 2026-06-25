"""
Reena Obmina | BCB330 Project 2025-2026 | University of Toronto

Scrapes groups, controls, and treatments for every view of every species,
covering BOTH eFP databases and ePlant databases, tagged by source so
eFP-only / ePlant-only / shared databases can be told apart.

Reuses the live site/view discovery already built and verified in
scrape_view_databases.py (same dropdown/viewNames.json + XML paths) instead
of duplicating it here. This replaces the old approach of reading
__pycache__/eplant_efp_views/eplant_audit.json (Vincent's server-local-only
ePlant audit) for ePlant layout info -- that file isn't available to other
team members and could go stale, whereas viewNames.json is live and public.
Run scrape_view_databases.py first if you only want the flat view->db
mapping (species_databases.json); this script additionally pulls each
view's full group/tissue/sample breakdown.

Reads:  {efp_base}/data/{datasource}.xml for each eFP species
        {eplant_base}/data/{family}/viewNames.json + per-view XML for each ePlant project
Writes: data/efp_info/efp_eplant_species_view_info.json -- combined output,
        each view tagged "source": "efp" or "eplant", keyed the same way as
        species_databases.json ("efp_<species>" / "eplant_<species>")
        data/efp_info/db_source_summary.json -- db name -> efp/eplant/both
"""

import json
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from scrape_view_databases import (
    EFP_SITES,
    _SPECIAL_CASES,
    _HARDCODED,
    _EFP_FALLBACK,
    get_datasource_options,
    EPLANT_SITES,
    EPLANT_SPECIES_FILE,
    EPLANT_FAMILIES,
    EPLANT_DB_OVERRIDE,
    get_eplant_view_names,
    _flat_view_label,
    _NESTED_EFPS_FAMILIES,
)

REQUEST_TIMEOUT = 20


def fetch_xml_root(xml_url):
    """Fetch a view's XML and return the parsed root element, or None on failure."""
    try:
        resp = requests.get(xml_url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return ET.fromstring(resp.content)
    except Exception as e:
        print(f"    Error fetching {xml_url}: {e}")
        return None


def extract_db(root):
    """Return the db attribute from the first <view> element, or None."""
    view = root.find(".//view")
    return view.get("db") if view is not None else None


def parse_groups(root):
    """Parse <group>/<tissue>/<sample> elements into {group_name: {controls, treatments}}."""
    groups = {}
    for group in root.findall(".//group"):
        group_name = group.get("name")
        if not group_name:
            continue

        controls = [c.get("sample") for c in group.findall("control") if c.get("sample")]

        treatments = {}
        for tissue in group.findall("tissue"):
            t_name = tissue.get("name")
            if not t_name:
                continue
            t_key = t_name.replace(" ", "_")
            samples = [s.get("name") for s in tissue.findall("sample") if s.get("name")]
            treatments.setdefault(t_key, [])
            treatments[t_key].extend(samples)

        groups[group_name.replace(" ", "_")] = {"controls": controls, "treatments": treatments}

    return groups


# ---------------------------------------------------------------------------
# eFP
# ---------------------------------------------------------------------------


def fetch_efp_view(species, base_url, value, label):
    """Fetch one eFP view's XML and return its db + group breakdown, tagged as eFP."""
    xml_url = f"{base_url}/data/{value}.xml"
    root = fetch_xml_root(xml_url)
    if root is None:
        return None
    return {
        "source": "efp",
        "species": species,
        "database": extract_db(root),
        "view_name": label,
        "view_file": value,
        "groups": parse_groups(root),
    }


def _hardcoded_or_fallback_views(species, db_by_label):
    """Build view entries (no group data available) for a hardcoded/fallback species."""
    return [
        {
            "source": "efp",
            "species": species,
            "database": db_name,
            "view_name": label,
            "view_file": None,
            "groups": {},
        }
        for label, db_name in db_by_label.items()
    ]


def collect_efp_views():
    """Discover and fetch every eFP species' views."""
    results = {}
    for species, efp_url in EFP_SITES.items():
        print(f"[efp] Processing {species}...")
        base_url = efp_url.rsplit("/", 2)[0]
        key = f"efp_{species.replace(' ', '_')}"

        if species in _HARDCODED:
            results[key] = _hardcoded_or_fallback_views(species, _HARDCODED[species])
            continue

        options = _SPECIAL_CASES.get(species) or get_datasource_options(efp_url)
        if not options:
            if species in _EFP_FALLBACK:
                print("  Live scrape failed -- using last-known-good fallback (no group data)")
                results[key] = _hardcoded_or_fallback_views(species, _EFP_FALLBACK[species])
            else:
                print("  No views found")
                results[key] = []
            continue

        species_views = []
        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = {
                pool.submit(fetch_efp_view, species, base_url, value, label): label
                for value, label in options
            }
            for future in as_completed(futures):
                view = future.result()
                if view:
                    species_views.append(view)
        print(f"  Found {len(species_views)} views")
        results[key] = species_views
    return results


# ---------------------------------------------------------------------------
# ePlant
# ---------------------------------------------------------------------------


def eplant_xml_url(base_url, family, folder, species_file):
    """Build the XML URL for an ePlant view, mirroring scrape_view_databases.fetch_eplant_db."""
    if folder is None:
        return f"{base_url}/data/{family}/{species_file}.xml"
    nested = "efps/" if family in _NESTED_EFPS_FAMILIES else ""
    return f"{base_url}/data/{family}/{nested}{folder}/{species_file}.xml"


def fetch_eplant_view(site, base_url, family, display, folder, species_file):
    """Fetch one ePlant view's XML and return its db + group breakdown, tagged as ePlant.

    The view is kept even when no db="..." attribute is present (e.g. eplant_tomato's
    Cell viewer), with database: None, so view counts match Vincent's eplant_views.csv
    audit exactly -- a real view with an unknown database is still a real view.
    """
    xml_url = eplant_xml_url(base_url, family, folder, species_file)
    root = fetch_xml_root(xml_url)
    if root is None:
        return None
    db = extract_db(root) or EPLANT_DB_OVERRIDE.get((site, family))
    return {
        "source": "eplant",
        "project": site,
        "species": species_file,
        "family": family,
        "database": db,
        "view_name": display,
        "view_folder": folder,
        "groups": parse_groups(root),
    }


def collect_eplant_views():
    """Discover (via viewNames.json, same as scrape_view_databases.py) and fetch every ePlant view."""
    jobs = []
    for site, base_url in EPLANT_SITES.items():
        species_file = EPLANT_SPECIES_FILE[site]
        for family in EPLANT_FAMILIES[site]:
            names = get_eplant_view_names(base_url, family)
            if names is not None:
                for display in names:
                    folder = display.replace(" ", "")
                    jobs.append((site, base_url, family, display, folder, species_file))
            else:
                jobs.append((site, base_url, family, _flat_view_label(family), None, species_file))

    results = {}
    print(f"[eplant] Fetching {len(jobs)} candidate views across {len(EPLANT_SITES)} projects...")
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(fetch_eplant_view, *job): job[0] for job in jobs}
        for future in as_completed(futures):
            site = futures[future]
            view = future.result()
            if view:
                results.setdefault(site, []).append(view)
    for site in EPLANT_SITES:
        print(f"  {site}: fetched {len(results.get(site, []))} views")
    return results


def build_db_source_summary(efp_results, eplant_results):
    """Map each database name to which source(s) it appears under."""
    summary = {}
    for views in efp_results.values():
        for view in views:
            db = view.get("database")
            if db:
                summary.setdefault(db, set()).add("efp")
    for views in eplant_results.values():
        for view in views:
            db = view.get("database")
            if db:
                summary.setdefault(db, set()).add("eplant")

    return {
        db: ("both" if sources == {"efp", "eplant"} else next(iter(sources)))
        for db, sources in summary.items()
    }


def main():
    efp_results = collect_efp_views()
    eplant_results = collect_eplant_views()

    combined = {"efp": efp_results, "eplant": eplant_results}
    out_file = "data/efp_info/efp_eplant_species_view_info.json"
    with open(out_file, "w") as f:
        json.dump(combined, f, indent=2)
    print(f"\nOutput written to {out_file}")

    db_summary = build_db_source_summary(efp_results, eplant_results)
    summary_file = "data/efp_info/db_source_summary.json"
    with open(summary_file, "w") as f:
        json.dump(db_summary, f, indent=2, sort_keys=True)
    print(f"Output written to {summary_file}")

    efp_only = sum(1 for v in db_summary.values() if v == "efp")
    eplant_only = sum(1 for v in db_summary.values() if v == "eplant")
    both = sum(1 for v in db_summary.values() if v == "both")
    print(f"\nDatabases: {len(db_summary)} total -- eFP-only: {efp_only}, ePlant-only: {eplant_only}, both: {both}")


if __name__ == "__main__":
    main()
