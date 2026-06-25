"""
Reena Obmina | BCB330 Project 2025-2026 | University of Toronto

Scrapes view names and their database names from each species' datasources.xml,
covering BOTH eFP databases and ePlant databases, so the master list notes which
databases are eFP-only, ePlant-only, or available through both frontends.

eFP side:
    Reads:  {efp_base}/data/{datasource}.xml for each datasource in each species'
            HTML dropdown (discovered live from the efpWeb.cgi page itself).

ePlant side:
    Each ePlant project (e.g. eplant_maize) has its own set of "*eFP viewer" tabs
    (family names like "experiment", "plant", "cell" -- "Tissue and experiment eFP
    viewer", "Plant eFP viewer", "Cell eFP viewer"). When a tab has more than one
    view, the app populates a "Select View" dropdown from {base}/data/{family}/
    viewNames.json. When a tab has exactly one view, there's no dropdown/JSON file
    and the view's XML sits directly at {base}/data/{family}/{species_file}.xml.
    Reads:  {eplant_base}/data/{family}/viewNames.json (dropdown views, if any)
            {eplant_base}/data/{family}/efps/{folder}/{species_file}.xml (per-view
                XML for the "experiment" family, which nests views under "efps/")
            {eplant_base}/data/{family}/{folder}/{species_file}.xml (per-view XML
                for other families, which nest views directly)
    The per-project species filename and family list are stable, project-specific
    paths on the server and aren't otherwise discoverable over HTTP, so they're
    hardcoded below (cross-checked against Vincent's eplant_audit.json).

Writes: species_databases.json -- ``{ species_or_project: { view_name: db_name, ... }, ... }``
        Keys prefixed "efp_" + the eFP species (e.g. "efp_arabidopsis") or "eplant_" +
        the ePlant project's species (e.g. "eplant_maize") so eFP-only vs ePlant-only vs shared databases
        can be told apart just by which key(s) a db name shows up under.

Run this first to discover what views exist for a species before running
build_proj_id_view_mapping.py.
"""

import re
import xml.etree.ElementTree as ET
import json

import requests

