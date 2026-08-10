import re
from api.utils.bar_utils import BARUtils


class eFPUtils:
    @staticmethod
    def is_efp_view_name(efp_view):
        """This function is used for validated eFP View names for eFP service
        :param efp_view: string view name
        :return: True if valid
        """
        if efp_view and re.search(r"^[a-z1-9_]{1,50}$", efp_view, re.I):
            return True
        else:
            return False

    @staticmethod
    def is_efp_mode(efp_mode):
        """This function checks if the eFP mode is valid
        :param efp_mode: string eFP Mode
        :return: True or False
        """
        # These are case-sensitive
        valid_modes = ["Absolute", "Relative", "Compare"]
        if efp_mode in valid_modes:
            return True
        else:
            return False

    @staticmethod
    def is_efp_input_valid(efp, view, mode, gene_1, gene_2=None):
        """Test if eFP input is valid
        :return: List with boolean and string
        """
        species = [
            "efp_arabidopsis",
            "efp_arachis",
            "efp_cannabis",
            "efp_grape",
            "efp_maize",
            "efp_rice",
            "efp_sorghum",
            "efp_soybean",
        ]

        # Validate values
        if efp not in species:
            return False, "Invalid eFP."

        # Validate view
        if not eFPUtils.is_efp_view_name(view):
            return False, "Invalid eFP View name."

        # Validate mode
        if not eFPUtils.is_efp_mode(mode):
            return False, "Invalid eFP mode."

        # efp is already constrained to one of the species list above, so it doubles as the gene-id project key
        if not BARUtils.is_efp_gene_valid(gene_1, efp):
            return False, "Gene 1 is invalid."

        if mode == "Compare" and not BARUtils.is_efp_gene_valid(gene_2, efp):
            return False, "Gene 2 is invalid."

        # In compare mode gene1 != gene2
        if mode == "Compare" and gene_1 == gene_2:
            return False, "In compare mode, both genes should be different."

        # Assuming all check have passed
        return True, None
