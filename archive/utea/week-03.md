# UTEA Progress Report

**Name:** Reena Obmina  
**Project:** BAR API / ePlant Modernisation  
**Supervisor:** Vincent Lau & Nicholas Provart  
**Week:** 03 (April 27 - May 1)  

---

## 1. Overview

This week focused on three tasks: updating the `id_autocomplete` endpoint based on feedback from Vincent, implementing a new `gene_density` endpoint to replace `genedensity.cgi`, and comprehensive testing of the gene expression endpoint across all species databases.

---

## 2. Work Completed

- Updated:
  - `GET /gene_information/id_autocomplete`, removed the `limit` query parameter as suggested by Vincent; response size is now fixed at 15 results
- Implemented:
  - `GET /gene_density`, new endpoint replacing `genedensity.cgi`, used by Eplant's ChromosomeView to colour chromosomes by gene density
- Tested:
  - Gene expression endpoint manually tested across all species databases one at a time via Swagger UI
  - Findings compiled and sent by email to Asher, Vincent, and Dr. Provart

---

## 3. Technical Details

**Tools / languages used:** Python, Flask-RESTX, SQLAlchemy, SQLite (test), pytest

**`id_autocomplete` update:**  
Vincent suggested removing the `limit` parameter to simplify the API surface — callers do not need to control the result size for an autocomplete widget. The parameter was removed from the route decorator, request parsing, and validation logic. All three internal SQL queries now hardcode `15` directly.

**`gene_density` design:**  
The CGI fetched every gene row and counted bin membership in Python (one iteration per gene, plus an inner loop for any gene spanning multiple bins). The new endpoint replaces this with two SQL queries:

1. **Aggregated query** — `SELECT SUBSTR(geneId,3,1), FLOOR(Start/bin_size), COUNT(*) … GROUP BY …` with a `WHERE FLOOR(Start/bin_size) = FLOOR(End/bin_size)` filter. This handles ≥98% of genes at typical zoom levels with a single grouped result set.
2. **Multi-bin query** — fetches only the rare genes whose start and end fall in different bins, and counts each one into every bin it spans. Preserves exact parity with the original CGI output.

The chromosome is extracted from `geneId` character 3 (e.g. `AT1G01010` → `'1'`), matching the original CGI logic. The response wraps the array in the standard BAR API envelope (`wasSuccessful`, `data`).

**Files touched:**

| File | Change |
|---|---|
| `api/resources/gene_information.py` | Removed `limit` parameter from `IdAutocomplete` |
| `tests/resources/test_gene_information.py` | Removed limit-related test cases |
| `api/resources/gene_density.py` | New file — `GeneDensity` resource |
| `api/__init__.py` | Registered `gene_density` namespace |
| `tests/resources/test_gene_density.py` | New file — 8 test cases |

---

## 4. Challenges & Solutions

| Challenge | Solution |
|---|---|
| CGI looped over all ~27 000 gene rows in Python | Replaced with a `GROUP BY` SQL query; only the rare multi-bin genes (~1–2%) require individual rows |
| `SUBSTRING()` is MySQL-only; SQLite uses `SUBSTR()` | Used `func.substr()` via SQLAlchemy so the same code runs against both backends |
| Many gene expression databases returned 500 errors or probeset-lookup 404s for standard gene IDs | Documented each case in the observations table below and flagged to the team |

---

## 5. Results / Outcomes

- All existing tests continue to pass
- 8 new tests added for `gene_density`, all passing
- `id_autocomplete` simplified per Vincent's feedback with no regressions
- Gene expression testing findings shared with Asher, Vincent, and Dr. Provart by email

---

## 6. Next Steps

- Convert `querygenebyidentifier.cgi` to a BAR API endpoint

---

## 7. Notes / Observations

Gene expression endpoint tested across all species databases. Results below. "NONE" in the Error column means the request succeeded with data returned.

