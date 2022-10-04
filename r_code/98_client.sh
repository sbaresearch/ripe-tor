#! /bin/zsh

RSCRIPT=/usr/bin/Rscript
SCRIPTS=/home/havok/coding/work/room5/2022_ripe-tor-data/r_code

BASE_PATH=~/Documents/ripetor/run_gabriel/real_2022/clients
IMAGE_PATH=/home/havok/Documents/ripetor/images_gabriel/

$RSCRIPT $BASE_PATH/02_client_top.R -b ${BASE_PATH}/ipv4/ -o /home/havok/Documents/ripetor/images_gabriel/client-ipv4/
$RSCRIPT $BASE_PATH/02_client_top.R -b ${BASE_PATH}/ipv6/ -o /home/havok/Documents/ripetor/images_gabriel/client-ipv6/

$RSCRIPT $BASE_PATH/02_client_top.R -r -b ${BASE_PATH}/censored/ -o /home/havok/Documents/ripetor/images_gabriel/client-censored/