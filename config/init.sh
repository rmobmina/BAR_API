#!/bin/sh
# This script initialized the GitHub environment

# To use locally, set DB_USER/DB_PASS/DB_HOST as environment variables.
# Defaults below are for GitHub Actions — do not change the defaults.
DB_USER=${DB_USER:-"root"}
DB_PASS=${DB_PASS:-"root"}
DB_HOST=${DB_HOST:-"localhost"}

# Load the data
echo "Welcome to the BAR API. Running init!"

db_exists() {
    mysql -h $DB_HOST -u $DB_USER -p$DB_PASS -e "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='$1';" 2>/dev/null | grep -q "$1"
}

import_if_missing() {
    DB_NAME=$1
    SQL_FILE=$2
    if db_exists "$DB_NAME"; then
        echo "[skip] $DB_NAME already exists"
    else
        echo "[load] importing $DB_NAME..."
        mysql -h $DB_HOST -u $DB_USER -p$DB_PASS < "$SQL_FILE"
    fi
}

# Import real curated data for databases that have a static dump BEFORE
# bootstrapping the simple eFP schemas below. Several of these databases
# (e.g. shoot_apex, arachis, single_cell) are also entries in
# SIMPLE_EFP_DATABASE_SCHEMAS; if the dynamic bootstrap ran first it would
# create their table empty, db_exists() would then see it as "already
# there", and import_if_missing would skip loading the real data --
# leaving real endpoints permanently empty in any fresh environment (CI,
# a new dev machine) even though it looks fine on a machine that already
# had the data from before the dynamic bootstrap existed.
import_if_missing annotations_lookup    ./config/databases/annotations_lookup.sql
import_if_missing arabidopsis_ecotypes  ./config/databases/arabidopsis_ecotypes.sql
import_if_missing arachis               ./config/databases/arachis.sql
import_if_missing cannabis              ./config/databases/cannabis.sql
import_if_missing canola_nssnp          ./config/databases/canola_nssnp.sql
import_if_missing dna_damage            ./config/databases/dna_damage.sql
import_if_missing embryo                ./config/databases/embryo.sql
import_if_missing eplant2               ./config/databases/eplant2.sql
import_if_missing eplant_poplar         ./config/databases/eplant_poplar.sql
import_if_missing eplant_rice           ./config/databases/eplant_rice.sql
import_if_missing eplant_soybean        ./config/databases/eplant_soybean.sql
import_if_missing eplant_tomato         ./config/databases/eplant_tomato.sql
import_if_missing fastpheno             ./config/databases/fastpheno.sql
import_if_missing germination           ./config/databases/germination.sql
import_if_missing homologs_db           ./config/databases/homologs_db.sql
import_if_missing interactions_vincent_v2 ./config/databases/interactions_vincent_v2.sql
import_if_missing kalanchoe             ./config/databases/kalanchoe.sql
import_if_missing klepikova             ./config/databases/klepikova.sql
import_if_missing llama3                ./config/databases/llama3.sql
import_if_missing phelipanche           ./config/databases/phelipanche.sql
import_if_missing physcomitrella_db     ./config/databases/physcomitrella_db.sql
import_if_missing poplar_nssnp          ./config/databases/poplar_nssnp.sql
import_if_missing rice_interactions     ./config/databases/rice_interactions.sql
import_if_missing selaginella           ./config/databases/selaginella.sql
import_if_missing shoot_apex            ./config/databases/shoot_apex.sql
import_if_missing silique               ./config/databases/silique.sql
import_if_missing single_cell           ./config/databases/single_cell.sql
import_if_missing soybean_nssnp         ./config/databases/soybean_nssnp.sql
import_if_missing strawberry            ./config/databases/strawberry.sql
import_if_missing striga                ./config/databases/striga.sql
import_if_missing tomato_nssnp          ./config/databases/tomato_nssnp.sql
import_if_missing tomato_sequence       ./config/databases/tomato_sequence.sql
import_if_missing triphysaria           ./config/databases/triphysaria.sql
import_if_missing gaia                  ./config/databases/gaia.sql

# SUPeR Viewer pseudobulk + UMAP databases (real per-gene dumps with an extra
# data_signal_std column on the pseudobulk side, and a separate umap_coords /
# umap_expression pair on the UMAP side) -- must load before the dynamic
# bootstrap below for the same reason as the real-data imports above.
import_if_missing arabidopsis_NIE_pseudobulk        ./config/databases/arabidopsis_NIE_pseudobulk_dump.sql
import_if_missing arabidopsis_flower_lee_pseudobulk ./config/databases/arabidopsis_flower_lee_pseudobulk_dump.sql
import_if_missing arabidopsis_root_rs_pseudobulk    ./config/databases/arabidopsis_root_rs_pseudobulk_dump.sql
import_if_missing arabidopsis_seed_martin_pseudobulk ./config/databases/arabidopsis_seed_martin_pseudobulk_dump.sql
import_if_missing arabidopsis_silique_lee_pseudobulk ./config/databases/arabidopsis_silique_lee_pseudobulk_dump.sql
import_if_missing arabidopsis_stem_lee_pseudobulk   ./config/databases/arabidopsis_stem_lee_pseudobulk_dump.sql
import_if_missing rice_OW_pseudobulk                ./config/databases/rice_OW_pseudobulk_dump.sql
import_if_missing arabidopsis_NIE_umap              ./config/databases/arabidopsis_NIE_umap.sql
import_if_missing arabidopsis_flower_lee_umap       ./config/databases/arabidopsis_flower_lee_umap.sql
import_if_missing arabidopsis_root_shahan_umap      ./config/databases/arabidopsis_root_shahan_umap.sql
import_if_missing arabidopsis_seed_martin_umap      ./config/databases/arabidopsis_seed_martin_umap.sql
import_if_missing arabidopsis_silique_lee_umap      ./config/databases/arabidopsis_silique_lee_umap.sql
import_if_missing arabidopsis_stem_lee_umap         ./config/databases/arabidopsis_stem_lee_umap.sql
import_if_missing rice_OW_umap                      ./config/databases/rice_OW_umap.sql

# Build the remaining simple eFP databases dynamically so we do not need a
# static SQL dump for every one of them. Uses checkfirst=True, so any
# database already created by the real-data imports above (same name) is
# left untouched rather than being recreated empty.
echo "Bootstrapping simple eFP databases..."
python3 ./scripts/bootstrap_simple_efp_dbs.py --user "$DB_USER" --password "$DB_PASS"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to bootstrap simple eFP databases"
    exit 1
fi
echo "Successfully bootstrapped simple eFP databases"

echo "Data are now loaded. Preparing API config"
echo "Please manually edit config file!"

echo "Configuration file ready."
echo "----------- WARNING ----------"
echo "Do not forget to delete your password from the configuration files"
echo "if you are pushing to publicly hosted Git repository."
