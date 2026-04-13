"""
Reena Obmina | BCB330 Project 2025-2026 | University of Toronto

Scrapes view names and their database names from each species' datasources.xml.

Reads:  {efp_base}/data/datasources.xml for each species in EFP_SITES
Writes: species_databases.json — ``{ species: { view_name: db_name, ... }, ... }``

Run this first to discover what views exist for a species before running
scrape_species_view_info.py or audit_efp_xml_duplicates.py.
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


def fetch_view_databases(species, efp_url):
    """Fetch datasources.xml for a species and extract view name → database name mappings.

    :param species: Species key (e.g. ``'arabidopsis'``), used only for error messages.
    :type species: str
    :param efp_url: Full URL to the species' efpWeb.cgi endpoint.
    :type efp_url: str
    :returns: Dict mapping view name to database name, or an empty dict on failure.
    :rtype: dict[str, str]
    """
    base_url = efp_url.rsplit("/", 2)[0]
    datasources_url = f"{base_url}/data/datasources.xml"

    views = {}
    try:
        resp = requests.get(datasources_url, timeout=15)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)

        for datasource in root.findall(".//datasource"):
            db_elem = datasource.find("db")
            name_elem = datasource.find("name")

            if db_elem is not None and name_elem is not None:
                db_name = db_elem.text.strip() if db_elem.text else None
                view_name = name_elem.text.strip() if name_elem.text else None

                if view_name and db_name:
                    views[view_name] = db_name

    except Exception as e:
        print(f"  Error fetching datasources for {species}: {e}")

    return views


def main():
    """Iterate over all EFP sites, collect view-to-database mappings, and write output."""
    all_species_databases = {}

    for species, efp_url in EFP_SITES.items():
        print(f"Processing {species}...")
        views = fetch_view_databases(species, efp_url)
        if views:
            all_species_databases[species] = views
            print(f"  Found {len(views)} views")
        else:
            print(f"  No views found")

    out_file = "species_databases.json"
    with open(out_file, "w") as f:
        json.dump(all_species_databases, f, indent=2)

    print(f"\nOutput written to {out_file}")


if __name__ == "__main__":
    main()
