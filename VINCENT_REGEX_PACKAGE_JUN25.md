# eFP Regex Validation Package for Vincent
**Source Branch:** endpoint-creation  
**Date:** June 25, 2026  
**For:** Production Database Validation

---

## 📦 What You're Getting

### 1. **Regex Reference JSON** ✅
- **File:** `data/efp_info/efp_regex_endpoint_creation.json`
- **Content:** All 20+ regex patterns extracted from endpoint-creation branch
- **Format:** Machine-readable with descriptions and examples
- **Coverage:** 20 species/validators

### 2. **Source Code** ✅
- **File:** `api/utils/bar_utils.py` (endpoint-creation branch)
- **Lines:** Individual validator functions for each species
- **Note:** Each function is independent, no consolidated dictionary

### 3. **Master Database JSON** ✅
- **File:** `data/efp_info/combined_master.json`
- **Content:** 48 species, 193 databases, SQL schemas
- **Source:** Generated from cleaned-endpoint branch

---

## 📋 Species/Regex Coverage

| Species | Regex Pattern | Function | Examples |
|---------|--------------|----------|----------|
| Arabidopsis | `^At[12345cm]g\d{5}.?\d?$` | `is_arabidopsis_gene_valid()` | At1g12345, At2g05123 |
| Rice | `^LOC_Os\d{2}g\d{5}(\.\d{1,2})?$` | `is_rice_gene_valid()` | LOC_Os01g01010, LOC_Os01g01010.1 |
| Maize | `^(AC[0-9]{6}\.[0-9]{1}_FG...)` | `is_maize_gene_valid()` | AC233276.1_FG001, GRMZM2G000010 |
| Poplar | `^POTRI\.\d{3}g\d{6}.?\d{0,3}$` | `is_poplar_gene_valid()` | POTRI.001g000010 |
| Grape | `^VIT_\d{0,3}\D\d{0,5}g\d{0,6}$` | `is_grape_gene_valid()` | VIT_00s0120g00060 |
| Tomato | `^Solyc\d\dg\d{6}(\.\d+)?$` | `is_tomato_gene_valid()` | Solyc01g000010, Solyc01g000010.1 |
| Soybean | `^((Glyma\d{1,3}g...)` | `is_soybean_gene_valid()` | Glyma06g47400, Glyma.06g000010 |
| Canola | `^Bna[AC]\d{2}g\d{5}[A-D]?$` | `is_canola_gene_valid()` | BnaC07g42830D |
| Sorghum | `^(Sobic.\d{0,5}G...)` | `is_sorghum_gene_valid()` | Sobic.001G000010 |
| Strawberry | `^FvH4_\d{1,3}g\d{1,8}$` | `is_strawberry_gene_valid()` | FvH4_1g00010 |
| Kalanchoe | `^Kaladp\d{1,10}s\d{1,10}$` | `is_kalanchoe_gene_valid()` | Kaladp000001s000001 |
| Cannabis | `^AGQN\d{0,10}$` | `is_cannabis_gene_valid()` | AGQN03000001 |
| Arachis | `^Adur\d{1,10}_comp...` | `is_arachis_gene_valid()` | Adur10000_comp0_c0_seq1 |
| Brassica rapa | `^BraA.{1,4}g\d{1,9}$` | `is_brassica_rapa_gene_valid()` | BraA01g000010 |
| Physcomitrella | `^Pp1s\d{1,8}_\d{1,8}V6...` | `is_physcomitrella_gene_valid()` | Pp1s9_70V6.1 |
| Phelipanche | `^OrAeBC5_\d{1,6}\.\d{1,3}$` | `is_phelipanche_gene_valid()` | OrAeBC5_9992.10 |
| Thellungiella | `^Thhalv\d+m\.g$\|^nXLOC...` | `is_thellungiella_gene_valid()` | Thhalv10000089m.g, nXLOC_003010 |
| Striga | `^StHeBC3_\d{1,6}\.\d{1,5}$` | `is_striga_gene_valid()` | StHeBC3_9993.10 |
| Triphysaria | `^TrVeBC3_\d{1,6}\.\d{1,3}$` | `is_triphysaria_gene_valid()` | TrVeBC3_9999.18 |
| Selaginella | `^Smo\d{1,8}$` | `is_selaginella_gene_valid()` | Smo402070 |

---

## ⚠️ Known Issues

### Tomato Database Mapping Question
Multiple tomato databases use the same regex:
- tomato
- tomato_ils
- tomato_ils2
- tomato_ils3
- tomato_meristem
- tomato_renormalized
- tomato_root
- tomato_root_field_pot
- tomato_s_pennellii
- tomato_seed
- tomato_shade_mutants
- tomato_shade_timecourse

**Action Needed:** Consult with Asher on whether these should have:
1. **Per-species mapping** (current): One regex for all tomato databases
2. **Per-database mapping**: Different regexes for each variant based on actual data

---

## 🎯 Production Validation Steps

### Step 1: Scan All Databases
Run regexes against production BAR database:
- Check `sample_data.data_probeset_id` columns
- Validate gene IDs against assigned regex patterns
- All 193 databases

### Step 2: Generate Coverage Report
```
Which databases: ✅ PASS (100% ID validation)
Which databases: ⚠️  WARNING (some IDs don't match)
Which databases: ❌ FAIL (significant ID mismatches)
```

### Step 3: Identify Edge Cases
- New ID formats not yet covered
- Per-database regex issues (especially tomato)
- Microarray vs RNA-seq format differences

### Step 4: Report Findings
Provide:
- List of databases needing regex updates
- Recommended new patterns for edge cases
- Decision on tomato database mapping approach

---

## 📁 Files Provided

```
endpoint-creation branch:
├── api/utils/bar_utils.py                    (Source code with validators)
└── data/efp_info/
    ├── efp_regex_endpoint_creation.json      (All regexes extracted & formatted)
    ├── combined_master.json                  (Database metadata)
    └── efp_regex_reference.json              (Alternative format)
```

---

## 💡 Usage Notes

Each regex in the JSON file includes:
- **regex:** The actual pattern to use
- **function:** Source function name from bar_utils.py
- **description:** What the regex validates
- **case_insensitive:** Whether regex uses re.I flag
- **examples:** Sample IDs that should match
- **notes:** Any special considerations

All regexes are extracted with original case-sensitivity settings from the functions.

---

## ✅ Next Steps

1. **Vincent:** Run production database scan
2. **Vincent → Asher:** Decide on tomato database mapping strategy
3. **Reena:** Update DATABASE_EFP_PROJECT mapping once decision is made
4. **Team:** Deploy validated regexes to production

---

**Contact:** Reena Obmina (rmobmina@gmail.com)  
**Questions:** About regex patterns, production validation, or architecture decisions
