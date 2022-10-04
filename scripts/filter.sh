#! /bin/zsh
BASE_PATH=~/Documents/ripetor/run_gabriel
WILLI_PATH=~/Documents/ripetor/run_willi

IPV4_DE_2020=(${WILLI_PATH}/combined-top-de/stat/)
IPV4_US_2020=(${WILLI_PATH}/combined-top-us/stat/)
IPV4_DE_INPUT=(${BASE_PATH}/*multi_germany_ipv4/stat/)
IPV4_US_INPUT=(${BASE_PATH}/*multi_usa_ipv4/stat/)
IPV6_DE_INPUT=(${BASE_PATH}/*multi_germany_ipv6/stat/)
IPV6_US_INPUT=(${BASE_PATH}/*multi_usa_ipv6/stat/)
IPV4_RU_INPUT=(${BASE_PATH}/20220919-143112_multi_russia_ipv4/stat/)
IPV6_RU_INPUT=(${BASE_PATH}/20220919-205747_multi_russia_ipv6/stat/)
IPV4_RU_CENSORED=(${BASE_PATH}/20220919-214151_multi_russia-censored_ipv4/stat/)

CLIENT_FILTER=/home/havok/Documents/ripetor/run_gabriel/client-filter.dat
DESTINATION_FILTER=/home/havok/Documents/ripetor/run_gabriel/destination-filter.dat

DESTINATION_OUTPUT=${BASE_PATH}/real_2022/destinations
CLIENT_OUTPUT=${BASE_PATH}/real_2022/clients
IMAGE_OUTPUT=~/ripetor/images_gabriel/
mkdir -p ${DESTINATION_OUTPUT} ${CLIENT_OUTPUT}/ipv4 ${CLIENT_OUTPUT}/ipv6 ${CLIENT_OUTPUT}/censored ${CLIENT_OUTPUT}/2020_ipv4

PYTHON=~/.virtualenvs/2022_ripe-tor-data-t0_rpTGD/bin/python3
FILTER=~/coding/work/room5/2022_ripe-tor-data/scripts/filter_export_data.py

function generate_data {
  PROJ_PATH=$1
  COUNTRY_CODE=$2
  PROTO=$3

  echo "Working with ${PROJ_PATH}"

  $PYTHON $FILTER -di $PROJ_PATH -x 0.2 -t 1000 -r ${DESTINATION_FILTER} -o ${DESTINATION_OUTPUT}/destination_${COUNTRY_CODE}_${PROTO}.dat
  $PYTHON $FILTER -i $PROJ_PATH -x 0.05 -r ${CLIENT_FILTER} -o ${CLIENT_OUTPUT}/${PROTO}/client-top-${COUNTRY_CODE}.dat
}

generate_data $IPV4_DE_INPUT "de" "ipv4"
generate_data $IPV6_DE_INPUT "de" "ipv6"
generate_data $IPV4_US_INPUT "us" "ipv4"
generate_data $IPV6_US_INPUT "us" "ipv6"
generate_data $IPV4_RU_INPUT "ru" "ipv4"
generate_data $IPV6_RU_INPUT "ru" "ipv6"

generate_data $IPV4_DE_2020 "de" "2020_ipv4"
generate_data $IPV4_US_2020 "us" "2020_ipv4"

$PYTHON $FILTER -di $IPV4_RU_CENSORED -x 0.2 -t 1000 -r ${DESTINATION_FILTER} -o ${DESTINATION_OUTPUT}/destination_ru_censored_v4.dat
$PYTHON $FILTER -i $IPV4_RU_CENSORED -x 0.05 -r ${CLIENT_FILTER} -o ${CLIENT_OUTPUT}/censored/client-top-ru-censored.dat