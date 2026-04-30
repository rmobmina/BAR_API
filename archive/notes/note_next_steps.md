# Next Steps — A Guide

**Context:** This note is for whoever picks up this project after April 2026. It covers where
things were left off, what is production-ready, and what still needs to be done, in order
of priority.

---

## Current State (as of April 2, 2026)

The modernised gene expression API has been merged into the BAR codebase by system administrator
Asher Pasha and is **live on the development server**:

```
bar.utoronto.ca/api_dev/gene_expression/expression/klepikova/AT1G01010
```

The immediate next step is promoting it to the production BAR API at `bar.utoronto.ca/api/`,
pending final review by the team.

---

## Priority 1 — Production Deployment

Promote the dev API to production. This is already in Asher's hands. No code changes are needed;
this is a server-side step.

---

## Priority 2 — Gene-to-Probeset Conversion (14 Species)

This is the most impactful remaining technical task.

The API currently requires users to supply a **probeset ID** directly for 14 species. For
non-specialist users this is a barrier — they know their gene ID, not the microarray probe ID.
Arabidopsis already has a working lookup. The goal is to extend that to all supported species.

### Background: The ePlant Lookup Investigation

Vincent asked us to check what gene IDs ePlant uses for each species — because not every species
has its own ePlant viewer, and the ones that do give us a known, working gene ID to test against.
These were the ePlant test genes used:

| Species | Source | Gene ID |
|---------|--------|---------|
| Arabidopsis | AtGenExpress eFP | `AT5G60200` / DOF5.3, TMO6 |
| Maize | Plant eFP | `GRMZM2G158252` |
| Poplar | Plant eFP | `Potri.003G172600` |
| Tomato | Plant eFP | `Solyc04g014530` |
| Camelina | Plant eFP | `Csa01g001040` |
| Soybean | Plant eFP | `Glyma.06G202300` |
| Potato | Plant eFP | `PGSC0003DMG400000005` |
| Barley V3 | Gene Info Viewer | `HORVU.MOREX.r3.1HG0000030.V3` |
| Barley V1 | Gene Info Viewer | `HORVU1Hr1G000010` |
| Medicago | Gene Info Viewer | `Medtr8g043970` |
| Eucalyptus | Plant eFP | `Eucgr.A00001` |
| Rice | Plant eFP | `LOC_Os01g01080` |
| Willow | Gene Info Viewer | `SapurV1A.0035s0010` |
| Sunflower | Plant eFP | `HanXRQChr12g0384141` |
| Cannabis | Plant eFP | `AGQN03000001` |
| Wheat | Early Stages eFP (RNA-Seq) | `TraesCS1A01G000100` |
| Sugarcane | Leaf eFP | `Sh01_g000010` |

These were then compared against `sample_data_results.csv` (see `archive/test_data/`) to check
whether the database stores gene IDs directly or uses a different probeset format requiring
conversion.

### What Was Found

From `sample_data_results.csv`, the `data_probeset_id` column shows what format the database
actually stores. Key findings:

- **Barley** has two formats across databases: `HORVU.MOREX.r3.1HG*` (V3) in `barley_seed`
  and related RNA-Seq databases, and `HORVU0Hr1G*` (V1) in the older microarray databases.
  Any lookup table needs to handle both and route to the right database.
- **Tomato, Cannabis, Wheat** appear to store the gene ID directly (no conversion needed —
  the ePlant gene ID is the probeset ID).
- **Maize, Poplar, Soybean, Potato, Camelina, Rice, Medicago** likely need lookup tables.
  See `note_efp_lookup_table_verification.md` for the probe set identifiers confirmed via
  the eFP browser bottom sentence.

### What Still Needs to Be Done

For each of these species, the conversion pathway needs to be built:

1. Confirm which BAR database holds the gene-to-probeset mapping (check the existing
   `annotation` or `lookup` tables in the relevant database).
2. Add the lookup query to the API endpoint (follow how Arabidopsis does it in the current
   codebase).
3. Test with the ePlant gene IDs in the table above — these are known-good IDs to validate
   against.

The potato `G → P` identifier quirk (gene model `PGSC0003DMG*` → protein model `PGSC0003DMP*`)
is documented in `note_efp_lookup_table_verification.md` and still needs a decision: apply the
conversion to match eFP behaviour, or follow ePlant and use the gene ID directly.

---

## Priority 3 — Automate Mode B XML Validation in GitHub Actions

XML validation (`Mode B` — checking that XML view definitions match the underlying database
tables) currently has to be run manually. This should be automated as a scheduled GitHub Actions
workflow so any drift between XML config and database is caught before it reaches production.

Suggested schedule: run nightly or on each push to `dev`. Report failures as a GitHub Actions
annotation or Slack/email alert to the BAR team.

---

## Priority 4 — Connect to ePlant3 React Frontend

The API is ready. The remaining work is on the frontend side: update ePlant3 to point its
World eFP and Tissue eFP visualisation modules at the new endpoint paths instead of the legacy
CGI calls. Once that is done, ePlant3 users will see the full benefit of the latency improvements
(sub-6 ms local vs 800 ms+ legacy CGI — see `note_benchmarking_results.md`).
