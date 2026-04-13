# Duplicate Tissue/Group/Sample Names in XML Files

Checked for duplicate names across tissue, group, and sample fields in EFP XML files,
as requested by Dr. Provart. Used a web scraper to flag duplicates, then manually verified results.
Scraper output saved in `data_duplicate_xml_fields.json`.

---

## Duplicates Found by Species

**Actinidia — Bud_Development.xml**
- Tissue `"bud"` repeated under group `"Nov"`

**Actinidia — Flower_Fruit_Development.xml**
- Tissues `"core"`, `"cortex"`, `"flesh"` repeated under group `"flower"`

**Actinidia — Postharvest.xml**
- Tissues `"core"`, `"cortex"`, `"flesh"` repeated under group `"Postharvest Control"`

**Arabidopsis — Development_RMA.xml**
- Tissue `"Root"` repeated under group `"CTRL_7"`

**Arabidopsis — Developmental_Map.xml**
- Tissue `"Root"` repeated under group `"CTRL_7"`

**Arabidopsis — Lateral_Root_Initiation.xml**
- Groups `"Cortex.0hr.Mean"` and `"Pericycle.0hr.Mean"` duplicated

**Arabidopsis — Regeneration.xml**
- Groups `"bot1330w;bot1517;bot1516"` and `"bot1334w;bot1521;bot1520"` duplicated

**Arabidopsis — Tissue_Specific.xml**
- Group `"ATGE_CTRL_7"` has multiple duplicates

**Arabidopsis Seedcoat — Seed_Coat.xml**
- Group `"tt16-1 mutant seed"` duplicated

**Grape — grape_developmental.xml**
- Tissue `"Bud - Winter Dormant"` repeated under group `"Dev"`

**Rice — rice_leaf_gradient.xml**
- Tissue `"R7"` repeated under group `"Rice"`

**Rice — ricestress_mas.xml**
- Sample `"RICE_CTRL_STRESS"` duplicated across `"Control_Shoot"` and `"Control_Root"`

**Rice — ricestress_rma.xml**
- Sample `"RICE_CTRL_STRESS"` duplicated across `"Control_Shoot"` and `"Control_Root"`
