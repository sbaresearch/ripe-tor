#! /bin/zsh

RSCRIPT=/usr/bin/Rscript
SCRIPTS=/home/havok/coding/work/room5/2022_ripe-tor-data/r_code

BASE_PATH=/home/havok/Documents/ripetor/run_gabriel/real_2022/destinations
IMAGE_PATH=/home/havok/Documents/ripetor/images_gabriel/destinations/

# DE Files
echo
echo
echo "[*] Creating DE Files"
$RSCRIPT ${SCRIPTS}/02_destination_top.R -b ${BASE_PATH}/destination_de_ipv4.dat -o ${IMAGE_PATH} -f destinations_2022_de_v4_median.pdf -z
$RSCRIPT ${SCRIPTS}/02_destination_top.R -b ${BASE_PATH}/destination_de_ipv6.dat -o ${IMAGE_PATH} -f destinations_2022_de_v6_median.pdf -z

# US Files
echo
echo
echo "[*] Creating US Files"
$RSCRIPT ${SCRIPTS}/02_destination_top.R -b ${BASE_PATH}/destination_us_ipv4.dat -o ${IMAGE_PATH} -f destinations_2022_us_v4_median.pdf -z
$RSCRIPT ${SCRIPTS}/02_destination_top.R -b ${BASE_PATH}/destination_us_ipv6.dat -o ${IMAGE_PATH} -f destinations_2022_us_v6_median.pdf -z

# RU Files
echo
echo
echo "[*] Creating RU Files"
$RSCRIPT ${SCRIPTS}/02_destination_top.R -b ${BASE_PATH}/destination_ru_ipv4.dat -o ${IMAGE_PATH} -f destinations_2022_ru_v4_median.pdf -z
$RSCRIPT ${SCRIPTS}/02_destination_top.R -b ${BASE_PATH}/destination_ru_ipv6.dat -o ${IMAGE_PATH} -f destinations_2022_ru_v6_median.pdf -z

$RSCRIPT ${SCRIPTS}/02_destination_top.R -b ${BASE_PATH}/destination_ru_censored_v4.dat -o ${IMAGE_PATH} -f destinations_2022_ru_censored_v4.pdf
$RSCRIPT ${SCRIPTS}/02_destination_top.R -b ${BASE_PATH}/destination_ru_censored_v4.dat -o ${IMAGE_PATH} -f destinations_2022_ru_censored_v4_median.pdf -z