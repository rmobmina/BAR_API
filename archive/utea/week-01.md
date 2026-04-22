# UTEA Progress Report

**Name:** Reena Obmina  
**Project:** BAR API / ePlant Modernisation  
**Supervisor:** Vincent Lau & Nicholas Provart  
**Week:** 01 (April 13 - April 17)  

---

## 1. Overview

Project kick-off, initial planning, and research. First meeting held to align on scope and establish a proposal and timeline.

---

## 2. Work Completed

- Identified all CGI script locations used across ePlant
- Established proposal structure and 16-week project timeline

---

## 3. Technical Details

Met with Vincent and Dr. Provart remotely on Discord to discuss project scope, timeline, and expectations.

---

## 4. Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| Many CGI scripts still in use across the codebase | Prioritised by complexity; phased 16-week migration plan |

---

## 5. Results / Outcomes

- Gained understanding of CGI script history and the motivation for removing them
- Produced a full inventory of 9 CGI endpoints to migrate with file locations and complexity ratings

---

## 6. Next Steps

- Convert `/gene_information/gene_query` endpoint from POST to GET
- Implement autocomplete feature

---

## 7. Notes / Observations

A compiled list of the CGI endpoints that need to be migrated.


| # | Endpoint | File(s) | Complexity |
|---|----------|---------|------------|
| 1 | `idautocomplete.cgi` | `Species/arabidopsis/index.ts:13` | Low |
| 2 | `querygene.cgi` | `Species/arabidopsis/index.ts:22`, `InteractionsViewer/scripts/eventHandlers.tsx:58` | Low |
| 3 | `get_rank.php` | `views/eFP/Viewer/GeneDistributionChart.tsx:19` | Low |
| 4 | `chromosomeinfo.cgi` | `views/ChromosomeViewer/ChromosomeView.tsx:145` | Medium |
| 5 | `querygenesbyposition.cgi` | `views/ChromosomeViewer/Viewer/GeneList.tsx:45` | Medium |
| 6 | `groupsuba4.php` | `InteractionsViewer/scripts/loadSublocalizations.tsx:78`, `CellEFP/CellEFPDataObject/index.tsx:43` | Medium (POST) |
| 7 | `get_interactions_dapseq.py` | `views/InteractionsViewer/InteractionsView.tsx:236` | Medium |
| 8 | `plantefp.cgi` | `views/eFP/index.tsx:63` | High (chunked, progress callbacks) |
| 9 | `eplant_navigator_service.cgi` | `views/NavigatorView/NavigatorView.tsx:995` | High (multi-species tree) |

---

### 16-Week Roadmap

**Phase 1 — Foundational Work (Weeks 1–4)**

- **Wk 1–2:** `idautocomplete.cgi` — `Species/arabidopsis/index.ts:13`. Simple GET, returns gene ID suggestions. *(finishing this week)*
- **Wk 3–4:** `querygene.cgi` — two call sites (`index.ts:22` and `eventHandlers.tsx:58`). Wire up REST replacement in both and verify tooltip generation still works in InteractionsViewer.

**Phase 2 — Chromosome Viewer (Weeks 5–8)**

- **Wk 5–6:** `chromosomeinfo.cgi` — `ChromosomeViewer/ChromosomeView.tsx:145`. Returns chromosome structural data; test that the diagram renders correctly.
- **Wk 7–8:** `querygenesbyposition.cgi` — `ChromosomeViewer/Viewer/GeneList.tsx:45`. Depends on chromosome data; do after chromosomeinfo. Test gene list populating on chromosome region click.

**Phase 3 — Expression & Ranking (Weeks 9–11)**

- **Wk 9–10:** `get_rank.php` — `eFP/Viewer/GeneDistributionChart.tsx:19`. Single call returning a percentile; verify distribution chart renders correctly after.
- **Wk 11:** Integration testing of Phases 1–3, catch regressions, supervisor check-in.

**Phase 4 — Interactions & Localization (Weeks 12–14)**

- **Wk 12–13:** `groupsuba4.php` — two call sites (`loadSublocalizations.tsx:78` and `CellEFPDataObject/index.tsx:43`). Only POST endpoint in the list; verify subcellular localisation overlays in both the Interactions and Cell EFP views.
- **Wk 14:** `get_interactions_dapseq.py` — `InteractionsViewer/InteractionsView.tsx:236`. DAP-seq interaction graph data; test that the force-directed graph still loads.

**Phase 5 — Heavy lifters (Weeks 15–16)**

- **Wk 15–16:** `plantefp.cgi` — `views/eFP/index.tsx:63`. Chunked fetch with progress callbacks — most complex call in the codebase. Sample batching logic will need rethinking for the new API.
- `eplant_navigator_service.cgi`? Multi-species, returns a nested tree (`NavigatorView.tsx:995`). May run into Week 17+ or be scoped separately.

---

### CGI (Common Gateway Interface)

What is CGI?
- CGI = Common Gateway Interface
- Early web standard for connecting web servers to programs/scripts
- Flow:
  - Server receives request
  - Launches a new process
  - Passes data via environment variables or stdin
  - Script outputs response to stdout
- Commonly used with:
  - Perl
  - Python
  - PHP

Why CGI Is Being Deprecated/Replaced?
- Inefficient:
  - New process per request makes it slow and resource-heavy
- Poor scalability:
  - Does not handle high traffic well
- Outdated architecture:
  - No persistent state or connection handling
- Harder to maintain:
  - Requires manual request and response parsing
- Replaced by:
  - Persistent application servers
  - Structured frameworks with routing, middleware, and APIs

As for CGI in Python...
- `cgi` module:
  - Deprecated in Python 3.11
  - Removed in Python 3.13
- Part of PEP 594 (removal of outdated standard library modules)
- Also deprecated:
  - `CGIHTTPRequestHandler`
  - `http.server --cgi`
- Reason:
  - Shift toward modern web architectures

---

Perl
- CGI is not removed from the language
- `CGI.pm` module still exists and is maintained
- Still usable but considered legacy
- Modern Perl applications often use:
  - FastCGI
  - mod_perl
  - Web frameworks (e.g., Dancer, Mojolicious)

PHP
- CGI is still supported via CGI SAPI (`php-cgi`)
- Not commonly used in modern deployments
- Standard modern setup:
  - PHP-FPM (FastCGI Process Manager)
- Key idea:
  - CGI exists but is not the preferred architecture