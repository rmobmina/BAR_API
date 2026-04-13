# EFP Browser Lookup Table Verification

Manual check of lookup tables across all EFP browsers by reading the bottom sentence
displayed on each eFP browser page (e.g. "X was used as the probe set identifier for your primary
gene, Y").

---

## Method

Each EFP browser was visited manually and the bottom sentence was recorded to identify the probe
set identifier used vs. the gene ID returned. This was Dr. Provart's suggested approach before a
deeper lookup table audit.

---

## Probe Set Identifiers by Species

| Species | Probe Set Identifier | Gene ID | Description |
|---|---|---|---|
| Arabidopsis | `261585_at` | `At1g01010` | ANAC001_NAC001_NTL10__NAC domain containing protein 1 |
| Arabidopsis SeedCoat | `A000011_01` | `At1g17665` | None |
| Poplar | `PtpAffx.200227.1.S1_s_at` | `grail3.0047015901` | None |
| Medicago | `Mtr.25884.1.S1_at` | `Medtr1g102430` | DEAD-box ATP-dependent RNA helicase |
| Soybean | `Glyma06g47400` | `Glyma.06g316600` | RIN2 RPM1 interacting protein 2 |
| Potato | `PGSC0003DMG400000005` | `PGSC0003DMP400000011` | None |
| Tomato | `Solyc04g014530` | `Solyc04g014530` | Ethylene responsive transcription factor 1a |
| Eutrema | `Thhalv10000089m.g` | `AT2G21470` | None |
| Camelina | `AT4G13770` (Arabidopsis best hit) | `Csa00382s010.1` | — |
| Arachis | `Adur10000_comp0_c0_seq1` | `Adur10000_comp0_c0_seq1` | None |
| Grape | `CHRUN_JGVV120_4_T01` | `VIT_00s0120g00060` | AAA-type ATPase |
| Cannabis | `AGQN03000001` | `AGQN03000001` | None |
| Kalanchoe | `Kaladp0001s0001` | `Kaladp0001s0001` | None |
| Actinidia | `Acc00001.1` | `Acc00001.1` | None |
| Brassica | `BraA01g000010` | `BraA01g000010` | None |
| Canola | `BnaA01g00010D` | `BnaA01g00010D` | None |
| Cacao CCN | `CCN-51_Chr0v1_20099` | `CCN-51_Chr0v1_20099` | None |
| Cacao SCA | `SCA-6_Chr1v1_00001` | `SCA-6_Chr1v1_00001` | None |
| Cacao TC | `Tc01v2_g000010` | `Tc01v2_g000010` | None |
| Mangosteen | `DN1` | `DN1` | Tyrosine--tRNA ligase 1, cytoplasmic |
| Lupin | `Luan_Oskar_Trin_282785` | `Luan_Oskar_Trin_282785` | None |
| Strawberry | `FvH4_1g00010` | `gene10171` | None |
| Maize | `GRMZM2G083841` | `GRMZM2G083841_T01` | Phosphoenolpyruvate carboxylase, putative |
| Rice | `Os.21356.1.S1_at` | `LOC_Os01g01080` | Protein decarboxylase, putative |
| Barley | `Contig3045_at` | `AK364622` | Cytochrome P450 |
| Triticale | `Ta.10026.1.A1_at` | `EU181179` | Nucleotide binding / protein kinase activity |
| Brachypodium | `Bradi4g05940.1` | `Bradi4g05940.1` | None |
| Wheat | `TraesCS1A01G000100` | `TraesCS1A01G000100` | None |
| Little Millet | `TRINITY_DN0_c0_g1_i15` | `TRINITY_DN0_c0_g1_i15` | None |
| Oat | `N0.HOG0015560` (orthogroup) | `N0.HOG0015560` | — |
| Physcomitrella | `Pp1s103_79V6.1` | `Phypa_166136` | None |
| Selaginella | `Smo402070` | `Smo402070` | None |
| H (Human) | `206991_s_at` | `CCR5` | Chemokine (C-C motif) receptor 5 |
| Phelipanche | `OrAeBC5_10.1` | `AT1G07890` | None |
| Striga | `StHeBC3_1.1` | `AT3G11400` | None |
| Triphysaria | `TrVeBC3_1.1` | `AT1G11260` | None |

---

## Follow-up: Potato Identifier Discrepancy

Potato uses two different identifiers across eFP and ePlant with no clear consistency:

- **eFP Potato** — takes `PGSC0003DMG400000005` as input and **converts** it to
  `PGSC0003DMP400000011` (G → P, gene model to protein model variant). The bottom sentence
  confirms: *"PGSC0003DMG400000005 was used as the probe set identifier for your primary gene,
  PGSC0003DMP400000011 (None)"*
- **ePlant Potato** — uses `PGSC0003DMG400000005` **directly**, no conversion. Verified by
  checking the ePlant scripts.

Why was conversion chosen for eFP but not ePlant?
Should the BAR API implementation apply the G → P conversion to match eFP behaviour?