# ---------------------------------------------------------------------------
# eFP sites
# ---------------------------------------------------------------------------
EFP_SITES = {
    "arabidopsis": "https://bar.utoronto.ca/efp_arabidopsis/cgi-bin/efpWeb.cgi",
    "arabidopsis lipid": "https://bar.utoronto.ca/efp_arabidopsis_lipid/cgi-bin/efpWeb.cgi",
    "arabidopsis cell": "https://bar.utoronto.ca/cell_efp/cgi-bin/cell_efp.cgi",
    "arabidopsis seedcoat": "https://bar.utoronto.ca/efp_seedcoat/cgi-bin/efpWeb.cgi",
    "poplar": "https://bar.utoronto.ca/efppop/cgi-bin/efpWeb.cgi",
    "medicago": "https://bar.utoronto.ca/efpmedicago/cgi-bin/efpWeb.cgi",
    "soybean": "https://bar.utoronto.ca/efpsoybean/cgi-bin/efpWeb.cgi",
    "potato": "https://bar.utoronto.ca/efp_potato/cgi-bin/efpWeb.cgi",
    "tomato": "https://bar.utoronto.ca/efp_tomato/cgi-bin/efpWeb.cgi",
    "eutrema": "https://bar.utoronto.ca/efp_eutrema/cgi-bin/efpWeb.cgi",
    "camelina": "https://bar.utoronto.ca/efp_camelina/cgi-bin/efpWeb.cgi",
    "arachis": "https://bar.utoronto.ca/efp_arachis/cgi-bin/efpWeb.cgi",
    "grape": "https://bar.utoronto.ca/efp_grape/cgi-bin/efpWeb.cgi",
    "cannabis": "https://bar.utoronto.ca/efp_cannabis/cgi-bin/efpWeb.cgi",
    "kalanchoe": "https://bar.utoronto.ca/efp_kalanchoe/cgi-bin/efpWeb.cgi",
    "actinidia": "https://bar.utoronto.ca/efp_actinidia/cgi-bin/efpWeb.cgi",
    "brassica rapa": "https://bar.utoronto.ca/efp_brassica_rapa/cgi-bin/efpWeb.cgi",
    "canola": "https://bar.utoronto.ca/efp_canola/cgi-bin/efpWeb.cgi",
    "cacao ccn": "https://bar.utoronto.ca/efp_cacao_ccn/cgi-bin/efpWeb.cgi",
    "cacao sca": "https://bar.utoronto.ca/efp_cacao_sca/cgi-bin/efpWeb.cgi",
    "cacao tc": "https://bar.utoronto.ca/efp_cacao_tc/cgi-bin/efpWeb.cgi",
    "mangosteen": "https://bar.utoronto.ca/efp_mangosteen/cgi-bin/efpWeb.cgi",
    "lupin": "https://bar.utoronto.ca/efp_lupin/cgi-bin/efpWeb.cgi",
    "strawberry": "https://bar.utoronto.ca/efp_strawberry/cgi-bin/efpWeb.cgi",
    "maize": "https://bar.utoronto.ca/efp_maize/cgi-bin/efpWeb.cgi",
    "rice": "https://bar.utoronto.ca/efprice/cgi-bin/efpWeb.cgi",
    "barley": "https://bar.utoronto.ca/efpbarley/cgi-bin/efpWeb.cgi",
    "triticale": "https://bar.utoronto.ca/efp_triticale/cgi-bin/efpWeb.cgi",
    "brachypodium": "https://bar.utoronto.ca/efp_brachypodium/cgi-bin/efpWeb.cgi",
    "wheat": "https://bar.utoronto.ca/efp_wheat/cgi-bin/efpWeb.cgi",
    "little millet": "https://bar.utoronto.ca/efp_little_millet/cgi-bin/efpWeb.cgi",
    "oat": "https://bar.utoronto.ca/efp_oat/cgi-bin/efpWeb.cgi",
    "physcomitrella": "https://bar.utoronto.ca/efp_physcomitrella/cgi-bin/efpWeb.cgi",
    "selaginella": "https://bar.utoronto.ca/efp_selaginella/cgi-bin/efpWeb.cgi",
    "mouse": "https://bar.utoronto.ca/mouse_efp/cgi-bin/efpWeb.cgi",
    "human": "https://bar.utoronto.ca/efp_human/cgi-bin/efpWeb.cgi",
    "phelipanche": "https://bar.utoronto.ca/efp_phelipanche/cgi-bin/efpWeb.cgi",
    "striga": "https://bar.utoronto.ca/efp_striga/cgi-bin/efpWeb.cgi",
    "triphysaria": "https://bar.utoronto.ca/efp_triphysaria/cgi-bin/efpWeb.cgi",
    # Found by cross-checking api/random_rows_json/ sample data against this site
    # list: these sites exist live but were never added here.
    "durum wheat": "https://bar.utoronto.ca/efp_durum_wheat/cgi-bin/efpWeb.cgi",
    "euphorbia": "https://bar.utoronto.ca/efp_euphorbia/cgi-bin/efpWeb.cgi",
    "marchantia": "https://bar.utoronto.ca/efp_marchantia/cgi-bin/efpWeb.cgi",
    "sorghum": "https://bar.utoronto.ca/efp_sorghum/cgi-bin/efpWeb.cgi",
    "tung tree": "https://bar.utoronto.ca/efp_tung_tree/cgi-bin/efpWeb.cgi",
    "apple": "https://bar.utoronto.ca/efp_apple/cgi-bin/efpWeb.cgi",
    # Metabolite/enzyme-class sites -- see _HARDCODED below for why these are
    # single fixed views rather than scraped dropdowns.
    "maize enzyme": "https://bar.utoronto.ca/efp_maize_enzyme/cgi-bin/efpWeb.cgi",
    "maize metabolite": "https://bar.utoronto.ca/efp_maize_metabolite/cgi-bin/efpWeb.cgi",
    "rice metabolite": "https://bar.utoronto.ca/efp_rice_metabolite/cgi-bin/efpWeb.cgi",
    "brachypodium metabolites": "https://bar.utoronto.ca/efp_brachypodium_metabolites/cgi-bin/efpWeb.cgi",
}

