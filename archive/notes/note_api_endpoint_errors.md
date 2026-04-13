# API Endpoint Error Breakdown

Summary of current errors occurring in the BAR API, organized by endpoint group,
as requested by Dr. Provart. This was all tested manually.

---

## Gene Information

| Endpoint | Code | Error |
|---|---|---|
| `/gene_information/gene_aliases` | 400 BAD REQUEST | Unknown field |
| `/gene_information/gene_isoforms/` | 400 BAD REQUEST | Unknown field |

---

## ThaleMine

| Endpoint | Code | Error |
|---|---|---|
| `/thalemine/gene_information/{gene_id}` | 500 INTERNAL SERVER ERROR | ConnectionError: Error 111 connecting to localhost:6379 — connection refused |
| `/thalemine/gene_rife/{gene_id}` | 500 INTERNAL SERVER ERROR | ConnectionError: Error 111 connecting to localhost:6379 — connection refused |
| `/thalemine/publications/{gene_id}` | 500 INTERNAL SERVER ERROR | ConnectionError: Error 111 connecting to localhost:6379 — connection refused |

---

## SNPs

| Endpoint | Code | Error |
|---|---|---|
| `/snps/docking/{receptor}/{ligand}` | 400 BAD REQUEST | Invalid Arabidopsis PDB gene ID |
| `/snps/phenix/{fixed_pdb}/{moving_pdb}` | 500 INTERNAL SERVER ERROR | FileNotFoundError: `phenix.superpose_pdbs` not found |
| `/snps/pymol/{model}` | 500 INTERNAL SERVER ERROR | NameError: `cmd` not defined — missing import |
| `/snps/seq_hotspot/{pval}/{araid}/{popid}` | 500 INTERNAL SERVER ERROR | FileNotFoundError: `/home/ihazelwood/BCB330-Homologues/ara-pop3.0-all-valid.tsv` |
| `/snps/struct_hotspot/{pval}/{araid}/{popid}` | 500 INTERNAL SERVER ERROR | FileNotFoundError: `/home/ihazelwood/BCB330-Homologues/ara-pop3.0-all-valid.tsv` |
| `/snps/{species}/samples` | 500 INTERNAL SERVER ERROR | ConnectionError: Error 111 connecting to localhost:6379 — connection refused |
| `/snps/{species}/{gene_id}` | 500 INTERNAL SERVER ERROR | ConnectionError: Error 111 connecting to localhost:6379 — connection refused |

---

## Interactions

| Endpoint | Code | Error |
|---|---|---|
| `/interactions/mfinder` | 500 INTERNAL SERVER ERROR | CalledProcessError: `/bartmp/mfinder` returned non-zero exit status 127 |

---

## eFP Image

| Endpoint | Code | Note |
|---|---|---|
| `/efp_image/get_efp_data_source/{species}` | 200 OK | Only available on the BAR |
| `/efp_image/get_efp_dir/{species}` | 500 INTERNAL SERVER ERROR | FileNotFoundError: `/var/www/html/eplant/efp/data/` not found |
