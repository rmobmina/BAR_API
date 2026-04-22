# UTEA Progress Report

**Name:** Reena Obmina  
**Project:** BAR API / ePlant Modernisation  
**Supervisor:** Vincent Lau & Nicholas Provart  
**Week:** 02 (April 20 - April 24)  

---

## 1. Overview

This week focused on two tasks: converting the `gene_query` endpoint from POST to GET, and implementing a new `id_autocomplete` endpoint to replace the legacy `idautocomplete.cgi` script.

---

## 2. Work Completed

- Implemented:
  - `GET /gene_information/id_autocomplete` is a new endpoint replacing `idautocomplete.cgi`
  - `AgiNames` SQLAlchemy model in `api/models/eplant2.py` (table was used by the CGI but had no Python representation in the BAR API)
- Fixed:
  - SQL injection vulnerability in the CGI's raw string query construction — replaced with SQLAlchemy parameterized queries
  - Broken limit math in the CGI (`LIMIT -15` crash) which is fixed by tracking remaining budget across all three queries
  - (`except: print("{}")`) is replaced with proper HTTP 400 responses
  - O(n²) becomes O(1)
- Converted:
  - `gene_query` endpoint from POST to GET
- Added:
  - `agi_names` table definition and sample rows to `config/databases/eplant2.sql` for test coverage
  - 9 test cases for `id_autocomplete` in `tests/resources/test_gene_information.py`

---

## 3. Technical Details

**Tools / languages used:** Python, Flask-RESTX, SQLAlchemy, SQLite (test), pytest

**`gene_query` POST → GET conversion:**  
GET is more appropriate here because the endpoint reads data and changes nothing. POST requests also cannot be bookmarked or called directly from a browser address bar. The conversion involved switching the decorator from `@gene_information.expect(...)` with a JSON body to `@gene_information.param(...)` with query string arguments, and reading values from `request.args` instead of `request.get_json()`.

**`id_autocomplete` design:**  
The endpoint queries three tables in priority order, `agi_alias`, `agi_names`, then `tair10_gff3` as a fallback. Then it returns up to `limit` results (default 15, max 50). A single `seen_agis` Python set spans all three queries to prevent duplicate AGIs in the response. The remaining capacity is recalculated before each query so the limit is never exceeded and no negative `LIMIT` values are generated.

**Key design decisions:**
- Minimum term length of 2 characters enforced before any DB query runs, preventing expensive full-table scans
- Output changed from flat strings (`"AT1G01010/ANAC001"`) to structured objects (`{"agi": "AT1G01010", "match": "ANAC001"}`) and the `match` field identifies which alias or name triggered the hit, which is more useful for UI highlighting
- `limit` is an optional query parameter (1–50) rather than hardcoded, giving callers control over response size

**Files touched:**

| File | Change |
|---|---|
| `api/resources/gene_information.py` | Added `IdAutocomplete` resource class; converted `gene_query` to GET |
| `api/models/eplant2.py` | Added `AgiNames` model |
| `config/databases/eplant2.sql` | Added `agi_names` table schema and seed data |
| `tests/resources/test_gene_information.py` | Added `test_id_autocomplete` with 9 test cases |

---

## 4. Challenges & Solutions

| Challenge | Solution |
|---|---|
| `agi_names` table used by the CGI but not modelled in the BAR API | Added `AgiNames` SQLAlchemy model; inferred column structure (`agi`, `name`) from the CGI's SQL, needs confirmation that production schema matches |
| CGI's limit math produced `LIMIT -15`, crashing silently | Track `len(results)` across all three queries; pass `limit - len(results)` to each subsequent query |
| Stale SQLite test mirror did not include new `agi_names` table | Deleted cached `eplant2.db` to force rebuild from updated `eplant2.sql` on next test run |
| CGI's deduplication only checked the third query against the first two, using a slow prefix scan | Replaced with a `seen_agis` set populated from all three queries; exact-match lookup, O(1) per result |

---

## 5. Results / Outcomes

- All 8 existing `gene_information` tests continue to pass
- 9 new tests added for `id_autocomplete`, all passing
- SQL injection vulnerability in `idautocomplete.cgi` eliminated
- Broken `LIMIT -15` crash fixed
- Output changed to structured JSON objects, consistent with the rest of the BAR API response format

---

## 6. Next Steps

- Confirm that `agi_names` exists in production `eplant2` DB and that column names (`agi`, `name`) match
- Check whether ePlant frontend expects the old `"AT1G01010/ANAC001"` flat string format or can consume the new `{"agi", "match"}` objects

---

## 7. Notes / Observations