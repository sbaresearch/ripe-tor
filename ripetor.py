import argparse
import json
import logging
import pathlib
import time
import os

from datetime import datetime

from ripetor import data, statistics, measurements, atlas
from ripetor.util.common import set_global_file_logger


def download(base_path):
    # Download fresh data
    data_path = base_path + "/data/"
    os.makedirs(data_path)

    # summary = ripetor_data.load_summary(data_path + "summary.json")
    details = data.load_details(data_path + "details.json")
    probes = data.load_probes(data_path + "probes.json")
    data.download_ip2asn_v4(data_path + "ip2asn-v4.tsv")
    data.download_ip2asn_v6(data_path + "ip2asn-v6.tsv")

    logging.info("Finished downloading")

    return details, probes


def print_statistics(details, probes):
    logging.info("Start statistics")
    unfiltered, relays_v4, relays_v6, relays_ds = statistics.get_current_relays(details)
    s = statistics.calculate_basic_tor_relay_stats(unfiltered)
    statistics.print_basic_stats(s)

    unfiltered, probes_v4, probes_v6, probes_ds = statistics.get_current_probes(probes)
    s = statistics.calculate_basic_ripe_stats(unfiltered)
    statistics.print_basic_ripe_stats(s)
    logging.info("Stop statistics")


def create_sets_f(details, probes, c_as, d_as, base_path, ip_version="ipv4"):
    logging.info("Start creating sets")

    g_as = measurements.create_guard_set(details, ip_version)
    e_as = measurements.create_exit_set(details, ip_version)
    g_as_r = measurements.create_guard_with_ripe_probes_set(details, probes, ip_version)
    e_as_r = measurements.create_exit_with_ripe_probes_set(details, probes, ip_version)

    sets = {"g_as": g_as, "e_as": e_as, "g_as_r": g_as_r, "e_as_r": e_as_r, "c_as": c_as, "d_as": d_as}

    set_path = base_path + "/measurement-sets/"
    os.makedirs(set_path)

    # Write all 4 sets to disk
    for k, v in sets.items():
        with open(set_path + "%s.json" % k, "w") as f:
            json.dump(v, f, indent=2)

    logging.info("Stop creating sets")

    return sets


def create_measurement_definitions(measurement_sets, now_string, base_path, ip_version="ipv4"):
    logging.info("Start creating RIPE measurements")

    definitions_path = base_path + "/measurement-definitions/"
    os.makedirs(definitions_path)

    logging.info("Total theoretical cost c1: %d c2: %d c3: %d c4: %d total: %d" %
                 measurements.calculate_costs_for_measurement_set(measurement_sets))

    measurement_definitions = dict()
    if measurement_sets["c_as"]:
        measurement_definitions["case1"] = measurements.create_case1(now_string,
                                                                     measurement_sets["c_as"],
                                                                     measurement_sets["g_as"],
                                                                     ip_version)

        measurement_definitions["case4"] = measurements.create_case4(now_string,
                                                                     measurement_sets["g_as_r"],
                                                                     measurement_sets["c_as"],
                                                                     ip_version)

    if measurement_sets["d_as"]:
        measurement_definitions["case2"] = measurements.create_case2(now_string,
                                                                     measurement_sets["e_as_r"],
                                                                     measurement_sets["d_as"],
                                                                     ip_version)

        measurement_definitions["case3"] = measurements.create_case3(now_string,
                                                                     measurement_sets["d_as"],
                                                                     measurement_sets["e_as"],
                                                                     ip_version)

    for case_description, definition_list in measurement_definitions.items():
        for idx, single_measurement in enumerate(definition_list):
            logging.debug("Created measurement definition for %s part %d" % (case_description, idx))
            with open(definitions_path + "%s_%d.json" % (case_description, idx), "w") as f:
                json.dump(single_measurement, f, indent=2)

    logging.info("Stop creating RIPE measurements")
    return measurement_definitions


def start_executing_measurements(measurement_definitions, base_path):
    logging.info("Start executing RIPE measurements")

    response_path = base_path + "/measurement-responses/"
    os.makedirs(response_path)

    result_path = base_path + "/measurement-results/"
    os.makedirs(result_path, exist_ok=True)

    # MM: this response dict stores all measurement IDs with the corresponding progress
    # if in caseX, the measurement is still ongoing, if in downloaded or finished, the measurement is done
    measurement_responses = {"downloaded": [], "finished": [], "case1": [], "case2": [], "case3": [], "case4": []}

    # MM: iterate over all cases and definitions
    for case_description, definition_list in measurement_definitions.items():
        for idx, single_measurement in enumerate(definition_list):
            # Determine how many new measurements we would be starting with this definition
            number_measurements = measurements.calculate_number_of_measurements(single_measurement)

            # MM: if the currently running plus the new measurements would be above 100
            # wait for 40 seconds and attempt to download all running measurements.
            # Further, if the measurements did not stop after 40 seconds, we stop them
            atlas.wait_and_download(
                result_path,
                measurement_responses,
                nr_measurement=number_measurements
            )

            # MM: Start the new measurement(s), at this point, no measurements should be running!
            response = atlas.start_definition(single_measurement)
            time.sleep(15)

            # MM: Dump the gotten response for the started measurements and add the measurement IDs to our case set
            logging.debug("Response for %s part %d: %s" % (case_description, idx, response))
            with open(response_path + "%s_%d_response.json" % (case_description, idx), "w") as f:
                json.dump(response, f, indent=2)
            measurement_responses[case_description].extend(response["measurements"])

    logging.info("Stop executing RIPE measurements")
    return measurement_responses