| Species | Dataset | Database | Error | Test ID(s) |
|---|---|---|---|---|
| actinidia | Bud_Development | actinidia_bud_development | NONE | Acc00001.1 |
| actinidia | Flower_Fruit_Development | actinidia_flower_fruit_development | NONE | Acc00001.1 |
| actinidia | Postharvest | actinidia_postharvest | NONE | Acc00001.1 |
| actinidia | Vegetative_Growth | actinidia_vegetative_growth | NONE | Acc00001.1 |
| arabidopsis | Abiotic_Stress | atgenexp_stress | 500 Internal Server Error | 261585_at / At1g01010 |
| arabidopsis | Abiotic_Stress_II | atgenexp_stress | 500 Internal Server Error | 261585_at / At1g01010 |
| arabidopsis | Biotic_Stress | atgenexp_pathogen | 500 Internal Server Error | 261585_at / At1g01010 |
| arabidopsis | Biotic_Stress_II | atgenexp_pathogen | 500 Internal Server Error | 261585_at / At1g01010 |
| arabidopsis | Chemical | atgenexp_hormone | 500 Internal Server Error | 261585_at / At1g01010 |
| arabidopsis | DNA_Damage | dna_damage | NONE | At1g01010 |
| arabidopsis | Development_RMA | atgenexp | 500 Internal Server Error | 261585_at / At1g01010 |
| arabidopsis | Developmental_Map | atgenexp_plus | 500 Internal Server Error | 261585_at / At1g01010 |
| arabidopsis | Developmental_Mutants | atgenexp_plus | 500 Internal Server Error | 261585_at / At1g01010 |
| arabidopsis | Embryo | embryo | NONE | At1g01010 |
| arabidopsis | Germination | germination | NONE | AT1G01010 |
| arabidopsis | Guard_Cell | guard_cell | 500 Internal Server Error | 261585_at / At1g01010 |
| arabidopsis | Gynoecium | gynoecium | NONE | AT1G01010 |
| arabidopsis | Hormone | atgenexp_hormone | 500 Internal Server Error | 261585_at / At1g01010 |
| arabidopsis | Klepikova_Atlas | klepikova | NONE | AT1G01010 |
| arabidopsis | Lateral_Root_Initiation | lateral_root_initiation | 500 Internal Server Error | 261585_at / At1g01010 |
| arabidopsis | Light_Series | light_series | 500 Internal Server Error | 261585_at / At1g01010 |
| arabidopsis | Natural_Variation | arabidopsis_ecotypes | 500 Internal Server Error | 261585_at / At1g01010 |
| arabidopsis | Regeneration | meristem_db | 500 Internal Server Error | 261585_at / At1g01010 |
| arabidopsis | Root | root | 500 Internal Server Error | 261585_at / At1g01010 |
| arabidopsis | Root_II | root | 500 Internal Server Error | 261585_at / At1g01010 |
| arabidopsis | Seed | seed_db | 500 Internal Server Error | 261585_at / At1g01010 |
| arabidopsis | Shoot_Apex | shoot_apex | NONE | At1g01010 |
| arabidopsis | Silique | silique | NONE | At1g01010 |
| arabidopsis | Single_Cell | single_cell | NONE | At1g01010 |
| arabidopsis | Tissue_Specific | atgenexp_plus | 500 Internal Server Error | 261585_at / At1g01010 |
| arabidopsis | Seed_Coat | seedcoat | 400 Invalid arabidopsis gene ID / 404 No expression data found | A000011_01 / At1g17665 |
| arachis | Arachis_Atlas | arachis | NONE | Adur10000_comp0_c0_seq1 |
| barley | barley_mas | barley_mas | 404 Probeset lookup not available — supply probeset ID directly | Contig3045_at / AK364622 |
| barley | barley_rma | barley_rma | 404 Probeset lookup not available — supply probeset ID directly | Contig3045_at / AK364622 |
| brachypodium | Brachypodium_Atlas | brachypodium | NONE | Bradi4g05940.1 |
| brachypodium | Brachypodium_Grains | brachypodium_grains | NONE | Bradi4g05940.1 |
| brachypodium | Brachypodium_Spikes | brachypodium_Bd21 | NONE | Bradi4g05940.1 |
| brachypodium | Photo_Thermocycle | brachypodium_photo_thermocycle | NONE | Bradi4g05940.1 |
| brassica rapa | Embryogenesis | brassica_rapa | NONE | BraA01g000010 |
| cacao ccn | Developmental_Atlas | cacao_developmental_atlas | NONE | CCN-51_Chr0v1_20099 |
| cacao ccn | Drought_Diurnal_Atlas | cacao_drought_diurnal_atlas | NONE | CCN-51_Chr0v1_20099 |
| cacao sca | Developmental_Atlas | cacao_developmental_atlas_sca | NONE | SCA-6_Chr1v1_00001 |
| cacao sca | Drought_Diurnal_Atlas | cacao_drought_diurnal_atlas_sca | NONE | SCA-6_Chr1v1_00001 |
| cacao sca | Meristem_Atlas | cacao_meristem_atlas_sca | NONE | SCA-6_Chr1v1_00001 |
| cacao sca | Seed_Atlas | cacao_seed_atlas_sca | NONE | SCA-6_Chr1v1_00001 |
| cacao tc | Cacao_Infection | cacao_infection | NONE | Tc01v2_g000010 |
| cacao tc | Cacao_Leaf | cacao_leaf | NONE | Tc01v2_g000010 |
| camelina | Developmental_Atlas_FPKM | camelina | 404 No expression data found for AT4G13770 | AT4G13770 / Csa00382s010.1 |
| camelina | Developmental_Atlas_TPM | camelina_tpm | NONE | Csa00382s010.1 |
| cannabis | Cannabis_Atlas | cannabis | NONE | AGQN03000001 |
| canola | Canola_Seed | canola_seed | NONE | BnaA01g00010D |
| eutrema | Eutrema | thellungiella_db | 400 Invalid arabidopsis gene ID / 404 Probeset lookup not available | Thhalv10000089m.g / AT2G21470 |
| grape | grape_developmental | grape_developmental | 400 Invalid grape gene ID / 404 Probeset lookup not available | CHRUN_JGVV120_4_T01 / VIT_00s0120g00060 |
| kalanchoe | Light_Response | kalanchoe | NONE | Kaladp0001s0001 |
| little millet | Life_Cycle | little_millet | NONE | TRINITY_DN0_c0_g1_i15 |
| lupin | LCM_Leaf | lupin_lcm_leaf | NONE | Luan_Oskar_Trin_282785 |
| lupin | LCM_Pod | lupin_lcm_pod | NONE | Luan_Oskar_Trin_282785 |
| lupin | LCM_Stem | lupin_lcm_stem | NONE | Luan_Oskar_Trin_282785 |
| lupin | Whole_Plant | lupin_whole_plant | NONE | Luan_Oskar_Trin_282785 |
| maize | Downs_et_al_Atlas | maize_gdowns | 404 Probeset lookup not available | Zm006552_s_at / GRMZM2G083841_T01 |
| maize | Early_Seed | maize_early_seed | NONE | Zm00001d046170 |
| maize | Embryonic_Leaf_Development | maize_embryonic_leaf_development | NONE | Zm00001d046170 |
| maize | Hoopes_et_al_Atlas | maize_buell_lab | NONE | Zm00001d046170 |
| maize | Hoopes_et_al_Stress | maize_buell_lab | NONE | Zm00001d046170 |
| maize | Maize_Kernel | maize_early_seed | NONE | Zm00001d046170 |
| maize | Maize_Root | maize_root | NONE | GRMZM2G083841 / GRMZM2G083841_T01 |
| maize | Sekhon_et_al_Atlas | maize_RMA_linear | 404 No expression data found for GRMZM2G083841 | GRMZM2G083841_T01 |
| maize | Tassel_and_Ear_Primordia | maize_ears | NONE | GRMZM2G083841 / GRMZM2G083841_T01 |
| maize | maize_iplant | maize_iplant | NONE | GRMZM2G083841 / GRMZM2G083841_T01 |
| maize | maize_leaf_gradient | maize_leaf_gradient | NONE | GRMZM2G083841 / GRMZM2G083841_T01 |
| maize | maize_rice_comparison | maize_rice_comparison | 404 No expression data found for Zm00001d046170 | Zm00001d046170 (also fails on eFP browser) |
| mangosteen | Aril_vs_Rind | mangosteen_aril_vs_rind | NONE | DN1 |
| mangosteen | Callus | mangosteen_callus | NONE | DN1 |
| mangosteen | Diseased_vs_Normal | mangosteen_diseased_vs_normal | NONE | DN1 |
| mangosteen | Fruit_Ripening | mangosteen_fruit_ripening | NONE | DN1 |
| mangosteen | Seed_Development | mangosteen_seed_development | NONE | DN1 |
| mangosteen | Seed_Germination | mangosteen_seed_germination | NONE | DN1 |
| medicago | medicago_mas | medicago_mas | 404 Probeset lookup not available | Mtr.25884.1.S1_at / Medtr1g102430 |
| medicago | medicago_rma | medicago_rma | 404 Probeset lookup not available | Mtr.25884.1.S1_at / Medtr1g102430 |
| medicago | medicago_seed | medicago_seed | 404 No expression data found for MEDTR1G102430 | Medtr_v1_007681 / MEDTR1G102430 |
| poplar | Poplar | poplar | 400 Invalid poplar gene ID | PtpAffx.200227.1.S1_s_at / grail3.0047015901 |
| poplar | PoplarTreatment | poplar | 400 Invalid poplar gene ID | PtpAffx.200227.1.S1_s_at / grail3.0047015901 |
| potato | Potato_Developmental | potato_dev | 404 Probeset lookup not available | PGSC0003DMG400000005 / PGSC0003DMP400000011 |
| potato | Potato_Stress | potato_stress | 404 Probeset lookup not available | PGSC0003DMG400000005 / PGSC0003DMP400000011 |
| rice | rice_drought_heat_stress | rice_drought_heat_stress | NONE | LOC_Os01g01080 |
| rice | rice_leaf_gradient | rice_leaf_gradient | NONE | LOC_Os01g01080 |
| rice | rice_maize_comparison | rice_maize_comparison | NONE | LOC_Os01g01080 |
| rice | rice_mas | rice_mas | 404 Probeset lookup not available | Os.21356.1.S1_at / LOC_Os01g01080 |
| rice | rice_rma | rice_rma | 404 Probeset lookup not available | Os.21356.1.S1_at / LOC_Os01g01080 |
| rice | riceanoxia_mas | rice_mas | 404 Probeset lookup not available | Os.21356.1.S1_at / LOC_Os01g01080 |
| rice | riceanoxia_rma | rice_rma | 404 Probeset lookup not available | Os.21356.1.S1_at / LOC_Os01g01080 |
| rice | ricestigma_mas | rice_mas | 404 Probeset lookup not available | Os.21356.1.S1_at / LOC_Os01g01080 |
| rice | ricestigma_rma | rice_rma | 404 Probeset lookup not available | Os.21356.1.S1_at / LOC_Os01g01080 |
| rice | ricestress_mas | rice_mas | 404 Probeset lookup not available | Os.21356.1.S1_at / LOC_Os01g01080 |
| rice | ricestress_rma | rice_rma | 404 Probeset lookup not available | Os.21356.1.S1_at / LOC_Os01g01080 |
| soybean | soybean | soybean | 404 Probeset lookup not available | Glyma06g47400 / Glyma.06g316600 |
| soybean | soybean_embryonic_development | soybean_embryonic_development | 404 Probeset lookup not available | Glyma06g47400 / Glyma.06g316600 |
| soybean | soybean_heart_cotyledon_globular | soybean_heart_cotyledon_globular | 404 Probeset lookup not available | Glyma06g47400 / Glyma.06g316600 |
| soybean | soybean_senescence | soybean_senescence | 404 Probeset lookup not available | Glyma06g47400.1 |
| soybean | soybean_severin | soybean_severin | 404 Probeset lookup not available | Glyma06g47400 / Glyma.06g316600 |
| strawberry | Developmental_Map_Strawberry_Flower_and_Fruit | strawberry | 400 Invalid strawberry gene ID | FvH4_1g00010 / gene10171 |
| strawberry | Strawberry_Green_vs_White_Stage | strawberry | 400 Invalid strawberry gene ID | FvH4_1g00010 / gene10171 |
| tomato | ILs_Leaf_Chitwood_et_al | tomato_ils | 400 Invalid tomato gene ID / 404 No expression data found | Solyc04g014530.1 / Solyc04g014530 |
| tomato | ILs_Root_Tip_Brady_Lab | tomato_ils2 | 400 Invalid tomato gene ID / 404 No expression data found | Solyc04g014530.1 / Solyc04g014530 |
| tomato | M82_S_pennellii_Atlases_Koenig_et_al | tomato_s_pennellii | 400 Invalid tomato gene ID / 404 No expression data found | Solyc04g014530.1 / Solyc04g014530 |
| tomato | Rose_Lab_Atlas | tomato | NONE | Solyc04g014530 |
| tomato | Rose_Lab_Atlas_Renormalized | tomato_renormalized | NONE | Solyc04g014530 |
| tomato | SEED_Lab_Angers | tomato_seed | 400 Invalid tomato gene ID / 404 No expression data found | Solyc04g014530.1 / Solyc04g014530 |
| tomato | Shade_Mutants | tomato_shade_mutants | NONE | Solyc04g014530 |
| tomato | Shade_Timecourse_WT | tomato_shade_timecourse | 404 No expression data found (also fails on eFP browser) | Solyc04g014530 |
| tomato | Tomato_Meristem | tomato_meristem | NONE | Solyc04g014530 |
| triticale | triticale | triticale | 404 Probeset lookup not available | Ta.10026.1.A1_at / EU181179 |
| triticale | triticale_mas | triticale_mas | 404 Probeset lookup not available | Ta.10026.1.A1_at / EU181179 |
| wheat | Developmental_Atlas | wheat | NONE | TraesCS1A01G000100 |
| wheat | Wheat_Abiotic_Stress | wheat_abiotic_stress | NONE | TraesCS1A02G000100.1 |
| wheat | Wheat_Embryogenesis | wheat_embryogenesis | NONE | TraesCS1A01G000100 |
| wheat | Wheat_Meiosis | wheat_meiosis | NONE | TraesCS1A02G000100.1 |
