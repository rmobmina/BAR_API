import re
import redis
import os

from api.utils.master_data_utils import load_combined_master

# Per-eFP-project input validation regexes. Sourced from Vincent's
# regex_master_list_efp_eplant registry (tested at 99%+ coverage against real
# probeset/gene ID sample data) and embedded into combined_master.json at
# build time by build_combined_master_json.py -- see get_validation_patterns().
# Each pattern covers canonical gene IDs AND (where applicable) microarray
# probeset IDs. Copied (not aliased) so the aliases added below don't mutate
# the shared cached master JSON other modules also read.
EFP_PROJECT_REGEXES: dict = dict(load_combined_master()["validation_patterns"])

# Aliases for alternate eFP project key spellings used by the BAR (not present
# in Vincent's registry, which is keyed by canonical eFP project name only).
EFP_PROJECT_REGEXES["efpbarley"] = EFP_PROJECT_REGEXES["efp_barley"]
EFP_PROJECT_REGEXES["efprice"] = EFP_PROJECT_REGEXES["efp_rice"]
EFP_PROJECT_REGEXES["efpmedicago"] = EFP_PROJECT_REGEXES["efp_medicago"]
EFP_PROJECT_REGEXES["efppop"] = EFP_PROJECT_REGEXES["efp_poplar"]
EFP_PROJECT_REGEXES["efpsoybean"] = EFP_PROJECT_REGEXES["efp_soybean"]
EFP_PROJECT_REGEXES["maizeefp"] = EFP_PROJECT_REGEXES["efp_maize"]

# General injection guard, run before any per-project/probeset format check.
# A handful of eFP projects accept loose freeform text (metabolite/enzyme/trait
# names, e.g. "TG 54:5; 16:0_20:1_18:4" or "efpconfig"'s near-unrestricted
# `.{0,16}`), so this can't blacklist individual characters like ';' or "'" --
# those are legitimate in real sample data. Instead it looks for actual attack
# syntax: SQL comment/statement-chaining sequences, tautologies, UNION SELECT,
# script tags, and null bytes.
_INJECTION_RE = re.compile(
    r"(--)"
    r"|(/\*)|(\*/)"
    r"|(;\s*(drop|delete|update|insert|alter|exec|union|select)\b)"
    r"|(\bunion\b\s+\bselect\b)"
    r"|(\bor\b\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+)"
    r"|(<\s*script\b)"
    r"|(javascript\s*:)"
    r"|(\bxp_cmdshell\b)"
    r"|(\x00)",
    re.IGNORECASE,
)


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
        """Validates barley gene IDs: HORVU0Hr1G000320, HORVU.MOREX.r3.1HG0000030 (bare gene,
        BAR's own live example), HORVU.MOREX.r3.1HG0003350.1 (with isoform suffix),
        or HORVU.MOREX.r3.UnG0797170.1 (Un = unplaced scaffold, no chromosome digit)"""
        return bool(
            gene and re.search(r"^HORVU(\d+Hr\d+G\d+|\.MOREX\.r\d+\.(\dH|Un)G\d+(\.\d+)?)$", gene, re.I)
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
        """Validates Camelina gene IDs: Csa01g001040 (bare gene, BAR's own live example),
        Csa01g012560.1, Csa00462s060.1 (with isoform suffix)"""
        return bool(gene and re.search(r"^Csa\d+[gs]\d+(\.\d+)?$", gene, re.I))

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
        if gene and re.search(r"^(Glyma\d{1,3}g\d{1,6}\.?\d?)$|^(Glyma\.\d{1,3}g\d{1,8})$", gene, re.I):
            return True
        else:
            return False

    @staticmethod
    def is_maize_gene_valid(gene):
        """This function verifies if maize gene is valid: Zm00001d046170
        :param gene:
        :return: True if valid
        """
        if gene and re.search(
            r"^(AC[0-9]{6}\.[0-9]{1}_FG[0-9]{3})$|^(AC[0-9]{6}\.[0-9]{1}_FGT[0-9]{3})$|^(GRMZM(2|5)G[0-9]{6})$|^(GRMZM(2|5)G[0-9]{6}_T[0-9]{2})$|^(Zm\d+d\d+)$|^(Zm\d{1,8}\D{1,3}\d{1,8})$",
            gene,
            re.I,
        ):
            return True
        else:
            return False

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
    def is_injection_attempt(data: str) -> bool:
        """Flag obvious SQL/script injection payloads.

        Meant to run before any format-specific check (probeset-shape check,
        per-project regex, species validator) since some of those are
        deliberately permissive -- e.g. efpconfig's near-unrestricted
        `.{0,16}` or the metabolite/lipid projects' freeform text patterns --
        and would otherwise let attack syntax through unexamined.

        :param data: Raw input string to inspect
        :return: True if the input looks like an injection attempt
        """
        return bool(_INJECTION_RE.search(data))

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
        if BARUtils.is_injection_attempt(gene):
            return False
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
