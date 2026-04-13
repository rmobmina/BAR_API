# Gene ID Lookup Requirements for ePlant Species

Vincent asked us to check what gene IDs ePlant uses for each species, then cross-reference
them against `sample_data_results.csv` to determine whether the database stores that gene ID directly
or requires a conversion. The test genes below are the ones used in ePlant (Plant eFP / Gene Info
Viewer / AtGenExpress eFP).

Cross-reference source: `archive/test_data/sample_data_results.csv`

---

## Test Genes (from ePlant)

| Species | ePlant Source | Test Gene ID |
|---------|--------------|--------------|
| Arabidopsis | AtGenExpress eFP | `AT5G60200` (DOF5.3 / TMO6) |
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

---

## Conversion Required

These databases do NOT store the ePlant gene ID format directly.

---

### Arabidopsis — `atgenexp*` databases
- **ePlant ID:** `AT5G60200`
- **Stored format:** `*_at` (ATH1 Affymetrix probeset, e.g. `AFFX-BioB-M_at`, `261585_at`)
- **Conversion:** AGI → ATH1 probeset
- **Status:** Already implemented via `EFPDataService.agi_to_probset` — use this as the reference for all other species.

---

### Maize — multiple databases, each with a different format
- **ePlant ID:** `GRMZM2G158252` (B73 v2)
- **Databases and what they actually store (confirmed from sample data):**

| Database | Stored format | Example |
|----------|--------------|---------|
| `maize_gdowns` | GenBank accession probesets | `AB004882_at` |
| `maize_RMA_linear` | Contig-based probesets | `AC148152.3_FGT005` |
| `maize_buell_lab` | B73 v4 gene IDs | `Zm00001d000001` |

- **Status:** Three separate lookup tables needed — one per format. The `GRMZM*` → each target format is a non-trivial mapping.
- **Note:** `maize_iplant`, `maize_leaf_gradient`, `maize_early_seed`, and others also present in the data — spot-check their formats before implementing.

---

### Poplar — depends on which database
- **ePlant ID:** `Potri.003G172600`
- **Databases:**
  - `poplar` (Affymetrix): stores `PtpAffx.*_at` probesets (confirmed via eFP browser bottom sentence: `PtpAffx.200227.1.S1_s_at`). Needs `Potri.* → PtpAffx.*_at` conversion — likely two-step via `grail3.*`.
  - `poplar_hormone`: stores `Potri.*` directly (confirmed: `Potri.001G000200`). **No conversion needed** for this database.
- **Status:** Mixed — `poplar` needs a lookup; `poplar_hormone` does not.

---

### Soybean — all databases
- **ePlant ID:** `Glyma.06G202300` (new Wm82.a4 format, dot notation, uppercase G)
- **Stored format (confirmed):**
  - `soybean`, `soybean_severin`: `Glyma0021s00410` (old format, no dot, lowercase g)
  - `soybean_embryonic_development`: `Glyma14g36566` (old format, no dot)
- **Conversion:** new `Glyma.XxG*` → old `GlymaXxg*` / `GlymaXxs*`
- **Status:** Lookup table needed. Conversion involves gene model version reconciliation, not just string formatting.

---

### Rice — `rice_mas`, `rice_rma` only
- **ePlant ID:** `LOC_Os01g01080`
- **Stored format:** Affymetrix probesets (confirmed AFFX controls present; real probesets are `Os.*_at` format based on eFP browser)
- **Direct-query databases (no conversion needed):** `rice_drought_heat_stress` stores `LOC_Os*` directly.
- **Status:** Lookup needed for `rice_mas` / `rice_rma` only. RNA-Seq rice databases are direct.

---

### Medicago — depends on database
- **ePlant ID:** `Medtr8g043970`
- **Databases:**
  - `medicago_mas`, `medicago_rma`: Affymetrix probesets (`Mtr.*_at` format). Conversion needed.
  - `medicago_seed`: stores `Medtr_v1_000001` (old genome version). Confirmed from sample data. `Medtr8g*` → `Medtr_v1_*` version mapping needed.
- **Status:** Lookup needed for all three databases, each with a different target format.

---

