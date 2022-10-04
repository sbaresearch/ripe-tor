#! /bin/zsh

# TODO: Fix key or load from file / env?
RIPE_KEY="<ADD KEY>?"
PROJECT=/mnt/scans/2022_08_tor_ripe/ripe-tor
BASE_PATH=${PROJECT}/run_markus/
PYTHON=${PROJECT}/venv/bin/python3

cd $PROJECT
export RIPE_KEY

# IPv4
$PYTHON ripetor.py -b ${BASE_PATH}        # single
sleep 120
$PYTHON ripetor.py -b ${BASE_PATH} -m     # multi germany
sleep 120
$PYTHON ripetor.py -b ${BASE_PATH} -m -u  # multi usa
sleep 120

# IPv6
$PYTHON ripetor.py -b ${BASE_PATH} -6
sleep 120
$PYTHON ripetor.py -b ${BASE_PATH} -6 -m
sleep 120
$PYTHON ripetor.py -b ${BASE_PATH} -6 -m -u