#! /bin/env python3
# This script is used to load the output data from evaluation.py for guard and exit files
# Further, it is used to truncate the data to the <t> top AS found within the file
# The output files are further used to generate both the client_top and destination_top graphs

import argparse
import csv
import logging
import pathlib
import statistics


def get_default_format():
    return '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


def get_console_logger(name):
    logger = logging.getLogger(name)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)

    # create formatter
    log_format = get_default_format()
    formatter = logging.Formatter(log_format)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    logger.setLevel(logging.INFO)
    return logger


parser = argparse.ArgumentParser(description='Filter guard files and combine to output file')
parser.add_argument('-i', '--input', required=True, type=str, help='Path to input files')
parser.add_argument('-o', '--output', required=True, type=str, help='Path to output file')
parser.add_argument('-d', '--destinations', action="store_true", default=False, help='Filter on exit instead of guard')
parser.add_argument('-t', '--top', type=int, default=15, help='Load top <t> AS from each file')
parser.add_argument('-n', '--number', type=int, default=5, help='Feature at least X data points')
parser.add_argument('-r', '--asn_list', type=str, help='Path to file containing AS to unconditionally use')
parser.add_argument('-x', '--threshold', type=float, default=1.0, help='Threshold for minimum value')
parser.add_argument('-m', '--mean', action='store_true', default=False, help='Use mean instead of max')
args = parser.parse_args()

log = get_console_logger("filter_client")
log.setLevel(logging.DEBUG)

input_path = args.input
input_path = pathlib.Path(input_path)

output_file = args.output
output_file = pathlib.Path(output_file)

fix_asn_list = set()

if args.asn_list is not None and args.asn_list != "":
    asn_path = pathlib.Path(args.asn_list)
    log.info(f'Found asn file')
    with open(asn_path) as asn_file:
        for line in asn_file:
            line = line.strip()
            if 'AS' not in line:
                line = f'AS{line}'

            fix_asn_list.add(line)

    log.info(f'Loaded {len(fix_asn_list)} asn from list')

top_asn = args.top
data_threshold = args.threshold
destinations = args.destinations
number_points = args.number
use_mean = args.mean

ranking = max
if use_mean:
    ranking = statistics.mean

if not input_path.exists() or input_path.is_file():
    log.error("Input dir does not exist or is file")
    exit(1)

log.info(f"Filtering the top {top_asn} ASN from each file")

asn_list = {}

if destinations:
    log.info(f'Filtering on exit stat files')
    glob_string = "exit_*_stats.tsv"
else:
    log.info(f'Filtering on guard stat files')
    glob_string = "guard_*_stats.tsv"

max_asn_value = {}
own_asn_value = {}
filter_target_asn = set()

for in_file in input_path.glob(glob_string):
    log.info(f'Using file {in_file}')

    with open(in_file) as csv_file:

        file_name = in_file.name
        target_as = file_name.split('_')[1]
        filter_target_asn.add(target_as)
        use_max = "AS" in file_name

        header = [h.strip() for h in csv_file.readline().split('\t')]
        reader = csv.DictReader(csv_file, delimiter='\t', fieldnames=header)
        for index, line in enumerate(reader):
            asn = line['AS'].strip()
            if destinations and asn in str(in_file):
                log.debug(f"skipping {asn} due to in filename")
                continue

            p_relay = float(line['Own'].strip())
            p_sum = float(line['Sum'].strip())

            if asn not in asn_list:
                asn_list[asn] = []
                own_asn_value[asn] = p_relay
            asn_list[asn].append(p_sum)

            if use_max:
                if asn not in max_asn_value:
                    max_asn_value[asn] = {'max': 0.0, 'as': ''}
                last_max = max_asn_value[asn]['max']

                if max_asn_value[asn]['max'] < p_sum:
                    max_asn_value[asn]['max'] = p_sum
                    max_asn_value[asn]['as'] = target_as

# at this point we have a dict from ASN -> [percentages]

result_dict = {}
for asn in filter_target_asn:
    if asn in asn_list:
        del asn_list[asn]

# select all asn from the given list to the result dict
for asn in fix_asn_list:
    if asn in asn_list:
        log.info(f'Added {asn} per default')
        result_dict[asn] = asn_list[asn]
        del asn_list[asn]

# do some kind of ranking for the
# max ranking
res = {key: val for key, val in sorted(asn_list.items(), key=lambda ele: ranking(ele[1]), reverse=True) if len(val) >= number_points}
for index, asn in enumerate(res.keys()):
    if index >= top_asn:
        break

    data = asn_list[asn]
    max_value = ranking(data)

    if max_value < data_threshold:
        continue

    result_dict[asn] = data

log.info("Writing output file")
with open(output_file, 'w') as output_file_pointer:
    fieldnames = ['index', 'AS', 'perc', 'max_target', 'p_relay']
    writer = csv.DictWriter(output_file_pointer, fieldnames=fieldnames)
    for index, (asn, values) in enumerate(result_dict.items()):
        max_target = max_asn_value.get(asn, "")
        record = {
            'index': index,
            'AS': asn,
            'perc': 0,
            'max_target': max_target['as'],
            'p_relay': own_asn_value[asn]
        }

        for value in values:
            record['perc'] = value
            writer.writerow(record)