### Barley — `barley_mas`, `barley_rma`
- **ePlant ID:** `HORVU.MOREX.r3.1HG0000030.V3` (V3) / `HORVU1Hr1G000010` (V1)
- **Stored format in `barley_mas` / `barley_rma`:** `1200459_Reg_88-1740_at` (Affymetrix chip probesets). Confirmed from sample data.
- **Status:** Lookup table needed to map HORVU gene IDs to Affymetrix probeset IDs.

---

## Direct Query (No Conversion Needed)

These databases store the gene ID in the same format as the ePlant input. Confirmed from `sample_data_results.csv`.

| Species | Database(s) | ePlant ID format | Stored format | Confirmed |
|---------|-------------|-----------------|---------------|-----------|
| Eucalyptus | `eucalyptus` | `Eucgr.A00001` | `Eucgr.A00001` | ✓ exact match |
| Wheat | `wheat`, `wheat_*` | `TraesCS1A01G000100` | `TraesCS1A01G000100` | ✓ exact match |
| Sugarcane | `sugarcane_leaf` | `Sh01_g000010` | `Sh01_g000010` | ✓ exact match |
| Cannabis | `cannabis` | `AGQN03*` | `AGQN03*` | ✓ format match |
| Tomato (ILs) | `tomato_ils`, `tomato_ils2` | `Solyc*` | `Solyc*` | ✓ format match |
| Barley V1 | `barley_spike_meristem` | `HORVU0Hr1G000010` | `HORVU0Hr1G000010` | ✓ exact match |
| Potato | `potato_dev`, `potato_stress` | `PGSC0003DMG*` | `PGSC0003DMG*` | ✓ DMG stored directly |
| Barley V3* | `barley_seed`, `barley_spike_meristem_v3` | `HORVU.MOREX.r3.*HG*.V3` | `HORVU.MOREX.r3.*HG*.1` | ⚠ suffix differs |
| Poplar hormone | `poplar_hormone` | `Potri.*` | `Potri.*` | ✓ direct |
| Rice (RNA-Seq) | `rice_drought_heat_stress` | `LOC_Os*` | `LOC_Os*` | ✓ direct |

*Barley V3: the database stores `.1` suffix (e.g. `HORVU.MOREX.r3.1HG0000030.1`) while ePlant uses `.V3` suffix.
Strip the suffix and match on the base ID, or normalise on input.

---

## Needs Investigation

These species have a mismatch between the ePlant gene ID format and what the database actually stores,
but the correct lookup approach is not yet confirmed.

| Species | ePlant ID format | Stored format (from sample data) | Question |
|---------|-----------------|----------------------------------|----------|
| **Willow** | `SapurV1A.0035s0010` | `comp93760_c2_seq23` (Trinity assembly) | Is the data from an older transcriptome assembly? Does a SapurV1A → Trinity mapping exist? |
| **Sunflower** | `HanXRQChr12g0384141` | `Ha1_00043026` | Different genome version or assembly — is there a mapping file available? |
| **Camelina** | `Csa01g001040` (genome v6) | `Csa00382s020.1` (older assembly) | Version mapping between Csa genome releases needed — check BAR annotation tables |
| **Tomato (Rose Lab Atlas)** | `Solyc*` | `TU000001` (Tomato Unigene probesets) | Affymetrix Tomato GeneChip uses TU* IDs — lookup table from Solyc → TU needed. ILs databases (`tomato_ils*`) use Solyc directly and are fine. |

---

## Summary

| Status | Species / Databases |
|--------|-------------------|
| Already implemented | Arabidopsis (atgenexp*) |
| Direct query, confirmed | Eucalyptus, Wheat, Sugarcane, Cannabis, Tomato ILs, Barley V1, Potato, Poplar hormone, Rice RNA-Seq |
| Minor normalisation only | Barley V3 (strip `.V3` suffix → `.1`) |
| Lookup table needed | Maize (3 formats), Poplar Affymetrix, Soybean (version mismatch), Rice mas/rma, Medicago (3 formats), Barley mas/rma |
| Needs investigation first | Willow, Sunflower, Camelina, Medicago seed, Tomato Rose Lab Atlas |
