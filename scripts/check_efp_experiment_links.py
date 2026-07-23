#!/usr/bin/env python3
"""
Walks every eFP browser view for every species in data/efp_info/combined_master.json
and checks whether each "To the Experiment" hyperlink shown in the expression-value
table actually resolves to something real, instead of erroring out or looping back
into the eFP browser itself.

For each species/instance:
  1. Load the bare efpWeb.cgi page (the browser's own default primary/secondary gene
     is pre-filled in the form, same as what a user sees on first load).
  2. For every dataSource ("view") offered in that page's <select>, submit it with
     the default gene(s) -- equivalent to clicking "Go".
  3. Pull the "Click Here for Table of Expression Values" output/efp-*.html table
     and extract every "To the Experiment" href, one per tissue/sample-group row.
  4. Resolve every *unique* experiment link with a real HTTP GET (concurrently --
     these are arbitrary external hosts, not bar.utoronto.ca, so parallel is fine)
     and classify the outcome.
  5. Write one CSV row per (species, view, tissue/sample-group).

Usage:
    python scripts/check_efp_experiment_links.py
    python scripts/check_efp_experiment_links.py --species poplar arabidopsis
    python scripts/check_efp_experiment_links.py --limit 5
    python scripts/check_efp_experiment_links.py --workers 15 --output scripts/results/efp_link_audit.csv
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MASTER_JSON = ROOT_DIR / "data" / "efp_info" / "combined_master.json"
DEFAULT_OUTPUT = ROOT_DIR / "scripts" / "results" / "efp_experiment_link_audit.csv"
DEFAULT_LOG = ROOT_DIR / "scripts" / "results" / "efp_experiment_link_audit_errors.log"

BASE = "https://bar.utoronto.ca"
USER_AGENT = "Mozilla/5.0 (compatible; BAR-API-link-audit/1.0; +https://bar.utoronto.ca)"

TO_THE_EXPERIMENT_ROW_RE = re.compile(
    r'<tr[^>]*>\s*<td>\d+</td>\s*<td>(.*?)</td>.*?href=["\']?([^"\'>\s]+)["\']?>To the Experiment',
    re.IGNORECASE | re.DOTALL,
)
TAG_RE = re.compile(r"<.*?>")
NOT_FOUND_TEXT_RE = re.compile(r"no (record|items?) found|does not exist|invalid accession", re.IGNORECASE)
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)


class LinkSweeper:
    """Runs the two-phase eFP link audit: fast discovery against bar.utoronto.ca,
    then concurrent classification of every unique external experiment link found.
    """

    def __init__(
        self,
        connect_timeout: float = 8,
        read_timeout: float = 12,
        hard_timeout: float = 18,
        delay: float = 0.25,
        workers: int = 10,
    ):
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.hard_timeout = hard_timeout
        self.delay = delay
        self.workers = workers

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        retry = Retry(total=0, connect=0, read=0, redirect=3)
        adapter = HTTPAdapter(max_retries=retry, pool_connections=workers * 2, pool_maxsize=workers * 2)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # A background pool used purely to enforce a hard wall-clock cap per request,
        # so one unresponsive host can never stall discovery or classification.
        self._bg_executor = concurrent.futures.ThreadPoolExecutor(max_workers=workers + 2)

        self.errors: list[str] = []
        self._log_fh = None

    # -- infrastructure -------------------------------------------------

    def log_error(self, msg: str) -> None:
        self.errors.append(msg)
        if self._log_fh is not None:
            self._log_fh.write(msg + "\n")
            self._log_fh.flush()

    def _bounded_request(self, method: str, url: str, **kwargs):
        kwargs.setdefault("timeout", (self.connect_timeout, self.read_timeout))
        fut = self._bg_executor.submit(getattr(self.session, method), url, **kwargs)
        try:
            return fut.result(timeout=self.hard_timeout)
        except concurrent.futures.TimeoutError:
            raise requests.exceptions.Timeout(f"hard wall-clock timeout after {self.hard_timeout}s")

    def _polite_get(self, url: str, **kwargs):
        time.sleep(self.delay)
        return self._bounded_request("get", url, **kwargs)

    # -- phase 1: discovery ----------------------------------------------

    def get_instance_meta(self, instance: str) -> dict | None:
        """Fetch the bare efpWeb.cgi page; return its default gene(s) and view list."""
        url = f"{BASE}/{instance}/cgi-bin/efpWeb.cgi"
        try:
            r = self._polite_get(url)
        except requests.exceptions.RequestException as e:
            self.log_error(f"{instance}: base page fetch failed: {e}")
            return None
        if r.status_code != 200:
            self.log_error(f"{instance}: base page HTTP {r.status_code}")
            return None
        html = r.text
        g1 = re.search(r'name="primaryGene"\s+value="([^"]*)"', html)
        g2 = re.search(r'name="secondaryGene"[^>]*value="([^"]*)"', html)
        opts = re.findall(r'<option\s+value="([^"]*)"', html)
        if not g1 or not opts:
            self.log_error(f"{instance}: could not parse default gene / dataSource options")
            return None
        return {
            "primaryGene": g1.group(1),
            "secondaryGene": g2.group(1) if g2 else "",
            "dataSources": opts,
        }

    def get_view_table(self, instance: str, view: str, gene1: str, gene2: str) -> list[tuple[str, str]] | None:
        """Submit "Go" for a given view; return [(tissue_or_sample_group, href), ...]."""
        url = (
            f"{BASE}/{instance}/cgi-bin/efpWeb.cgi"
            f"?dataSource={view}&mode=Absolute&primaryGene={gene1}"
            f"&secondaryGene={gene2}&grey_low=None&grey_stddev=None"
        )
        try:
            r = self._polite_get(url)
        except requests.exceptions.RequestException as e:
            self.log_error(f"{instance}/{view}: results page fetch failed: {e}")
            return None
        if r.status_code != 200:
            self.log_error(f"{instance}/{view}: results page HTTP {r.status_code}")
            return None
        m = re.search(r"output/(efp-[a-zA-Z0-9_]+\.html)", r.text)
        if not m:
            self.log_error(f"{instance}/{view}: no expression table link found (default gene may lack data for this view)")
            return None
        table_url = f"{BASE}/{instance}/output/{m.group(1)}"
        try:
            rt = self._polite_get(table_url)
        except requests.exceptions.RequestException as e:
            self.log_error(f"{instance}/{view}: table fetch failed: {e}")
            return None
        if rt.status_code != 200:
            self.log_error(f"{instance}/{view}: table HTTP {rt.status_code}")
            return None
        results = [
            (TAG_RE.sub("", tissue).strip(), href.strip())
            for tissue, href in TO_THE_EXPERIMENT_ROW_RE.findall(rt.text)
        ]
        if not results:
            self.log_error(f"{instance}/{view}: table had no 'To the Experiment' rows (may lack links)")
        return results

    def discover(self, instances: dict) -> list[list]:
        """Phase 1: for every instance/view, collect (species, instance, view, tissue, href|None, skip_reason|None)."""
        rows = []
        t0 = time.time()
        total = len(instances)
        for i, (instance, info) in enumerate(instances.items(), 1):
            species = info["species"]
            print(f"[discover {i}/{total}] {instance} ({species}) -- {time.time() - t0:.0f}s elapsed", file=sys.stderr, flush=True)
            meta = self.get_instance_meta(instance)
            if meta is None:
                rows.append([species, instance, "", "", None, "SKIPPED: could not load base page/default gene"])
                continue
            gene1, gene2 = meta["primaryGene"], meta["secondaryGene"]
            views = meta["dataSources"] if meta["dataSources"] else sorted(info["views"])
            for view in views:
                table = self.get_view_table(instance, view, gene1, gene2)
                if table is None:
                    rows.append([species, instance, view, "", None, "SKIPPED: no table/no data for default gene"])
                    continue
                if not table:
                    rows.append([species, instance, view, "", None, "No experiment links present in table"])
                    continue
                for tissue, href in table:
                    rows.append([species, instance, view, tissue, href, None])
        print(f"Discovery done in {time.time() - t0:.0f}s: {len(rows)} rows", file=sys.stderr, flush=True)
        return rows

    # -- phase 2: classification -----------------------------------------

    def classify_link(self, url: str) -> tuple[str, object, str, str, str]:
        """Resolve one experiment link and classify it. Returns (url, status, final_url, classification, note)."""
        parsed = urlparse(url if "://" in url else f"http://{url}")
        if not parsed.scheme or not parsed.netloc or url.strip() in ("#", ""):
            return url, "N/A", url, "Broken link", "href is empty/'#' or has no valid scheme -- dead link in the eFP table itself"

        try:
            r = self._bounded_request("get", url, allow_redirects=True, headers={"User-Agent": USER_AGENT})
            status = r.status_code
            final_url = r.url
            text = r.text[:5000] if r.text else ""
            final_parsed = urlparse(final_url)
            is_bar_host = final_parsed.netloc.replace("www.", "") == "bar.utoronto.ca"
            is_bare_path = final_parsed.path in ("", "/") and not final_parsed.query
            if status == 403:
                classification, note = "Blocked by target site", "HTTP 403 -- likely anti-bot protection on the target site, not necessarily a dead link"
            elif status >= 400:
                classification, note = "Error", f"HTTP {status}"
            elif is_bar_host and is_bare_path:
                classification, note = "Loops back to eFP homepage", "Link is/redirects to the bare bar.utoronto.ca homepage instead of a specific experiment"
            elif is_bar_host and "efpWeb.cgi" in final_url:
                classification, note = "Loops back to eFP page", "Redirected back into the eFP browser itself instead of an experiment"
            elif NOT_FOUND_TEXT_RE.search(text):
                classification, note = "Error", "Page loaded but reports record not found"
            else:
                classification = "Valid experiment"
                title_m = TITLE_RE.search(text)
                note = title_m.group(1).strip()[:120] if title_m else ""
        except requests.exceptions.ConnectionError as e:
            status, final_url = "N/A", url
            if "NameResolutionError" in str(e) or "nodename nor servname" in str(e):
                classification, note = "Error", "Could not resolve host -- link may contain a baked-in library-proxy prefix or a dead domain"
            else:
                classification, note = "Error", f"Connection failed: {e}"
        except requests.exceptions.RequestException as e:
            status, final_url, classification, note = "N/A", url, "Error", f"Request failed: {e}"
        return url, status, final_url, classification, note

    def classify_all(self, unique_links: list[str]) -> dict:
        results = {}
        t0 = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as pool:
            futs = {pool.submit(self.classify_link, url): url for url in unique_links}
            done = 0
            for fut in concurrent.futures.as_completed(futs):
                url, status, final_url, classification, note = fut.result()
                results[url] = (status, final_url, classification, note)
                done += 1
                if done % 25 == 0 or done == len(unique_links):
                    print(f"[classify {done}/{len(unique_links)}] -- {time.time() - t0:.0f}s elapsed", file=sys.stderr, flush=True)
        return results

    # -- orchestration ----------------------------------------------------

    def _classify_and_write(self, discovery_rows: list[list], csv_path: Path) -> None:
        unique_links = sorted({r[4] for r in discovery_rows if r[4]})
        print(f"{len(unique_links)} unique experiment links to classify", file=sys.stderr, flush=True)
        link_results = self.classify_all(unique_links)

        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with open(csv_path, "w", newline="") as csv_f:
            w = csv.writer(csv_f)
            w.writerow(["species", "efp_instance", "view", "tissue_or_sample_group", "experiment_link", "http_status", "final_url", "result"])
            for species, instance, view, tissue, href, skip_reason in discovery_rows:
                if not href:
                    w.writerow([species, instance, view, tissue, "", "", "", skip_reason])
                else:
                    status, final_url, classification, note = link_results.get(href, ("N/A", href, "Error", "not classified"))
                    w.writerow([species, instance, view, tissue, href, status, final_url, f"{classification}: {note}"])
        print(f"Done. {len(discovery_rows)} rows written to {csv_path}", file=sys.stderr, flush=True)

    def run(self, instances: dict, csv_path: Path, log_path: Path) -> None:
        """Full run: discover every view against bar.utoronto.ca, then classify every unique link found."""
        log_path.parent.mkdir(parents=True, exist_ok=True)
        self._log_fh = open(log_path, "w")
        discovery_rows = self.discover(instances)
        self._classify_and_write(discovery_rows, csv_path)
        self._log_fh.close()
        print(f"{len(self.errors)} issues logged to {log_path}", file=sys.stderr, flush=True)

    def reclassify(self, existing_csv_path: Path, csv_path: Path) -> None:
        """Re-run only the classification phase, reusing discovery rows already saved in an existing audit CSV.

        Useful after fixing/tuning classification logic -- avoids re-crawling bar.utoronto.ca (the slow part).
        """
        discovery_rows = []
        with open(existing_csv_path, newline="") as f:
            for row in csv.DictReader(f):
                href = row["experiment_link"] or None
                skip_reason = row["result"] if not href else None
                discovery_rows.append([row["species"], row["efp_instance"], row["view"], row["tissue_or_sample_group"], href, skip_reason])
        print(f"Loaded {len(discovery_rows)} discovery rows from {existing_csv_path}", file=sys.stderr, flush=True)
        self._classify_and_write(discovery_rows, csv_path)


def load_efp_instances(master_json_path: Path, species_filter: list[str] | None, instance_filter: list[str] | None) -> dict:
    """Build {instance_name: {species, views}} for every eFP frontend entry in combined_master.json."""
    master = json.loads(master_json_path.read_text())
    instances: dict = {}
    for db in master["databases"].values():
        for used_by in db.get("used_by", []):
            if used_by.get("frontend") != "efp":
                continue
            inst = used_by["instance"]
            instances.setdefault(inst, {"species": db.get("species"), "views": set()})
            instances[inst]["views"].add(used_by["view"])

    if species_filter:
        wanted = {s.lower() for s in species_filter}
        instances = {k: v for k, v in instances.items() if str(v["species"]).lower() in wanted}
    if instance_filter:
        wanted = set(instance_filter)
        instances = {k: v for k, v in instances.items() if k in wanted}
    return dict(sorted(instances.items()))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit every 'To the Experiment' link across all eFP browser views/species.")
    parser.add_argument("--master-json", type=Path, default=DEFAULT_MASTER_JSON, help="Path to combined_master.json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output CSV path")
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG, help="Path for the discovery error/skip log")
    parser.add_argument("--species", nargs="*", help="Only audit these species (matches combined_master.json species keys)")
    parser.add_argument("--instance", nargs="*", help="Only audit these eFP instance names (e.g. efp_poplar)")
    parser.add_argument("--limit", type=int, help="Only process the first N instances (useful for a quick test run)")
    parser.add_argument(
        "--reclassify-from",
        type=Path,
        help="Skip discovery entirely; reuse the (species/view/tissue/link) rows from this existing audit CSV "
        "and just re-run classification against them. Useful after changing classification logic.",
    )
    parser.add_argument("--workers", type=int, default=10, help="Concurrent workers for link classification (default: %(default)s)")
    parser.add_argument("--delay", type=float, default=0.25, help="Politeness delay between sequential requests to bar.utoronto.ca")
    parser.add_argument("--connect-timeout", type=float, default=8, help="Per-request connect timeout in seconds")
    parser.add_argument("--read-timeout", type=float, default=12, help="Per-request read timeout in seconds")
    parser.add_argument("--hard-timeout", type=float, default=18, help="Absolute per-request wall-clock cap in seconds")
    return parser.parse_args()


def main():
    args = parse_args()
    sweeper = LinkSweeper(
        connect_timeout=args.connect_timeout,
        read_timeout=args.read_timeout,
        hard_timeout=args.hard_timeout,
        delay=args.delay,
        workers=args.workers,
    )

    if args.reclassify_from:
        sweeper.reclassify(args.reclassify_from, args.output)
        return

    instances = load_efp_instances(args.master_json, args.species, args.instance)
    if args.limit:
        instances = dict(list(instances.items())[: args.limit])
    if not instances:
        print("No matching eFP instances found for the given filters.", file=sys.stderr)
        sys.exit(1)
    sweeper.run(instances, args.output, args.log)


if __name__ == "__main__":
    main()