def get_running_measurement(measurement_responses: dict):
    running = []
    for case, measurement_ids in measurement_responses.items():
        if case in ['downloaded', 'finished']:
            continue
        running.extend(measurement_ids)
    return running


def download_results(measurement_responses, base_path):
    logging.info("Start downloading results")

    result_path = base_path + "/measurement-results/"
    os.makedirs(result_path, exist_ok=True)

    done = get_running_measurement(measurement_responses) == 0
    running_counter = 0
    while not done:
        # Retry the download of everything
        atlas.download_everything(result_path, measurement_responses)

        running = get_running_measurement(measurement_responses)
        if len(running) == 0:
            done = True
            logging.info(f'All cases finished downloading')
        elif running_counter == 10:
            done = True
            logging.warning(f'Stopped prematurely after 10 minutes of retrying')
            logging.warning(f'Still running {len(running)} cases: {" ".join(running)}')
        else:
            running_counter += 1
            logging.info(f'Retrying download cycle after 60 seconds')
            time.sleep(60)

    logging.info("Finished downloading")


def build_probe_set_for_asn(probes, asn_list, ip_version):
    probe_set = {"probes": [], "addresses": [], "asn": []}
    for asn in asn_list:
        probe_candidates = statistics.get_example_set_by_asn(probes, asn, ip_version)
        if probe_candidates.get('probes'):
            # just take first probe candidate
            probe_set["probes"].append(probe_candidates.get('probes')[0])
            probe_set["addresses"].append(probe_candidates.get('addresses')[0])
            probe_set["asn"].append(asn)
        else:
            print(f"no matches for {asn}")
    return probe_set


def parse_args():
    parser = argparse.ArgumentParser(description='ripetor measurment script')
    parser.add_argument(
        '-b', '--basedir', type=str, default='run/',
        help='Directory to store results in'
    )
    parser.add_argument(
        '-6', '--ipv6', action='store_true', default=False,
        help='Set IP Version mode to IPv6 (default = IPv4)'
    )
    parser.add_argument(
        '-m', '--multi', action='store_true', default=False,
        help='Set measurement mode to multi (default = single)'
    )
    parser.add_argument('-c', '--country', default='germany', type=str, choices=['germany', 'usa', 'russia', 'russia-censored'],
        help='Set measurement country if multi measurement (allowed = germany, usa, russia, russia-censored; default = germany)'
    )

    parser.add_argument('-d', '--debug', action='store_true', default=False, help='Enable debug printing')
    args = parser.parse_args()
    basedir = pathlib.Path(args.basedir)

    ip_version = 'ipv4'
    if args.ipv6:
        ip_version = 'ipv6'

    mode = 'single'
    if args.multi:
        mode = 'multi'

    return basedir, mode, ip_version, args.country, args.debug


