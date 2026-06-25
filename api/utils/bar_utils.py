import re
import redis
import os

# fmt: off
# Per-eFP-project input validation regexes sourced from efpWeb.cgi.
# Each pattern covers canonical gene IDs AND (where applicable) microarray probeset IDs.
EFP_PROJECT_REGEXES: dict = {
    "efp": (
        r"^([Aa][Tt][12345CM][Gg][0-9]{5})$"
        r"|^([0-9]{6}(_[xsfi])?_at)$"
        r"|^([0-9]{6,9})$"
        # ATH1 Affymetrix bacterial/control spike-in probes, shared by all Affy platforms
        r"|^(AFFX-(BioB|BioC|BioDn|CreX|DapX|LysX|PheX|ThrX|TrpnX)-(3|5|M)_at)$"
        r"|^(AFFX-r2-(Bs|Ec|P1)-(dap|lys|phe|thr|bioB|bioC|bioD|cre)-(3|5|M)(_|_x_|_s_)at)$"
    ),
    "efp_arabidopsis": (
        r"^([Aa][Tt][12345CM][Gg][0-9]{5})$"
        r"|^([0-9]{6}(_[xsfi])?_at)$"
        r"|^([0-9]{6,9})$"
        r"|^(AFFX-(BioB|BioC|BioDn|CreX|DapX|LysX|PheX|ThrX|TrpnX)-(3|5|M)_at)$"
        r"|^(AFFX-r2-(Bs|Ec|P1)-(dap|lys|phe|thr|bioB|bioC|bioD|cre)-(3|5|M)(_|_x_|_s_)at)$"
    ),
    # Seedcoat uses CATMA probes (At\d{8}) and AROS probes (\D\d+_\d+) in addition to ATH1
    "efp_seedcoat": (
        r"^(At[12345CM]g[0-9]{5})$"
        r"|^([0-9]{6}(_[xsfi])?_at)$"
        r"|^([0-9]{6,9})$"
        r"|^(\D\d+_\d+)$"
        r"|^(At\d{8})$"
    ),
    "efp_barley": (
        r"^((HM|HV).*)$|^(HV.*_at)$"
        r"|^(([0-9]{4,7})_(Reg|R)_([0-9]{2,4})-([0-9]{4})_at)$"
        r"|^([0-9]{4,5}\.AF[0-9]{5}(_|_x_)at)$"
        r"|^(A[0-9]{5}\.[0-9]{1}(_|_x_|_s_)at)$"
        r"|^(([A-Z]{2}[0-9]{6}|[A-Z]{2}[0-9]{6}\.1)(_|_x_|_s_|_CDS-[0-9]{1,2}_|_CDS-[0-9]{1,2}_s_)at)$"
        r"|^(AFFX-(BioB|BioC|BioDn|CreX|DapX|LysX|PheX|ThrX|TrpnX)-(3|5|M)_at)$"
        r"|^(AFFX-r2-(Bs|Ec|P1)-(dap|lys|phe|thr|bioB|bioC|bioD|cre)-(3|5|M)(_|_x_|_s_)at)$"
        r"|^(ChlorContig[0-9]{1,2}(_|_x_|_s_)at)$"
        r"|^(((MitoContig|Contig)[0-9]{1,6})(_|_x_|_s_)at)$"
        r"|^(D[0-9]{5}_at)$"
        r"|^(Dhn[0-9]{2}\(Morex\)(_|_s_)at)$"
        r"|^(E(Ban|Bca|Bed|Bem|Bes|Bma|Bpi|Bro)[0-9]{2}_SQ[0-9]{3}_[A-Z]{1}[0-9]{2}(_|_s_|_x_)at)$"
        r"|^(Franka(_|_b_)3pri[0-9]{1,2}(_|_s_|_x_)at)$"
        r"|^(HVSME[a-z]{1}[0-9]{4}[A-Z]{1}[0-9]{2}(r2|f)(_|_x_|_s_)at)$"
        r"|^(HV_CEa[0-9]{4}[A-Z]{1}[0-9]{2}(r2|f)(_|_x_|_s_)at)$"
        r"|^(H[A-Z]{1}[0-9]{2}[A-Z]{1}[0-9]{2}[ru](_|_x_|_s_)at)$"
        r"|^(S[0-9]{10}[A-Z]{1}[0-9]{2}[A-Z]{1}[0-9]{1}(_|_x_|_s_)at)$"
        r"|^((b|rb)(aak|aal|ags|ah|asd)[0-9]{1,2}[a-z]{1}[0-9]{2}(_|_x_|_s_)at)$"
        r"|^(([0-9]{4,7})_(Reg|R)_([0-9]{2,4})-([0-9]{4}))$"
        r"|^([0-9]{4,5}\.AF[0-9]{5})$"
        r"|^(A[0-9]{5}\.[0-9]{1})$"
        r"|^([A-Z]{2}[0-9]{6}|[A-Z]{2}[0-9]{6}\.1)$"
        r"|^(AFFX-(BioB|BioC|BioDn|CreX|DapX|LysX|PheX|ThrX|TrpnX))$"
        r"|^(AFFX-r2-(Bs|Ec|P1)-(dap|lys|phe|thr|bioB|bioC|bioD|cre))$"
        r"|^(ChlorContig[0-9]{1,2})$"
        r"|^((MitoContig|Contig)[0-9]{1,6})$"
        r"|^(D[0-9]{5})$"
        r"|^(Dhn[0-9]{2}\(Morex\))$"
        r"|^(E(Ban|Bca|Bed|Bem|Bes|Bma|Bpi|Bro)[0-9]{2}_SQ[0-9]{3}_[A-Z]{1}[0-9]{2})$"
        r"|^(Franka(_|_b_)3pri[0-9]{1,2})$"
        r"|^(HVSME[a-z]{1}[0-9]{4}[A-Z]{1}[0-9]{2}(r2|f))$"
        r"|^(HV_CEa[0-9]{4}[A-Z]{1}[0-9]{2}(r2|f))$"
        r"|^(H[A-Z]{1}[0-9]{2}[A-Z]{1}[0-9]{2}[ru])$"
        r"|^(S[0-9]{10}[A-Z]{1}[0-9]{2}[A-Z]{1}[0-9]{1})$"
        r"|^((b|rb)(aak|aal|ags|ah|asd)[0-9]{1,2}[a-z]{1}[0-9]{2})$"
        r"|^(HO)$"
        r"|^(MLOC\.[0-9]{4,6}\.[0-9]{1,2})$"
        r"|^(AK[0-9]{6}\.1)$"
        r"|^(AJ[0-9]{6}\.1)$"
    ),
    "efp_rice": (
        r"^(LOC_Os[0-9]{2}g[0-9]{5})$"
        r"|^((AFFX|AFFX-Os)(-|_)(Ubiquitin|Actin|Cyph|Gapdh|BioB|BioC|BioDn|CreX|DapX|LysX|PheX|ThrX|TrpnX|ef1a|gapdh)(-|_)(3|5|M)_(at|x_at|s_at))$"
        r"|^(AFFX-OS-(18SrRNA|25SrRNA|5\.8SrRNA)_(s_at|at))$"
        r"|^((AFFX-Mgr-(actin|ef1a|gapdh)-(3|5|M))_(at|x_at|s_at))$"
        r"|^(AFFX-r2-Tag(A|B|C|D|E|F|G|H)_at)$"
        r"|^(AFFX-r2-Tag(IN|I|J|O|Q)-(3|5|M)_at)$"
        r"|^((AFFX|AFFX-Os)-r2-(Bs|Ec|P1)-(dap|lys|phe|thr|bioB|bioC|bioD|cre)-(3|5|M)(_|_x_|_s_)at)$"
        r"|^((Os|OsAffx)\.[0-9]{1,5}\.[0-9]{1}\.(S1|A1|S2)_(at|x_at|s_at|a_at))$"
    ),
    "efp_medicago": (
        r"^(Medtr\d{1}g\d{6})$"
        r"|^(Medtr\d{1}g\d{6}\.[0-9]{1})$"
        # Medicago array probesets: Mtr/Msa/Sme prefix, any Affymetrix suffix variant
        r"|^(Mtr\.\d{4,5}\.\d+\.(S1|A1|S2)_(at|s_at|x_at|a_at))$"
        r"|^(Msa\.\d+\.\d+\.(S1|A1|S2)_(at|s_at|x_at|a_at))$"
        r"|^(Sme\.\d+\.\d+\.(S1|A1|S2)_(at|s_at|x_at|a_at))$"
        r"|^(AFFX-(Bio|Cre|Dap|Lys|Phe|Thr|Trpn)(B|C|Dn|X)-(3|5|M)_at)$"
        r"|^(AFFX-(Msa|Mtr)-(actin|gapc|gsta|ubq11|TrpnX)-(3|5|M)_(at|x_at|s_at))$"
        r"|^(AFFX-r2-(Bs|Ec|P1)-(cre|dap|lys|phe|thr|bioB|bioC|bioD)-(3|5|M)_(at|s_at|x_at))$"
        r"|^(AFFX-Mtr-ubq11-(3|5|M)_(at|s_at|x_at))$"
        r"|^(AFFX-r2-Tag[A-Z]{1,2}_at)$"
        r"|^(Medtr_v1_\d{6})$"
    ),
    "efp_poplar": (
        r"^(Ptp(Affx)?\.\d{1,6}\.\d{1,6}\.(A1|A2|S1|S2)_(x_at|s_at|at|a_at))$"
        r"|^((eugene3)\.\d{6,12})$"
        r"|^((estExt_)(Genewise|fgenesh)(1|4)\_(v1|kg|pg|pm)(\.|\_v1\.)C_LG_\w{6,10})$"
        r"|^((grail3\.)\d{8,12})$"
        r"|^((fgenesh)(1|4)\_(kg|pg|pm)\.C\_(scaffold|LG)\_\w{7,12})$"
        r"|^((gw1)\.\w{1,6}\.\w{1,4}\.1)$"
        r"|^((POPTR)\_[0-9]{4}s[0-9]{5}\.*[1-5]{0,1})$"
        # poplar_hormone's real sample IDs omit the transcript suffix entirely
        r"|^(Potri\.[0-9]{3}G[0-9]{6}(\.[0-9]{1})?)$"
    ),
    "efp_soybean": (
        r"^((Glyma\d{1,3}g\d{1,6}\.?\d?)$"
        r"|^(Glyma\.\d{1,3}g\d{1,8}))$"
    ),
    "efp_maize": (
        r"^(AC[0-9]{6}\.[0-9]{1}_FG[0-9]{3})$"
        r"|^(AC[0-9]{6}\.[0-9]{1}_FGT[0-9]{3})$"
        r"|^(GRMZM(2|5)G[0-9]{6})$"
        r"|^(GRMZM(2|5)G[0-9]{6}_T[0-9]{2})$"
        r"|^(Zm\d+d\d+)$"
        r"|^(Zm\d{1,10}eb\d{1,10})$"
        # Maize Affymetrix probeset IDs, e.g. Zm011368_at, Zm039842_s_at
        r"|^(Zm\d{6}(_[xsa])?_at)$"
    ),
    # TaAffx.* probes occur alongside Ta.* — handle both prefixes
    "efp_triticale": r"^((Ta|TaAffx)\.\d+\.\d+\.[A-Z]\d+_(at|s_at|x_at|a_at))$",
    # Affymetrix human probeset IDs (1557575_at, 202019_s_at) plus a loose fallback
    "efp_human": r"^(\d{6,7}(_[xsa])?_at)$|^(\D{0,12}\d{0,12})$|^(\d{1,12})$",
    # Remaining eFP projects, sourced verbatim from Vincent's efp_regex_audit_prod.csv
    "efp_Eutrema": r"^(Thhalv\d{8}m\.g)$|^(XLOC_\d{6})$|^(nXLOC\d{6})$|^(At\dg\d{5})$",
    "efp_actinidia": r"^(Acc\d+\.\d{0,3})$",
    "efp_apple": r"^(MfusH1_\d\dg\d{1,8})$",
    # CSV pattern is lowercase-only; lipid species names use mixed case (e.g. "TG 54:5; ...")
    "efp_arabidopsis_lipid": r"(?i)^[a-z0-9\s:;\/\[\]_\+\-]{1,64}$",
    "efp_arachis": r"^(Adur\d+_comp\d+_c\d+_seq\d+)$|^(Gyn_Aipa_c\d+_g\d+_i\d+)$|^(Aipa\d+_comp\d+_c\d+_seq\d+)$|^(Gyn_Adur_c\d+_g\d+_i\d+)$",
    "efp_brachypodium": r"^(Bradi\d+g\d+.\d)$|^(Bradi\d+s\d+.\d)$|^(Bradi\d+.g\d+)$",
    "efp_brachypodium_metabolites": r"(?i)^[a-z\s\-]{1,60}$",
    "efp_brassica_rapa": r"^(Bra.\d+g\d{0,10})$",
    "efp_cacao_ccn": r"^(CCN-51_Chr\d{1,3}v\d{1,3}_\d{1,9})$",
    "efp_cacao_sca": r"^(SCA-6_Chr\d{1,3}v\d{1,3}_\d{1,9})$",
    "efp_cacao_tc": r"^(Tc\d+v2_g\d+)$",
    "efp_camelina": r"^(Csa\d{0,5}[gs]\d{0,6}.\d{0,3})$|^(At\d[cgm]\d{0,6})$",
    "efp_cannabis": r"(^C\d+$)|(^scaffold\d+$)|(^AGQN\d+$)",
    "efp_canola": r"^(Bna\D\d{1,3}g\d{1,8}\D)$|^(Bna\Dnng\d{1,8}\D)$",
    "efp_durum_wheat": r"^(TrturSVE\d\D\d{1,3}G\d{1,12})$|^(TrturSVE\d\D\d{1,3}G\d{1,12}_ncBOCREA)$",
    "efp_euphorbia": r"^(Ep_chr\d_g\d{1,8})$",
    "efp_eutrema": r"^(Thhalv\d{8}m\.g)$|^(XLOC_\d{6})$|^(nXLOC\d{6})$|^(At\dg\d{5})$",
    "efp_grape": r"^(VIT_\d{1,2}s\d{4}g\d{5})$|^CHRUN[a-z0-9_]{1,20}$|^CHR\d{1,2}[a-z0-9_]{1,2}$",
    "efp_kalanchoe": r"^(Kaladp\d+s\d+)$",
    "efp_little_millet": r"^(TRINITY_DN\d+_c\d+_g\d+_i\d+)$",
    "efp_lupin": r"^(Luan_Oskar_.{1,12}_\d{1,12})$",
    # is_efp_gene_valid matches without re.IGNORECASE, so these freeform-text
    # patterns (enzyme/metabolite/category NAMES, not gene IDs) need an explicit
    # (?i) -- real sample data is mixed-case ("GAPDH (NAD)", "Citric Acid").
    "efp_maize_enzyme": r"(?i)^[a-z0-9\s\-\(\)]{1,50}$",
    "efp_maize_metabolite": r"(?i)^[a-z0-9\s,\.\-\(\)_'\+]{1,60}$",
    # Lipid species names (TG_52_1, MGDG_38_6), same freeform style as efp_arabidopsis_lipid
    "efp_maize_lipid_map": r"(?i)^[a-z0-9\s:;\/\[\]_\+\-]{1,64}$",
    # tomato_trait stores root-architecture trait descriptions, not gene IDs
    "efp_tomato_trait": r"^[A-Za-z][A-Za-z0-9\s\.,\-\(\)]{1,100}$",
    "efp_maize_transcriptomics": r"^(AC[0-9]{6}\.[0-9]{1}_FG[0-9]{3})$|^(AC[0-9]{6}\.[0-9]{1}_FGT[0-9]{3})$|^(GRMZM(2|5)G[0-9]{6})$|^(GRMZM(2|5)G[0-9]{6}_T[0-9]{2})$|^(Zm\d+d\d+)$|^(Zm\d{1,10}eb\d{1,10})$|^(Zm\d{6}(_[xsa])?_at)$",
    "efp_mangosteen": r"^(DN\d{1,10})$",
    "efp_marchantia": r"^(Mp.{1,3}g\d{1,7}\.?\d{1,3}?)$",
    "efp_oat": r"(^N0\.HOG\d{1,10}$|^\D{1,10}\.*\d{1,10}.{1,10}\d{1,10}$)",
    "efp_phelipanche": r"^(OrAeBC\d+_\d+\.\d{1,5})|(At\d[gcm]\d{1,6})$",
    "efp_physcomitrella": r"^(Pp)\d+s\d+_\d+V\d\.\d$|^Phypa_\d+$",
    "efp_potato": r"^(PGSC0003DMG4\d{8})$",
    "efp_rice_metabolite": r"(?i)^[a-z0-9,\s\.\-]{1,40}$",
    "efp_rice_transcriptomics": r"^(LOC_Os[0-9]{2}g[0-9]{5})$|^((AFFX|AFFX-Os)(-|_)(Ubiquitin|Actin|Cyph|Gapdh|BioB|BioC|BioDn|CreX|DapX|LysX|PheX|ThrX|TrpnX|ef1a|gapdh)(-|_)(3|5|M)_(at|x_at|s_at))$|^(AFFX-OS-(18SrRNA|25SrRNA|5.8SrRNA)_(s_at|at))$|^((AFFX-Mgr-(actin|ef1a|gapdh)-(3|5|M))_(at|x_at|s_at))$|^(AFFX-r2-Tag(A|B|C|D|E|F|G|H)_at)$|^(AFFX-r2-Tag(IN|I|J|O|Q)-(3|5|M)_at)$|^((AFFX|AFFX-Os)-r2-(Bs|Ec|P1)-(dap|lys|phe|thr|bioB|bioC|bioD|cre)-(3|5|M)(_|_x_|_s_)at)$|^((Os|OsAffx)\.[0-9]{1,5}\.[0-9]{1}\.(S1|A1|S2)_(at|x_at|s_at|a_at))$",
    "efp_selaginella": r"^(Smo\d+)$",
    "efp_sorghum": r"^(Sobic.\d{0,5}G\d{0,10}$|^Sobic.K\d{0,10}$|^ENSRNA\d{0,12}$|^SORBI_\d{1,6}G\d{1,10})$",
    "efp_strawberry": r"^(FvH4_c?\d{1,3}g\d{1,7})$|^(gene\d{1,10})$",
    "efp_striga": r"^(StHeBC3\_\d+\.\d{1,5})$|^(At\d[gcm]\d{1,6})$",
    "efp_tomato": r"^(Solyc\d{2}g\d{6}\.?\d{0,3})$|^(TU\d{6})$",
    "efp_triphysaria": r"^(TrVeBC\d+_\d+\.\d{1,5})$|^(At\d[gcm]\d{1,6})$",
    "efp_tung_tree": r"^(Vf\d+G\d+)$",
    "efp_wheat": r"^(TraesCS\d\D\d{0,2}[G]\d{0,6}L*C*\.*\d*)$|^(TraesCSU\d+G\d+L*C*\.*\d*)$",
    "efpconfig": r".{0,16}",
    "mouse_efp": r"^(XM_\d{0,8}\.\d{0,3})$|^(\d{1,10}\D\d{0,4}\D{0,4})$|^(\D{1,8}\d{0,8}\D{0,8})$|^(ENSMUSG\d{1,15})$|^(NM_\d{0,12}\d.\d{0,3})$",
}
# Aliases for alternate eFP project key spellings used by the BAR
EFP_PROJECT_REGEXES["efpbarley"] = EFP_PROJECT_REGEXES["efp_barley"]
EFP_PROJECT_REGEXES["efprice"] = EFP_PROJECT_REGEXES["efp_rice"]
EFP_PROJECT_REGEXES["efpmedicago"] = EFP_PROJECT_REGEXES["efp_medicago"]
EFP_PROJECT_REGEXES["efppop"] = EFP_PROJECT_REGEXES["efp_poplar"]
EFP_PROJECT_REGEXES["efpsoybean"] = EFP_PROJECT_REGEXES["efp_soybean"]
EFP_PROJECT_REGEXES["maizeefp"] = EFP_PROJECT_REGEXES["efp_maize"]
# fmt: on


