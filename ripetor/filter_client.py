#! /bin/env python3

import argparse
import csv
import pathlib
from util.common import get_console_logger

parser = argparse.ArgumentParser(description='Filter guard files and combine to output file')
parser.add_argument('-i', '--input', required=True, type=str, help='Path to input files')
parser.add_argument('-d', '--destinations', action="store_true", default=False, help='Filter on exit instead of guard')
parser.add_argument('-o', '--output', required=True, type=str, help='Path to output file')
parser.add_argument('-t', '--top', type=int, default=15, help='Load top <t> AS from each file')
args = parser.parse_args()

log = get_console_logger("filter_client")

input_path = args.input
input_path = pathlib.Path(input_path)

output_file = args.output
output_file = pathlib.Path(output_file)

top_asn = args.top
destinations = args.destinations

if not input_path.exists() or input_path.is_file():
    log.error("Input dir does not exist or is file")
    exit(1)

log.info(f"Filtering the top {top_asn} ASN from each file")

asn_list = {}

if destinations:
    log.info(f'Filtering on exit stat files')
    glob_string = "exit_AS*_stats.tsv"
else:
    log.info(f'Filtering on guard stat files')
    glob_string = "guard_AS*_stats.tsv"

for in_file in input_path.glob(glob_string):
    log.info(f'Using file {in_file}')

    with open(in_file) as csv_file:
        header = [h.strip() for h in csv_file.readline().split('\t')]
        reader = csv.DictReader(csv_file, delimiter='\t', fieldnames=header)
        for index, line in enumerate(reader):
            asn = line['AS'].strip()
            if asn in str(in_file):
                log.debug(f"skipping {asn} due to in filename")
                continue

            p_sum = float(line['Sum'].strip())

            if asn not in asn_list:
                asn_list[asn] = []
            asn_list[asn].append(p_sum)

            if index > top_asn:
                break

log.info("Writing output file")
with open(output_file, 'w') as output_file_pointer:
    fieldnames = ['index', 'AS', 'perc']
    writer = csv.DictWriter(output_file_pointer, fieldnames=fieldnames)
    for index, (asn, values) in enumerate(asn_list.items()):
        record = {
            'index': index,
            'AS': asn,
            'perc': 0
        }

        for value in values:
            record['perc'] = value
            writer.writerow(record)