def main():
    dateformat = "%Y%m%d-%H%M%S"

    basedir, mode, ip_version, country, debug = parse_args()

    # Create standardized result folder
    now_string = datetime.now().strftime(dateformat)

    current_measurement = f'{now_string}_{mode}_{ip_version}'
    if mode == "multi":
        current_measurement = f'{now_string}_{mode}_{country}_{ip_version}'

    base_path = basedir.joinpath(current_measurement)
    base_path.mkdir(parents=True)

    # setup logging
    log_file = base_path.joinpath("run.log")
    set_global_file_logger(log_file, debug=debug)
    if debug:
        logging.debug(f'Enabled debug logging to console')

    logging.info(f'Starting run {current_measurement}')

    if atlas.get_measurements_running()["count"] > 0:
        logging.error("There are measurements running, dont execute")
        exit(1)

    # DOWNLOAD
    # Fix base_path to string for further usage
    base_path = str(base_path)
    details, probes = download(base_path)

    # STATISTICS
    print_statistics(details, probes)

    logging.info(f'Using mode {mode}')
    if mode == "multi":
        logging.info(f'Using country {country}')
    logging.info(f'IP version {ip_version}')

    # ADD MEASUREMENT DATA
    c_as = {}
    if mode == "single":
        # 2020
        c_as = {
            "probes": [26895],
            "addresses": ["185.81.215.146:0"]
        }  # Nextlayer / sba-research.org

        # 2022
        c_as = {
            "probes": [6304],
            "addresses": [["92.60.13.86:0", "[2a01:190:1703:4::2]:0"]]
        }  # Nextlayer anchor

    elif mode == "multi":
        # 2020
        country_top_historical = {
            'germany': {'AS3320', 'AS6830', 'AS31334', 'AS8881', 'AS3209', 'AS6805', 'AS553', 'AS680', 'AS8422',
                       'AS9145'},
            'usa': {'AS7922', 'AS701', 'AS7018', 'AS209', 'AS20115', 'AS22773', 'AS5650', 'AS20001', 'AS10796',
                   'AS11427'}
        }

        # 2022
        country_top_v4 = {
            'germany': {'AS3320', 'AS3209', 'AS8881', 'AS6805', 'AS553', 'AS680', 'AS60294', 'AS24940', 'AS8422',
                        'AS9145'},
            'usa': {'AS7922', 'AS7018', 'AS701', 'AS209', 'AS20115', 'AS22773', 'AS5650', 'AS20001', 'AS47583',
                    'AS20473'},
            'russia': {'AS12389', 'AS8402', 'AS25513', 'AS42610', 'AS35807', 'AS12714', 'AS3216', 'AS8359',
                       'AS12668', 'AS31200'}
        }
        country_top_v6 = {
            'germany': {'AS3320', 'AS3209', 'AS8881', 'AS6805', 'AS8422', 'AS199284', 'AS60294', 'AS24940', 'AS8767',
                        'AS680'},
            'usa': {'AS7922', 'AS7018', 'AS701', 'AS47583', 'AS20473', 'AS62538', 'AS20001', 'AS209', 'AS22773',
                    'AS20115'},
            'russia': {'AS42610', 'AS25513', 'AS202422', 'AS8331', 'AS12668', 'AS20764', 'AS50716', 'AS35807',
                       'AS12714', 'AS15974'}
        }
        client_country = country
        if country == 'russia-censored':
             client_country = 'russia'

        # just add everything - the more results the better... we filter for available probes (ipv4/ipv6) anyway! 
        country_top = set(country_top_v4.get(client_country, set()) | country_top_v6.get(client_country, set()) | country_top_historical.get(client_country, set()))

        c_as = build_probe_set_for_asn(probes, country_top, ip_version)

    else:
        exit("unknown mode")

    d_as = {}
    if mode == "single":
        # SET FOR SINGLE TEST
        # 2020
        d_as = {
            "probes": [50609],
            "addresses": ["88.198.220.88:0"]
        }  # Hetzner / torproject.org

        # 2022
        d_as = {
            "probes": [1004032],
            "addresses": [["138.201.152.183:0", "[2a01:4f8:1c17:6262::1]:0"]]
        }  # Hetzner / torproject.org

    elif mode == "multi":
        # SET described in Paper
        # 2020 (probe for AS7941 is not online anymore :-| )
        tranco_set_historic = {'AS3', 'AS15169', 'AS4837', 'AS24940', 'AS36351', 'AS14618', 'AS16509', 'AS14907', 'AS3356',
                      'AS7941'}
        # 2022 (top 100 domains -> 14 AS with ripe deployed)
        tranco_set_v4 = {'AS15169', 'AS16509', 'AS8075', 'AS4837', 'AS14907', 'AS55990', 'AS37963', 'AS132203',
                      'AS4134', 'AS4812', 'AS47764', 'AS29169', 'AS14618', 'AS396982'}

        # 2022 (top 100 domains -> 4 AS with ripe deployed)
        tranco_set_v6 = {'AS15169', 'AS16509', 'AS14907', 'AS47764'}
        # 2022 (top 250 domains -> 10 AS with ripe deployed)
        tranco_set_v6 = {'AS15169', 'AS16509', 'AS14907', 'AS47764', 'AS63949', 'AS3', 'AS37963', 'AS197695', 'AS32', 'AS14618'}
        # 2022 (taken from top 100 censored domains that are hosted in RU, UA)
        russia_censored_v4 = {'AS200350', 'AS15497', 'AS25532', 'AS207651', 'AS9123', 'AS28907', 'AS3326', 'AS197695', 'AS25521', 'AS12722'}
        # 2022 russia v6 only finds 2 ASNs...
        russia_censored_v6 = {'AS25532', 'AS197695'}

        tranco_all = set(tranco_set_v4 | tranco_set_v6 | tranco_set_historic)
        destination_set = tranco_all
        #if ip_version == "ipv6":
        #    destination_set = tranco_set_v6
        if country == "russia-censored":
            destination_set = russia_censored_v4

        d_as = build_probe_set_for_asn(probes, destination_set, ip_version)
    else:
        logging.error(f'Selected unknown mode "{mode}"')
        exit(1)

    # logging.info("destination set set to %s" % d_as)
    # CREATE SETS
    measurement_sets = create_sets_f(details, probes, c_as, d_as, base_path, ip_version)
    measurement_definitions = create_measurement_definitions(measurement_sets, now_string, base_path, ip_version)
    measurement_responses = start_executing_measurements(measurement_definitions, base_path)
    download_results(measurement_responses, base_path)

    logging.info("Run stopped")


if __name__ == '__main__':
    main()
