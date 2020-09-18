import os
import requests
import json
import bz2
import gzip
import logging

DETAILS_ULR = "https://onionoo.torproject.org/details"
PROBES_URL = "https://ftp.ripe.net/ripe/atlas/probes/archive/meta-latest"
IP2ASN_URL = "https://iptoasn.com/data/ip2asn-v4.tsv.gz"


def download_details(details_filename):
    logging.info("Downloading details from %s" % DETAILS_ULR)
    if not os.path.isfile(details_filename):
        r = requests.get(DETAILS_ULR)
        with open(details_filename, 'wb') as f:
            f.write(r.content)


def download_probes(probes_filename):
    logging.info("Downloading probes from %s" % PROBES_URL)
    if not os.path.isfile(probes_filename):
        r = requests.get(PROBES_URL)
        with open(probes_filename, 'wb') as f:
            unzip = bz2.decompress(r.content)
            f.write(unzip)


def download_ip2asn(ip2asn_filename):
    logging.info("Downloading ip2asn from %s" % IP2ASN_URL)
    if not os.path.isfile(ip2asn_filename):
        r = requests.get(IP2ASN_URL)
        with open(ip2asn_filename, 'wb') as f:
            unzip = gzip.decompress(r.content)
            f.write(unzip)


def load_details(filename):
    if not os.path.isfile(filename):
        download_details(filename)
    with open(filename, 'r') as f:
        return json.load(f)


def load_probes(filename):
    if not os.path.isfile(filename):
        download_probes(filename)
    with open(filename, 'r') as f:
        return json.load(f)