# Sites that do not use the standard dataSource dropdown; map them manually.
# (species key → list of (datasource_xml_filename, display_name) to look up)
_SPECIAL_CASES = {
    # Uses a lipidClass dropdown instead of dataSource; one fixed XML file.
    "arabidopsis lipid": [("Lipid_Map", "Lipid Map")],
}

# Sites with no discoverable XML; database names are hardcoded from known config.
_HARDCODED = {
    # Single-view cell browser with no dropdown and access-denied data directory.
    "arabidopsis cell": {"Cell Type": "single_cell"},
    # Metabolite/enzyme-class eFPs: the dataSource dropdown lists individual
    # compounds/enzymes (e.g. "Rubisco (initial)", "Glucose-6-phosphate") as the
    # *query parameter* into one single database, not separate per-compound
    # databases -- their XML has no per-option db= attribute. Confirmed against
    # Vincent's regex patterns (efp_maize_enzyme etc. validate the compound NAME
    # as the "gene_id", not a real gene ID) and the one underlying db each site
    # actually has sample data for.
    "maize enzyme": {"Enzyme Activity": "maize_enzyme"},
    "maize metabolite": {"Metabolite Level": "maize_metabolite"},
    "rice metabolite": {"Metabolite Level": "rice_metabolite"},
    "brachypodium metabolites": {"Metabolite Level": "brachypodium_metabolites_map"},
}

# efp_human currently 403s for us (server-side block, not a code issue). Fall back
# to the last-known-good scrape rather than silently dropping "human" from the output.
_EFP_FALLBACK = {
    "human": {
        "Circulatory Respiratory": "human_developmental",
        "Illumina Body Map 2 - FPKM": "human_body_map_2",
        "Nervous": "human_developmental",
        "Reproductive": "human_developmental",
        "Skeletal Immune Digestive": "human_developmental",
    },
}

# ---------------------------------------------------------------------------
# ePlant sites
# ---------------------------------------------------------------------------
EPLANT_SITES = {
    "eplant_arabidopsis": "https://bar.utoronto.ca/eplant",
    "eplant_maize": "https://bar.utoronto.ca/eplant_maize",
    "eplant_poplar": "https://bar.utoronto.ca/eplant_poplar",
    "eplant_tomato": "https://bar.utoronto.ca/eplant_tomato",
    "eplant_camelina": "https://bar.utoronto.ca/eplant_camelina",
    "eplant_soybean": "https://bar.utoronto.ca/eplant_soybean",
    "eplant_potato": "https://bar.utoronto.ca/eplant_potato",
    "eplant_barley": "https://bar.utoronto.ca/eplant_barley",
    "eplant_barley_legacy": "https://bar.utoronto.ca/eplant_barley_legacy",
    "eplant_medicago": "https://bar.utoronto.ca/eplant_medicago",
    "eplant_eucalyptus": "https://bar.utoronto.ca/eplant_eucalyptus",
    "eplant_rice": "https://bar.utoronto.ca/eplant_rice",
    "eplant_willow": "https://bar.utoronto.ca/eplant_willow",
    "eplant_sunflower": "https://bar.utoronto.ca/eplant_sunflower",
    "eplant_cannabis": "https://bar.utoronto.ca/eplant_cannabis",
    "eplant_wheat": "https://bar.utoronto.ca/eplant_wheat",
    "eplant_sugarcane": "https://bar.utoronto.ca/eplant_sugarcane",
}

# Species filename used in each ePlant project's per-view XML paths
# (e.g. .../data/experiment/efps/AbioticStress/Arabidopsis_thaliana.xml).
# Sourced from Vincent's eplant_audit.json (species detection per project);
# not discoverable over HTTP since these sites don't expose species.json publicly.
EPLANT_SPECIES_FILE = {
    "eplant_arabidopsis": "Arabidopsis_thaliana",
    "eplant_maize": "Zea_mays",
    "eplant_poplar": "Populus_trichocarpa",
    "eplant_tomato": "Solanum_lycopersicum",
    "eplant_camelina": "Camelina_sativa",
    "eplant_soybean": "Glycine_max",
    "eplant_potato": "Solanum_tuberosum",
    "eplant_barley": "Hordeum_vulgare",
    "eplant_barley_legacy": "Hordeum_vulgare",
    "eplant_medicago": "Medicago_truncatula",
    "eplant_eucalyptus": "Eucalyptus_grandis",
    "eplant_rice": "Oryza_sativa",
    "eplant_willow": "Salix_purpurea",
    "eplant_sunflower": "Helianthus_annuus",
    "eplant_cannabis": "Cannabis_sativa",
    "eplant_wheat": "Triticum_aestivum",
    "eplant_sugarcane": "Saccharum_R570",
}

