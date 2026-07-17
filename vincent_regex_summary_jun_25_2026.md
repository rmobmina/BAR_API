# BAR eFP Regex Validation Summary for Vincent
**Date:** June 25, 2026  
**Prepared by:** Reena Obmina  
**For:** Vincent (Production Database Validation)

---

## Summary

All eFP project regexes have been consolidated and are ready for production validation. These regexes validate both **canonical gene IDs AND microarray probeset IDs** where applicable.

### Key Deliverables

#### 1. **Master JSON File** ✅
- **File:** `data/efp_info/combined_master.json`
- **Contents:**
  - 48 species with standardized scientific names
  - 193 databases with complete metadata
  - SQL column structure for each database's sample_data table
  - Schema variants (rnaseq_simple, legacy_microarray_projinfo)
  - Frontend usage mapping for each database
  - Sample groups and experimental design

#### 2. **Consolidated Regex Dictionary** ✅
- **File:** `api/utils/bar_utils.py` (lines 8-177)
- **Dictionary:** `EFP_PROJECT_REGEXES`
- **Total Patterns:** 50+ eFP project keys
- **Coverage:** All RNA-seq and microarray platforms

---

## Regex Coverage by Platform

### RNA-seq Projects (Gene Models)
- `efp_arabidopsis` - AGI gene IDs (At1g12345)
- `efp_barley` - HM/HV identifiers
- `efp_rice` - LOC_Os identifiers
- `efp_medicago` - Medtr identifiers
- `efp_poplar` - Potri identifiers
- `efp_soybean` - Glyma identifiers
- `efp_maize` - GRMZM identifiers
- `efp_wheat` - TraesCS identifiers
- And 20+ more species (apple, cacao, grape, potato, etc.)

### Microarray Projects (Probeset IDs)
- `efp_arabidopsis` - Also accepts Affymetrix probeset IDs (123456_at, 123456_s_at)
- `efp_barley` - HV/HM array probes
- `efp_rice` - Affymetrix Rice array
- `efp_medicago` - Mtr/Msa/Sme array probes
- `efp_poplar` - Ptp array probes

### Special Cases
- `efp_seedcoat` - Accepts CATMA probes (At\d{8}) + ATH1 Affymetrix
- `efp_arabidopsis_lipid` - Lipid species names (freeform text)
- `efp_maize_metabolite` - Metabolite names (freeform text)
- `efp_human` - Human probeset IDs (e.g., 202019_s_at)
- `efp` - Generic Arabidopsis validator (fallback)

---

## Known Issues & Decisions Needed

### ⚠️ Tomato Regex Issue

**Current Status:** One generic regex for all tomato databases
```
"efp_tomato": r"^(Solyc\d{2}g\d{6}\.?\d{0,3})$|^(TU\d{6})$"
```

**Database Mapping:**
```
DATABASE_EFP_PROJECT = {
    "tomato":                    "efp_tomato",
    "tomato_ils":                "efp_tomato",
    "tomato_ils2":               "efp_tomato",
    "tomato_ils3":               "efp_tomato",
    "tomato_meristem":           "efp_tomato",
    "tomato_renormalized":       "efp_tomato",
    "tomato_root":               "efp_tomato",
    "tomato_root_field_pot":     "efp_tomato",
    "tomato_s_pennellii":        "efp_tomato",
    "tomato_seed":               "efp_tomato",
    "tomato_shade_mutants":      "efp_tomato",
    "tomato_shade_timecourse":   "efp_tomato",
    "tomato_trait":              "efp_tomato_trait",  (special case)
}
```

**Problem:** Different tomato databases may have different gene ID formats or probesets.

**Options for Resolution:**
1. **Per-Species Approach (Current):** Keep one regex per species, validate all databases the same way
2. **Per-Database Approach:** Create individual regex patterns for each tomato database variant

**Action Needed:** Vincent will consult with Asher about which approach to take.

---

## What Reena Still Needs

1. **`efp_human` regex** ✅ Already exists in bar_utils.py (line 125)
   ```python
   "efp_human": r"^(\d{6,7}(_[xsa])?_at)$|^(\D{0,12}\d{0,12})$|^(\d{1,12})$"
   ```

2. **`efp` (generic) regex** ✅ Already exists in bar_utils.py (line 9)
   ```python
   "efp": (
       r"^([Aa][Tt][12345CM][Gg][0-9]{5})$"
       r"|^([0-9]{6}(_[xsfi])?_at)$"
       r"|^([0-9]{6,9})$"
       r"|^(AFFX-(BioB|BioC|BioDn|CreX|DapX|LysX|PheX|ThrX|TrpnX)-(3|5|M)_at)$"
       r"|^(AFFX-r2-(Bs|Ec|P1)-(dap|lys|phe|thr|bioB|bioC|bioD|cre)-(3|5|M)(_|_x_|_s_)at)$"
   )
   ```

---

## Production Database Validation Steps

### For Vincent:

1. **Run the regexes against production BAR database**
   - Validate gene IDs in `sample_data.data_probeset_id` column
   - Check all 193 databases for ID format compliance
   - Generate coverage report

2. **Identify any edge cases or failures**
   - Sample IDs that don't match regex patterns
   - New ID formats not yet covered
   - Per-database vs per-species mismatches (especially tomato)

3. **Generate validation report**
   - Which databases pass 100% validation
   - Which databases have edge cases
   - Recommendations for regex refinements

### Expected Outputs:
- ✅ `efp_regex_audit_prod.csv` (already in repo)
- ✅ `db_regex_coverage_report.csv` (already in repo)
- 📊 New validation report from production scan

---

## Files Ready for Production Use

```
api/utils/bar_utils.py
  ├── EFP_PROJECT_REGEXES dict (lines 8-177)
  └── is_efp_gene_valid() validator function

api/utils/gene_id_utils.py
  ├── DATABASE_EFP_PROJECT mapping
  └── validate_gene_for_database() function

data/efp_info/combined_master.json
  └── Single source of truth for all database metadata
```

---

## Next Steps

1. **Vincent:** Run production validation scan against all databases
2. **Vincent → Asher:** Consult on tomato database regex strategy (per-species vs per-database)
3. **Reena:** Once decision is made, update `DATABASE_EFP_PROJECT` mapping if needed
4. **Team:** Merge validated regex patterns into production codebase

---

## Contact

For questions about:
- **Regex patterns:** Reena Obmina (rmobmina@gmail.com)
- **Production validation:** Vincent
- **Architecture decision:** Asher

**Generated:** June 25, 2026