class BARUtils:
    @staticmethod
    def error_exit(msg):
        """Exit if failed
        :param msg: message to pass on failure
        :return:
        """
        result = {"wasSuccessful": False, "error": msg}
        return result

    @staticmethod
    def success_exit(msg):
        """Output if success
        :param msg: the actual data the needs to be output
        :return:
        """
        result = {"wasSuccessful": True, "data": msg}
        return result

    @staticmethod
    def is_arabidopsis_gene_valid(gene):
        """This function verifies if Arabidopsis gene is valid
        :param gene:
        :return:
        """
        if re.search(r"^At[12345cm]g\d{5}.?\d?$", gene, re.I):
            return True
        else:
            return False

    @staticmethod
    def normalize_arabidopsis_gene(gene):
        """Return Arabidopsis gene in canonical case (At1g01010)."""
        if not gene:
            return gene
        lowered = gene.lower()
        if re.search(r"^at[12345cm]g\d{5}.?\d?$", lowered):
            return "At" + lowered[2:]
        return gene

    @staticmethod
    def is_actinidia_gene_valid(gene):
        """Validates kiwifruit (Actinidia) gene IDs: Acc23558.1"""
        return bool(gene and re.search(r"^Acc\d{5}\.\d+$", gene, re.I))

    @staticmethod
    def is_apple_gene_valid(gene):
        """Validates apple gene IDs: MfusH1_01g00343"""
        return bool(gene and re.search(r"^MfusH1_\d{2}g\d{5}$", gene, re.I))

    @staticmethod
    def is_barley_gene_valid(gene):
        """Validates barley gene IDs: HORVU0Hr1G000320, HORVU.MOREX.r3.1HG0003350.1,
        or HORVU.MOREX.r3.UnG0797170.1 (Un = unplaced scaffold, no chromosome digit)"""
        return bool(
            gene and re.search(r"^HORVU(\d+Hr\d+G\d+|\.MOREX\.r\d+\.(\dH|Un)G\d+\.\d+)$", gene, re.I)
        )

    @staticmethod
    def is_brachypodium_gene_valid(gene):
        """Validates Brachypodium gene IDs: Bradi1g04930.1"""
        return bool(gene and re.search(r"^Bradi\d+g\d+\.\d+$", gene, re.I))

    @staticmethod
    def is_cacao_gene_valid(gene):
        """Validates cacao gene IDs: CCN-51_Chr1v1_08396, SCA-6_Chr1v1_00610, Tc01v2_g002690"""
        return bool(gene and re.search(r"^((CCN-51|SCA-6)_Chr\d+v\d+_\d+|Tc\d+v\d+_g\d+)$", gene))

    @staticmethod
    def is_camelina_gene_valid(gene):
        """Validates Camelina gene IDs: Csa01g012560.1, Csa00462s060.1"""
        return bool(gene and re.search(r"^Csa\d+[gs]\d+\.\d+$", gene, re.I))

    @staticmethod
    def is_cassava_gene_valid(gene):
        """Validates cassava gene IDs: Manes.01G040000.v8.1"""
        return bool(gene and re.search(r"^Manes\.\d{2}G\d+\.v\d+\.\d+$", gene, re.I))

    @staticmethod
    def is_cuscuta_gene_valid(gene):
        """Validates Cuscuta gene IDs: Cc000663.t1 or Cc000082"""
        return bool(gene and re.search(r"^Cc\d+(\.t\d+)?$", gene, re.I))

    @staticmethod
    def is_eucalyptus_gene_valid(gene):
        """Validates Eucalyptus gene IDs: Eucgr.A01716"""
        return bool(gene and re.search(r"^Eucgr\.[A-Z]\d+$", gene, re.I))

    @staticmethod
    def is_euphorbia_gene_valid(gene):
        """Validates Euphorbia gene IDs: Ep_chr1_g00698"""
        return bool(gene and re.search(r"^Ep_chr\d+_g\d+$", gene, re.I))

    @staticmethod
    def is_grape_gene_valid(gene):
        """Validates grape gene IDs: CHR11_JGVV37_114_T01, CHR2_GSVIVT00001265001_T01,
        CHRUN_JGVV479_1_T01 (CHRUN = unplaced), or legacy VIT_00s0120g00060"""
        return bool(
            gene
            and re.search(
                r"^(CHR(\d+|UN)_[A-Z]+\d+(_\d+)?_T\d+|VIT_\d{0,3}\D\d{0,5}g\d{0,6})$", gene, re.I
            )
        )

    @staticmethod
    def is_poplar_gene_valid(gene):
        """This function verifies if Poplar v3 gene (Potri.001G123456.1) or World Map
        atlas probe (Potri.T174200) is valid
        :param gene:
        :return: True if valid
        """
        if re.search(r"^POTRI\.(\d{3}G\d{6}\.?\d{0,3}|T\d{6})$", gene, re.I):
            return True
        else:
            return False

    @staticmethod
    def is_rice_gene_valid(gene, isoform_id=False):
        """Validates rice gene IDs: LOC_Os01g01430, LOC_Os01g01430.1 (isoform), or Os01g0138100"""
        if not gene:
            return False
        if isoform_id and re.search(r"^LOC_Os\d{2}g\d{5}\.\d{1,2}$", gene, re.I):
            return True
        if not isoform_id and re.search(r"^LOC_Os\d{2}g\d{5}$", gene, re.I):
            return True
        if re.search(r"^Os\d{2}g\d+$", gene, re.I):
            return True
        return False

    @staticmethod
    def is_spruce_gene_valid(gene):
        """Validates spruce clone IDs from either of two cDNA libraries:
        GQ0031_G08.1 or WS0321_C07.1 / WS03217_B11.1"""
        return bool(gene and re.search(r"^(GQ|WS)\d{4,5}_[A-Z]\d{2}\.\d+$", gene))

    @staticmethod
    def is_sugarcane_gene_valid(gene):
        """Validates sugarcane gene IDs: Sh01_g004010 or BAC-clone-based
        Sh_209L02_contig-1_g000020 / Sh_135M16_g000010"""
        return bool(
            gene and re.search(r"^(Sh\d+_g\d+|Sh_[A-Z0-9]+(_contig-\d+)?_g\d+)$", gene, re.I)
        )

    @staticmethod
    def is_sunflower_gene_valid(gene):
        """Validates sunflower gene IDs: Ha10_00000854"""
        return bool(gene and re.search(r"^Ha\d+_\d+$", gene, re.I))

    @staticmethod
    def is_tung_tree_gene_valid(gene):
        """Validates tung tree gene IDs: Vf01G0116"""
        return bool(gene and re.search(r"^Vf\d+G\d+$", gene, re.I))

    @staticmethod
    def is_wheat_gene_valid(gene):
        """Validates wheat gene IDs: TraesCS1A01G268900LC, TraesCS1A02G311600LC.1, TrturSVE1A02G00066260"""
        return bool(
            gene
            and re.search(r"^(TraesCS[0-9A-Z]+(\.\d+)?|TrturSVE[0-9A-Z]+G\d+)$", gene, re.I)
        )

    @staticmethod
    def is_willow_gene_valid(gene):
        """Validates willow Trinity gene IDs: comp170315_c0_seq1"""
        return bool(gene and re.search(r"^comp\d+_c\d+_seq\d+$", gene, re.I))

    @staticmethod
    def is_thellungiella_gene_valid(gene):
        """Validates native Thellungiella (Eutrema salsugineum) gene IDs.
        Accepts Thhalv format (Thhalv10000089m.g) and novel locus IDs (nXLOC_003010).
        """
        return bool(re.search(r"^Thhalv\d+m\.g$", gene) or re.search(r"^nXLOC_\d+$", gene))

    @staticmethod
    def is_tomato_gene_valid(gene, isoform_id=False):
        """This function verifies if ITAG Solyc gene is valid
        :param gene:
        :param isoform_id: True if you want to verifiy isoform ID
        :return: True if valid
        """
        if isoform_id and re.search(r"^Solyc\d\dg\d{6}\.\d\.\d$", gene, re.I):
            return True
        elif isoform_id is False and re.search(r"^Solyc\d\dg\d{6}(\.\d+)?$", gene, re.I):
            return True
        else:
            return False

    @staticmethod
    def is_cannabis_gene_valid(gene):
        """This function verifies if cannabis gene is valid: AGQN03000001
        :param gene:
        :return: True if valid
        """
        if gene and re.search(r"^AGQN\d{0,10}$", gene, re.I):
            return True
        else:
            return False

    @staticmethod
    def is_canola_gene_valid(gene):
        """Validates canola gene IDs: BnaA01g34660D, BoC01g03100.09V4, BoBC_1096g00001.01V4,
        legacy BrChr4g00368.01V4 / BrBA_1327g00001.01V4 (canola_original* dbs), or
        legacy EST contig IDs (Contig18943)"""
        return bool(
            gene
            and re.search(
                r"^(Bna[AC]\d{2}g\d{5}[A-D]?|Bo[A-Z]+_?\d+g\d+\.\d+V\d+"
                r"|Br(Chr\d{1,2}|BA_\d+)g\d{5}\.\d{2}V\d|Contig\d+)$",
                gene,
                re.I,
            )
        )

    @staticmethod
    def is_arachis_gene_valid(gene):
        """This function verifies if arachis gene is valid: Adur10000_comp0_c0_seq1
        :param gene:
        :return: True if valid
        """
        if gene and re.search(r"^Adur\d{1,10}_comp\d{1,3}_\D{1,3}\d{1,3}_seq\d{1,5}$", gene, re.I):
            return True
        else:
            return False

    @staticmethod
    def is_brassica_rapa_gene_valid(gene):
        """Validates Brassica rapa gene IDs: BraA01g000010 or A01g510040.1_BraROA"""
        return bool(
            gene
            and re.search(r"^(BraA.{1,4}g\d{1,9}|[A-Z]\d{2}[gp]\d+\.\d+_BraROA)$", gene, re.I)
        )

    @staticmethod
    def is_human_gene_valid(gene):
        """Validates human NCBI Entrez gene IDs (10057), HGNC gene symbols (KRT79,
        MIR1285-1), and Ensembl clone-based names (RP11-108K3.3, CTD-2162K18.3,
        AC012360.2) used by RNA-seq atlases like human_body_map_2"""
        return bool(
            gene
            and re.search(
                r"^\d{1,10}$"
                r"|^[A-Z][A-Z0-9]{1,9}(-\d{1,3})?$"
                r"|^[A-Z]{2,4}\d{0,3}-\d{2,4}[A-Z]\d{1,3}\.\d{1,3}$"
                r"|^A[CL]\d{6}\.\d{1,3}$",
                gene,
                re.I,
            )
        )

    @staticmethod
    def is_little_millet_gene_valid(gene):
        """Validates little millet Trinity gene IDs: TRINITY_DN101568_c0_g1_i1"""
        return bool(gene and re.search(r"^TRINITY_DN\d+_c\d+_g\d+_i\d+$", gene, re.I))

    @staticmethod
    def is_lupin_gene_valid(gene):
        """Validates lupin gene IDs: Luan_Oskar_PB12_103067 or Luan_Oskar_Trin_111463"""
        return bool(gene and re.search(r"^Luan_Oskar_(PB\d+|Trin)_\d+$", gene, re.I))

    @staticmethod
    def is_mangosteen_gene_valid(gene):
        """Validates mangosteen Trinity gene IDs: DN118788"""
        return bool(gene and re.search(r"^DN\d+$", gene, re.I))

    @staticmethod
    def is_marchantia_gene_valid(gene):
        """Validates Marchantia polymorpha gene IDs: Mp1g01370.1, or unplaced-scaffold
        Mpzg00730.1"""
        return bool(gene and re.search(r"^Mp\w{1,3}g\d+\.\d+$", gene, re.I))

    @staticmethod
    def is_medicago_gene_valid(gene):
        """Validates Medicago gene IDs: Medtr1g018805, Medtr0010s0370, MtrunA17Chr1g0153991, Medtr_v1_003290"""
        return bool(
            gene
            and re.search(r"^(Medtr(\d+[gs]\d+|_v1_\d+)|MtrunA17Chr\dg\d+)$", gene, re.I)
        )

    @staticmethod
    def is_mouse_gene_valid(gene):
        """Validates mouse RefSeq transcript IDs: XM_122892.1"""
        return bool(gene and re.search(r"^XM_\d+\.\d+$", gene, re.I))

    @staticmethod
    def is_oat_gene_valid(gene):
        """Validates oat gene IDs: AVESA.00001b.r1.2AG01080490"""
        return bool(gene and re.search(r"^AV[A-Z]{3}\.\d{5}[a-z]\.r\d+\.\d[A-Z]{2}\d{8}$", gene))

    @staticmethod
    def is_potato_gene_valid(gene):
        """Validates potato gene IDs: PGSC0003DMG400001801 or EPlSTUG00000003328"""
        return bool(gene and re.search(r"^(PGSC0003DMG\d+|EPlSTUG\d+)$", gene, re.I))

    @staticmethod
    def is_quinoa_gene_valid(gene):
        """Validates quinoa gene IDs: CquiG00000000055"""
        return bool(gene and re.search(r"^CquiG\d+$", gene, re.I))

    @staticmethod
    def is_soybean_gene_valid(gene):
        """This function verifies if soybean gene is valid: Glyma06g47400
        :param gene:
        :return: True if valid
        """
        if gene and re.search(r"^((Glyma\d{1,3}g\d{1,6}\.?\d?)|(Glyma\.\d{1,3}g\d{1,8}))$", gene, re.I):
            return True
        else:
            return False

    @staticmethod
    def is_maize_gene_valid(gene):
        """Validates maize gene IDs: Zm00001d046170, Zm00001eb006030, AC195946.3_FG003, GRMZM2G000116"""
        return bool(
            gene
            and re.search(
                r"^(AC[0-9]{6}\.[0-9]+_FGT?[0-9]{3}|GRMZM[25]G[0-9]{6}(_T[0-9]{2})?|Zm\d+(d|eb)\d+)$",
                gene,
                re.I,
            )
        )

    @staticmethod
    def is_sorghum_gene_valid(gene):
        """Validates sorghum gene IDs: Sobic.001G003400, Sobic.001G085800.1, SORBI_3001G060800, ENSRNA049471574"""
        return bool(
            gene
            and re.search(
                r"^(Sobic\.\d+G\d+(\.\d+)?|Sobic\.K\d+|SORBI_\d+G\d+|ENSRNA\d+)$", gene, re.I
            )
        )

    @staticmethod
    def is_kalanchoe_gene_valid(gene):
        """This function verifies if Kalanchoe gene is valid
        :param gene:
        :return:
        """
        if re.search(r"^Kaladp\d{1,10}s\d{1,10}$", gene, re.I):
            return True
        else:
            return False

    @staticmethod
    def is_phelipanche_gene_valid(gene):
        """This function verifies if phelipanche gene (OrAeBC5_9992.10) is valid
        :param gene:
        :return:
        """
        if re.search(r"^OrAeBC5_\d{1,6}\.\d{1,3}$", gene, re.I):
            return True
        else:
            return False

    @staticmethod
    def is_physcomitrella_gene_valid(gene):
        """This function verifies if physcomitrella gene (Pp1s9_70V6.1) is valid
        :param gene:
        :return:
        """
        if re.search(r"^Pp1s\d{1,8}_\d{1,8}V6\.\d{1,3}$", gene, re.I):
            return True
        else:
            return False

    @staticmethod
    def is_selaginella_gene_valid(gene):
        """This function verifies if selaginella gene (Smo402070) is valid
        :param gene:
        :return:
        """
        if re.search(r"^Smo\d{1,8}$", gene, re.I):
            return True
        else:
            return False

    @staticmethod
    def is_strawberry_gene_valid(gene):
        """This function verifies if strawberry gene (FvH4_1g00010) is valid
        :param gene:
        :return:
        """
        if re.search(r"^FvH4_\d{1,3}g\d{1,8}$", gene, re.I):
            return True
        else:
            return False

    @staticmethod
    def is_striga_gene_valid(gene):
        """This function verifies if striga gene (StHeBC3_9993.10) is valid
        :param gene:
        :return:
        """
        if re.search(r"^StHeBC3_\d{1,6}\.\d{1,5}$", gene, re.I):
            return True
        else:
            return False

    @staticmethod
    def is_triphysaria_gene_valid(gene):
        """This function verifies if triphysaria gene (TrVeBC3_9999.18) is valid
        :param gene:
        :return:
        """
        if re.search(r"^TrVeBC3_\d{1,6}\.\d{1,3}$", gene, re.I):
            return True
        else:
            return False

    @staticmethod
    def is_integer(data):
        """Check if the input is at max ten figure number.
        :param data: int number
        :return: True if a number
        """
        if re.search(r"^\d{1,10}$", data):
            return True
        else:
            return False

    @staticmethod
    def is_gaia_alias(data):
        """Check if the input is a valid gaia alias.
        :param data
        :return: True if valid gaia alias
        """
        if re.search(r"^[a-z0-9_]{1,50}$", data, re.I):
            return True
        else:
            return False

    @staticmethod
    def format_poplar(poplar_gene):
        """Format Poplar gene ID to be Potri.016G107900, i.e. capitalized P and G
        :param poplar_gene: gene id
        :return: String
        """
        return poplar_gene.translate(str.maketrans("pOTRIg", "PotriG"))

    @staticmethod
    def is_efp_gene_valid(gene: str, efp_project: str) -> bool:
        """Validate a gene ID against the named eFP project's input regex.

        Accepts both canonical gene IDs (e.g. AT1G01010 for Arabidopsis) and
        microarray probeset IDs (e.g. 267643_at, Contig7905_at) depending on the
        project. Returns False if the eFP project name is unknown.

        :param gene: Gene identifier to validate
        :param efp_project: eFP project key (e.g. 'efp_arabidopsis', 'efpbarley')
        :return: True if the gene ID matches the project's accepted format
        """
        pattern = EFP_PROJECT_REGEXES.get(efp_project)
        if not pattern:
            return False
        return bool(re.search(pattern, gene))

    @staticmethod
    def connect_redis():
        """This function connects to redis
        :returns: redis connection
        """
        if os.environ.get("BAR"):
            r = redis.Redis(
                host=os.environ.get("BAR_REDIS_HOST"), port=6379, password=os.environ.get("BAR_REDIS_PASSWORD")
            )
        else:
            r = redis.Redis(host="localhost")

        return r