# "*eFP viewer" tabs (families) every ePlant project has, plus per-project extras.
_DEFAULT_EPLANT_FAMILIES = ["cell", "experiment", "plant"]
EPLANT_FAMILIES = {
    site: (["cell", "experiment", "plant", "worldLeaf", "worldXylem"] if site == "eplant_poplar" else _DEFAULT_EPLANT_FAMILIES)
    for site in EPLANT_SITES
}

# Families always nest their per-view XML under an "efps/" subfolder.
_NESTED_EFPS_FAMILIES = {"experiment"}

# Views whose XML has no db="..." attribute to scrape (single-cell browsers);
# the db is known from existing eFP config instead.
EPLANT_DB_OVERRIDE = {
    ("eplant_arabidopsis", "cell"): "single_cell",
}


def get_datasource_options(efp_url):
    """Fetch the eFP HTML page and extract all datasource option values and display names.

    :param efp_url: Full URL to the species' eFP CGI endpoint.
    :type efp_url: str
    :returns: List of (option_value, display_name) tuples, or empty list on failure.
    :rtype: list[tuple[str, str]]
    """
    options = []
    try:
        resp = requests.get(efp_url, timeout=15)
        resp.raise_for_status()
        html = resp.text

        # Match <option value="Some_Value"\n>Display Name</option>
        pattern = re.compile(
            r'<option\s+value="([^"]+)"[^>]*>\s*([^<]+?)\s*</option>',
            re.IGNORECASE | re.DOTALL,
        )
        for match in pattern.finditer(html):
            value = match.group(1).strip()
            label = match.group(2).strip()
            if value and label:
                options.append((value, label))
    except Exception as e:
        print(f"    Error fetching HTML: {e}")
    return options


def fetch_db_name(base_url, datasource_value):
    """Fetch the per-datasource XML and return the first database name found.

    :param base_url: Base URL for the eFP site (e.g. ``'https://bar.utoronto.ca/efp_arabidopsis'``).
    :type base_url: str
    :param datasource_value: Option value from the dropdown (e.g. ``'Developmental_Map'``).
    :type datasource_value: str
    :returns: Database name string, or ``None`` if not found.
    :rtype: str | None
    """
    xml_url = f"{base_url}/data/{datasource_value}.xml"
    try:
        resp = requests.get(xml_url, timeout=15)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        view = root.find(".//view")
        if view is not None:
            return view.get("db")
    except Exception:
        pass
    return None


def fetch_view_databases(species, efp_url):
    """Fetch view name → database name mappings for one eFP species.

    :param species: Species key (e.g. ``'arabidopsis'``), used only for error messages.
    :type species: str
    :param efp_url: Full URL to the species' efpWeb.cgi endpoint.
    :type efp_url: str
    :returns: Dict mapping view display name to database name, or an empty dict on failure.
    :rtype: dict[str, str]
    """
    base_url = efp_url.rsplit("/", 2)[0]

    if species in _HARDCODED:
        return _HARDCODED[species]

    if species in _SPECIAL_CASES:
        options = _SPECIAL_CASES[species]
    else:
        options = get_datasource_options(efp_url)
        if not options:
            return {}

    views = {}
    for value, label in options:
        db_name = fetch_db_name(base_url, value)
        if db_name:
            views[label] = db_name
        else:
            print(f"    No db found for datasource '{value}' ({label})")

    return views


def get_eplant_view_names(base_url, family):
    """Fetch the "Select View" dropdown options for one ePlant family, if any.

    :param base_url: Base URL for the ePlant project (e.g. ``'https://bar.utoronto.ca/eplant_maize'``).
    :type base_url: str
    :param family: Family/tab name (e.g. ``'experiment'``, ``'plant'``, ``'cell'``).
    :type family: str
    :returns: List of display names (possibly empty) if a dropdown exists, else ``None``
        when there's no viewNames.json at all (single-view or no-view family).
    :rtype: list[str] | None
    """
    url = f"{base_url}/data/{family}/viewNames.json"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        names = resp.json()
        if isinstance(names, list):
            return [n.strip() for n in names if isinstance(n, str) and n.strip()]
    except Exception:
        pass
    return None


def fetch_eplant_db(base_url, family, folder, species_file):
    """Fetch one ePlant view's XML and return its db attribute.

    :param base_url: Base URL for the ePlant project.
    :type base_url: str
    :param family: Family/tab name the view belongs to.
    :type family: str
    :param folder: View's on-disk folder name (display name with spaces removed), or
        ``None`` for a flat family with no per-view subfolder (XML sits directly under
        the family directory).
    :type folder: str | None
    :param species_file: Species XML filename stem (e.g. ``'Zea_mays'``).
    :type species_file: str
    :returns: Database name string, or ``None`` if not found.
    :rtype: str | None
    """
    if folder is None:
        xml_url = f"{base_url}/data/{family}/{species_file}.xml"
    else:
        nested = "efps/" if family in _NESTED_EFPS_FAMILIES else ""
        xml_url = f"{base_url}/data/{family}/{nested}{folder}/{species_file}.xml"
    try:
        resp = requests.get(xml_url, timeout=15)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        view = root.find(".//view")
        if view is not None:
            return view.get("db")
    except Exception:
        pass
    return None


def _flat_view_label(family):
    """Turn a single-view family name into a display label, e.g. 'worldLeaf' -> 'World Leaf'."""
    return re.sub(r"(?<!^)(?=[A-Z])", " ", family).title()


def fetch_eplant_views(site, base_url, species_file, families):
    """Fetch view name → database name mappings for every "*eFP viewer" tab of one ePlant project.

    :param site: ePlant project key (e.g. ``'eplant_maize'``), used for overrides/error messages.
    :type site: str
    :param base_url: Base URL for the ePlant project.
    :type base_url: str
    :param species_file: Species XML filename stem for this project.
    :type species_file: str
    :param families: Family/tab names to check for this project.
    :type families: list[str]
    :returns: Dict mapping view display name to database name.
    :rtype: dict[str, str]
    """
    views = {}
    for family in families:
        names = get_eplant_view_names(base_url, family)
        if names is not None:
            # Dropdown exists (possibly with zero real entries left over).
            for display in names:
                folder = display.replace(" ", "")
                db = fetch_eplant_db(base_url, family, folder, species_file)
                if db:
                    views[display] = db
                else:
                    print(f"    No db found for {site}/{family}/{display}")
        else:
            # No dropdown -> at most one flat view directly under this family.
            db = fetch_eplant_db(base_url, family, None, species_file)
            if not db:
                db = EPLANT_DB_OVERRIDE.get((site, family))
            if db:
                views[_flat_view_label(family)] = db

    return views


def main():
    """Iterate over all eFP and ePlant sites, collect view-to-database mappings, and write output."""
    all_species_databases = {}

    for species, efp_url in EFP_SITES.items():
        print(f"[efp] Processing {species}...")
        views = fetch_view_databases(species, efp_url)
        if not views and species in _EFP_FALLBACK:
            print("  Live scrape failed -- using last-known-good fallback")
            views = _EFP_FALLBACK[species]
        if views:
            all_species_databases[f"efp_{species.replace(' ', '_')}"] = views
            print(f"  Found {len(views)} views")
        else:
            print("  No views found")

    for site, base_url in EPLANT_SITES.items():
        print(f"[eplant] Processing {site}...")
        species_file = EPLANT_SPECIES_FILE[site]
        families = EPLANT_FAMILIES[site]
        views = fetch_eplant_views(site, base_url, species_file, families)
        if views:
            all_species_databases[site] = views
            print(f"  Found {len(views)} views")
        else:
            print("  No views found")

    out_file = "species_databases.json"
    with open(out_file, "w") as f:
        json.dump(all_species_databases, f, indent=2)

    print(f"\nOutput written to {out_file}")


if __name__ == "__main__":
    main()
